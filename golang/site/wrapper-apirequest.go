package openradar

import (
	"appengine"
	"appengine/user"
	"encoding/json"
	"fmt"
	"github.com/gorilla/mux"
	"net/http"
)

type APIRequest struct {
	id string
	w  http.ResponseWriter
	r  *http.Request
	c  appengine.Context
	u  *user.User
	v  map[string]string
	m  map[string]interface{}
}

func (p *APIRequest) Set(key string, value interface{}) {
	p.m[key] = value
}

func (p *APIRequest) Infof(format string, args ...interface{}) {
	message := fmt.Sprintf(format, args...)
	p.c.Infof("%s %s", p.id, message)
}

func (p *APIRequest) Errorf(format string, args ...interface{}) {
	message := fmt.Sprintf(format, args...)
	p.c.Errorf("%s %s", p.id, message)
}

func (p *APIRequest) render_json() (err error) {
	p.Infof("Rendering with %+v", p.m)
	encoder := json.NewEncoder(p.w)
	return encoder.Encode(p.m)
}

func (p *APIRequest) render_error(message string) {
	p.Errorf(message)
	p.m = make(map[string]interface{})
	p.Set("status", "error")
	p.Set("message", message)
	err := p.render_json()
	if err != nil {
		http.Error(p.w, err.Error(), 500)
	}
}

func api(handler func(*APIRequest) error) http.HandlerFunc {
	// wrap the APIRequest handler in a function to install in the http server
	return func(w http.ResponseWriter, r *http.Request) {
		request := APIRequest{
			id: requestID(),
			w:  w,
			r:  r,
			c:  appengine.NewContext(r),
			v:  mux.Vars(r),
			m:  make(map[string]interface{}),
		}
		request.Infof("%s", request.r.URL.Path)
		request.u = user.Current(request.c)
		err := handler(&request)
		if err != nil {
			request.render_error(fmt.Sprintf("Error in API request handler: %s", err.Error()))
		} else {
			request.Set("status", "OK")
			err = request.render_json()
			if err != nil {
				request.render_error(fmt.Sprintf("Rendering error: %s", err.Error()))
			}
		}
		return
	}
}
