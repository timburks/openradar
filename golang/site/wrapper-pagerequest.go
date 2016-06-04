package openradar

import (
	"appengine"
	"appengine/user"
	"fmt"
	"github.com/gorilla/mux"
	"net/http"
	"os"
	"strconv"
	"html/template"
)

type PageRequest struct {
	id       string
	w        http.ResponseWriter
	r        *http.Request
	c        appengine.Context
	u        *user.User
	v        map[string]string
	m        map[string]interface{}
	t        *template.Template
	loginURL string
	render   bool
}

func (p *PageRequest) render_template() (err error) {
	p.Infof("%s Rendering with %+v", p.m)
	return p.t.ExecuteTemplate(p.w, "page", p.m)
}

func (p *PageRequest) Set(key string, value interface{}) {
	p.m[key] = value
}

func (p *PageRequest) Template(path string) (err error) {
	_, err = p.t.ParseFiles(path)
	if err != nil {
		p.Errorf("template error %+v", err)
	}
	return err
}

func (p *PageRequest) Redirect(path string) {
	http.Redirect(p.w, p.r, path, http.StatusSeeOther)
	p.render = false
}

func (p *PageRequest) Infof(format string, args ...interface{}) {
	message := fmt.Sprintf(format, args...)
	p.c.Infof("%s %s", p.id, message)
}

func (p *PageRequest) Errorf(format string, args ...interface{}) {
	message := fmt.Sprintf(format, args...)
	p.c.Errorf("%s %s", p.id, message)
}

func (p *PageRequest) pwd() {
	p.Infof("Served from %s", os.Getenv("PWD"))
}

var requestCount int

func requestID() string {
	requestCount = requestCount + 1
	return "REQUEST-" + strconv.Itoa(requestCount)
}

func auth(required bool, handler func(*PageRequest) error) http.HandlerFunc {
	// wrap the PageRequest handler in a function to install in the http server
	return func(w http.ResponseWriter, r *http.Request) {
		p := PageRequest{
			id:     requestID(),
			w:      w,
			r:      r,
			c:      appengine.NewContext(r),
			v:      mux.Vars(r),
			m:      make(map[string]interface{}),
			t:      template.New(""),
			render: true,
		}
		// log the request and the working directory
		p.Infof("%s", p.r.URL.Path)
		p.pwd()

		var err error

		// identify the authenticated services of the current user
		p.u = user.Current(p.c)
		p.loginURL, err = user.LoginURL(p.c, r.URL.String())

		if required {
			// direct unauthorized users to login
			if (p.u == nil) && (p.r.URL.Path != "/signin") {
				p.Infof("Redirecting unauthorized user to /")
				http.Redirect(p.w, p.r, "/signin", http.StatusSeeOther)
				return
			}
		}
		// redirect authorized users from "/signin" to "/"
		if (p.u != nil) && (p.r.URL.Path == "/signin") {
			p.Infof("Redirecting authorized user to /")
			http.Redirect(p.w, p.r, "/", http.StatusSeeOther)
			return
		}

		// set some default parameters for the PageRequest
		p.Set("Hostname", appengine.DefaultVersionHostname(p.c))
		p.Set("User", p.u)
		p.Set("LoginURL", p.loginURL)

		// make some functions available to all PageRequests
		funcMap := template.FuncMap{
			"truncate":              templateHelper_truncate,
			"displayDate":           templateHelper_displayDate,
			"markdown":              templateHelper_markdown,
			"DateFormat":            DateFormat,
			"ShortDateFormat":       ShortDateFormat,
			"ScreenNameForUserName": ScreenNameForUserName,
		}
		p.t.Funcs(funcMap)

		// read default layout
		p.t.ParseFiles("templates/page.html", "templates/topbar.html")

		// call the page handler
		p.Infof("Calling request handler")
		err = handler(&p)

		// handle the response
		if err != nil {
			p.Errorf("Error in request handler: %s", err.Error())
			// reuse the template system to display an error page
			p.t = template.New("")
			p.Template("templates/error.html")
			p.Set("Error", err.Error())
			err = p.render_template()
			if err != nil {
				p.Errorf("Error in error handler: %s", err.Error())
				http.Error(p.w, err.Error(), 500)
			}
		} else if p.render {
			p.Infof("Rendering HTML response")
			p.w.Header().Set("Cache-Control", "private, no-cache, no-store, must-revalidate, max-age=0, ") // HTTP 1.1.
			p.w.Header().Set("Pragma", "no-cache")                                                         // HTTP 1.0.
			p.w.Header().Set("Expires", "0")                                                               // Proxies
			err = p.render_template()
			if err != nil {
				p.Errorf("Rendering error: %s", err.Error())
				http.Error(p.w, err.Error(), 500)
			}
		}
		return
	}
}
