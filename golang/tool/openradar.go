package main

import (
	"appengine"
	"appengine/datastore"
	"appengine/remote_api"
	_ "bytes"
	_ "crypto/sha1"
	"encoding/gob"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/docopt/docopt-go"
	"gopkg.in/yaml.v2"
	"io/ioutil"
	"log"
	_ "mime"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"os"
	_ "os/exec"
	"os/user"
	_ "path"
	_ "path/filepath"
	_ "regexp"
	"sort"
	"strconv"
	"strings"
	"time"
)

// use this for calling Python OpenRadar APIs
const APIKey_v1 = "30ce19bd-4946-11e5-9dc5-b125ceaa8fd4"

////////////////////////////////////////////////////////////////////////////
// These structures hold raw values read from the Python OpenRadar JSON API
////////////////////////////////////////////////////////////////////////////

type RawRadar struct {
	Identifier     int64  `json:"id"`
	Title          string `json:"title"`
	Number         string `json:"number"`
	UserName       string `json:"user"`
	Status         string `json:"status"`
	Description    string `json:"description"`
	Resolved       string `json:"resolved"`
	Product        string `json:"product"`
	Classification string `json:"classification"`
	Reproducible   string `json:"reproducible"`
	ProductVersion string `json:"product_version"`
	Originated     string `json:"originated"`
	Created        string `json:"created"`
	Modified       string `json:"modified"`
}

type RawRadarsResult struct {
	Radars []RawRadar `json:"result"`
	Cursor string     `json:"cursor"`
}

type RawComment struct {
	Identifier  int64  `json:"id"`
	UserName    string `json:"user"`
	Subject     string `json:"subject"`
	Body        string `json:"body"`
	RadarNumber string `json:"radar"`
	IsReplyTo   int64  `json:"is_reply_to"`
	PostedAt    string `json:"posted_at"`
}

type RawCommentsResult struct {
	Comments []RawComment `json:"result"`
	Cursor   string       `json:"cursor"`
}

////////////////////////////////////////////////////////////////////////////
// These structures correspond to the datastore for the Go OpenRadar
////////////////////////////////////////////////////////////////////////////

type Radar struct {
	Number         int64     `json:"number"`
	UserName       string    `json:"user"`
	Title          string    `json:"title"`
	Status         string    `json:"status"`
	Duplicating    int64     `json:"duplicating"`
	Description    string    `json:"description" datastore:",noindex"`
	Product        string    `json:"product"`
	Classification string    `json:"classification"`
	Reproducible   string    `json:"reproducible"`
	ProductVersion string    `json:"product_version"`
	Originated     time.Time `json:"originated"`
	Resolved       time.Time `json:"resolved"`
	Created        time.Time `json:"created"`
	Modified       time.Time `json:"modified"`
	Published      bool      `json:"published"`
}

type Comment struct {
	UserName    string `json:"user"`
	Subject     string `json:"subject"`
	Body        string `json:"body" datastore:",noindex"`
	RadarNumber int64  `json:"radar"`
	IsReplyTo   int64  `json:"is_reply_to"`
	Created     time.Time
	Modified    time.Time
	// temporary properties
	Number int64 `datastore:"-"`
}

////////////////////////////////////////////////////////////////////////////
// These structures are used for indexing in the Search API
////////////////////////////////////////////////////////////////////////////

type RadarSearchTerms struct {
	Number      string
	Title       string
	Description string
}

type CommentSearchText struct {
	Subject string
	Body    string
}

////////////////////////////////////////////////////////////////////////////
// This is for reading app.yaml
////////////////////////////////////////////////////////////////////////////

type App struct {
	Application string          `yaml:"application"`
	Version     string          `yaml:"version"`
	Runtime     string          `yaml:"runtime"`
	APIVersion  string          `yaml:"api_version"`
	Handlers    []AppURLHandler `yaml:"handlers"`
}

type AppURLHandler struct {
	URL         string `yaml:"url"`
	StaticDir   string `yaml:"static_dir"`
	StaticFiles string `yaml:"static_files"`
	Upload      string `yaml:"upload"`
	Script      string `yaml:"script"`
}

func ReadApp(path string) (app *App, err error) {
	bytes, err := ioutil.ReadFile(path + "/app.yaml")
	if err == nil {
		app = &App{}
		err = yaml.Unmarshal(bytes, app)
		if err == nil {
			return app, nil
		}
	}
	return nil, err
}

/////////////////////////////////////////////////////////////////////////////////////////
// try to clean up the randomly-formatted time values in the Python OpenRadar datastore
/////////////////////////////////////////////////////////////////////////////////////////

func parseTime(s string) (t time.Time, err error) {
	if s == "" {
		return t, errors.New("empty time string")
	}

	timeFormats := []string{
		"2006-01-02 15:04:05.000000",
		"2 Jan 2006",
		"2/Jan/2006",
		"2-Jan-2006",
		"2-January-2006",
		"2-Jan-2006 03:04 PM",
		"1/2/2006",
		"1.2.2006",
		"2.1.6",
		"1-2-2006",
		"2006/1/2",
		"1/2/06",
		"1-2-06",
		"2006-1-2",
		"2006.1.2",
		"2006-Jan-2",
		"2-1-2006",
		"2-Jan-06",
		"January 2, 2006",
		"2 January 2006",
		"Jan 2, 2006",
		"2/1/2006",
		"2.1.2006",
		"2/1/06",
		"1/2/06 03:04 PM",
		"Mon, 2 Jan 2006 15:04:05 GMT",
		"January 2 2006",
		"January 2nd, 2006",
		"Jan 2 2006",
		"2-Jan-2006 03:04PM",
		"2-Jan-2006 03:04",
		"2-Jan-2009 03:04:05GMT",
		"2006-01-02T15:04-0700",
		"Monday, January 2, 2006 3:04:05 PM Europe/Lisbon",
		"2-Jan-2006 03:04 PM",
		"20060102",
	}

	for _, timeFormat := range timeFormats {
		t, err = time.Parse(timeFormat, s)
		if err == nil {
			return t, err
		}
	}
	return t, err
}

/////////////////////////////////////////////////////////////////////////////////////////
// A Session represents a connection to a Go OpenRadar instance
/////////////////////////////////////////////////////////////////////////////////////////

type Session struct {
	Local         bool
	Source        string
	Radars        map[int64]Radar
	Comments      map[int64]Comment
	ServiceHost   string
	ServiceScheme string
	ServiceURL    *url.URL
	AppHost       string
	AppScheme     string
	AppURL        *url.URL
	App           *App
	client        *http.Client
}

type CookieTray struct {
	Cookies []*http.Cookie
	Path    string
}

func NewSession(app *App, local bool) (session *Session, err error) {
	// build the session object
	session = &Session{
		Local: local,
		App:   app,
	}
	if local {
		session.ServiceHost = "localhost:8000"
		session.ServiceScheme = "http"
		session.AppHost = "localhost:8080"
		session.AppScheme = "http"
	} else {
		session.ServiceHost = "appengine.google.com"
		session.ServiceScheme = "https"
		session.AppHost = app.Application + ".appspot.com"
		session.AppScheme = "https"
	}
	session.ServiceURL, err = url.Parse(session.ServiceScheme + "://" + session.ServiceHost)
	if err != nil {
		return nil, err
	}
	session.AppURL, err = url.Parse(session.AppScheme + "://" + session.AppHost)
	if err != nil {
		return nil, err
	}

	// try to read a cookie file, but if we fail, go on without it
	jar, err := cookiejar.New(nil)
	var cookieTrays []CookieTray
	f, readerr := os.Open(session.cookieFileName())
	if readerr == nil {
		dec := gob.NewDecoder(f)
		readerr = dec.Decode(&cookieTrays)
		if readerr == nil {
			for _, cookieTray := range cookieTrays {
				url, err := url.Parse(cookieTray.Path)
				if err == nil {
					jar.SetCookies(url, cookieTray.Cookies)
				}
			}
		}
	}

	// finish by creating the session client
	session.client = &http.Client{
		Jar: jar,
	}
	return session, err
}

func (session *Session) appValues() (values *url.Values) {
	values = &url.Values{}
	values.Set("app_id", session.App.Application)
	values.Set("version", session.App.Version)
	return values
}

func (session *Session) cookieFileName() (name string) {
	u, _ := user.Current()
	return u.HomeDir + "/.cookies"
}

// This signs us in so that we can use the remote_api.
// To do that we need a client object that has cookies that are set by responses to login requests.
func (session *Session) Signin(username, password string) (err error) {
	// create the http client that we'll use to make signin connections
	redirectPolicyFunc := func(req *http.Request, via []*http.Request) (err error) {
		return errors.New("don't follow redirects")
	}
	jar, _ := cookiejar.New(nil)
	client := &http.Client{
		CheckRedirect: redirectPolicyFunc,
		Jar:           jar,
	}

	// if we're connecting to a non-local app, first authenticate with Google
	var values map[string]string
	if !session.Local {
		v := url.Values{}
		v.Set("Email", username)
		v.Set("Passwd", password)
		v.Set("source", "Google-appcfg-1.9.17")
		v.Set("accountType", "HOSTED_OR_GOOGLE")
		v.Set("service", "ah")
		response, err := http.Get("https://www.google.com/accounts/ClientLogin?" + v.Encode())
		if err != nil {
			return err
		}
		defer response.Body.Close()
		contents, err := ioutil.ReadAll(response.Body)
		if err != nil {
			return err
		}
		values = make(map[string]string)
		lines := strings.Split(string(contents), "\n")
		for _, line := range lines {
			keyvalue := strings.Split(line, "=")
			if len(keyvalue) == 2 {
				values[keyvalue[0]] = keyvalue[1]
			}
		}
		fmt.Printf("RECEIVED: %+v\n", values)
		errorMessage, hasError := values["Error"]
		if hasError {
			return errors.New(errorMessage)
		}
	}

	// fetch the service and app login paths to get necessary cookies
	v2 := url.Values{}
	v2.Set("continue", "http://localhost")
	v2.Set("auth", values["Auth"])

	if session.Local {
		v2.Set("admin", "True")
		v2.Set("action", "Login")
		v2.Set("email", username)
	}
	_, err = client.Get(session.ServiceScheme + "://" + session.ServiceHost + "/_ah/login?" + v2.Encode())
	if len(session.App.Application) > 0 {
		_, err = client.Get(session.AppScheme + "://" + session.AppHost + "/_ah/login?" + v2.Encode())
	}

	// save the cookies locally
	cookieTrays := []CookieTray{}
	cookieTrays = append(cookieTrays, CookieTray{Path: session.AppScheme + "://" + session.AppHost, Cookies: jar.Cookies(session.AppURL)})
	cookieTrays = append(cookieTrays, CookieTray{Path: session.ServiceScheme + "://" + session.ServiceHost, Cookies: jar.Cookies(session.ServiceURL)})
	f, err := os.Create(session.cookieFileName())
	defer f.Close()
	enc := gob.NewEncoder(f)
	return enc.Encode(cookieTrays)
}

/////////////////////////////////////////////////
// Download radars from Open Radar
/////////////////////////////////////////////////

func fileNameForRadars(page int) string {
	return "Radars/radars-" + strconv.Itoa(page) + ".json"
}

// download a page of radars from Open Radar
func (session *Session) FetchRadars(page int, cursor string) (radars *RawRadarsResult, err error) {
	v := url.Values{}
	v.Set("page", strconv.Itoa(page))
	request, err := http.NewRequest("GET", "http://4.openradar.appspot.com/api/radars/recent?cursor="+cursor, nil)
	request.Header.Set("Authorization", APIKey_v1)
	response, err := session.client.Do(request)
	if err == nil {
		defer response.Body.Close()
		contents, err := ioutil.ReadAll(response.Body)
		if err == nil {
			err = ioutil.WriteFile(fileNameForRadars(page), contents, 0644)
		}
		if err == nil {
			result := &RawRadarsResult{}
			err = json.Unmarshal(contents, result)
			return result, err
		}
	}
	return nil, err
}

// download radars from Open Radar
func (session *Session) DownloadRadars(sinceDate time.Time) (err error) {
	os.RemoveAll("Radars")
	os.Mkdir("Radars", 0755)
	cursor := ""
	for i := 1; ; i++ {
		radarResult, err := session.FetchRadars(i, cursor)
		if err != nil {
			fmt.Printf("ERROR %+v\n", err)
			break
		} else {
			cursor = radarResult.Cursor
			count := len(radarResult.Radars)
			fmt.Printf("Radars[%d]: %s %d\n", i, radarResult.Cursor, count)
			if count == 0 {
				break
			} else {
				firstDate, _ := parseTime(radarResult.Radars[count-1].Modified)
				if firstDate.Before(sinceDate) {
					break
				}
			}
		}
	}
	return
}

/////////////////////////////////////////////////
// Local radar storage
/////////////////////////////////////////////////
func (session *Session) radarsFileName() string {
	return "radars.gob"
}

func (session *Session) SaveRadars() error {
	f, err := os.Create(session.radarsFileName())
	if err != nil {
		return err
	}
	defer f.Close()
	enc := gob.NewEncoder(f)
	return enc.Encode(session.Radars)
}

func (session *Session) LoadRadars() error {
	f, readerr := os.Open(session.radarsFileName())
	if readerr == nil {
		dec := gob.NewDecoder(f)
		session.Radars = make(map[int64]Radar)
		return dec.Decode(&session.Radars)
	} else {
		return nil
	}
}

func (session *Session) ImportRadars() (err error) {
	session.Radars = make(map[int64]Radar)
	for page := 1; ; page++ {
		fmt.Printf("importing page %d\n", page)
		contents, err := ioutil.ReadFile(fileNameForRadars(page))
		if err == nil {
			var result RawRadarsResult
			err = json.Unmarshal(contents, &result)
			if err != nil {
				fmt.Printf("error %v\n", err)
			}
			fmt.Printf("read %d radars\n", len(result.Radars))
			for _, raw := range result.Radars {
				var radar Radar
				radar.Number, _ = strconv.ParseInt(raw.Number, 10, 64)
				radar.UserName = raw.UserName
				radar.Title = raw.Title
				radar.Status = raw.Status
				radar.Description = raw.Description
				radar.Product = raw.Product
				radar.Classification = raw.Classification
				radar.Reproducible = raw.Reproducible
				radar.ProductVersion = raw.ProductVersion

				radar.Created, err = parseTime(raw.Created)
				radar.Modified, err = parseTime(raw.Modified)
				radar.Resolved, err = parseTime(raw.Resolved)
				radar.Originated, err = parseTime(raw.Originated)

				radar.Published = true
				if err != nil {
					fmt.Printf("%v => using %+v\n", err, radar.Created)
					radar.Originated = radar.Created
				}

				_, exists := session.Radars[radar.Number]
				if exists {
					fmt.Printf("DUPLICATE %d\n", radar.Number)
				} else {
					session.Radars[radar.Number] = radar
				}
			}
		} else {
			break
		}
	}
	return err
}

/////////////////////////////////////////////////
// Download comments from Open Radar
/////////////////////////////////////////////////

func fileNameForComments(page int) string {
	return "Comments/comments-" + strconv.Itoa(page) + ".json"
}

func (session *Session) FetchComments(page int, cursor string) (comments *RawCommentsResult, err error) {
	v := url.Values{}
	v.Set("cursor", cursor)
	v.Set("apikey", "")
	request, err := http.NewRequest("GET", "http://4.openradar.appspot.com/api/comments/recent?"+v.Encode(), nil)
	request.Header.Set("Authorization", APIKey_v1)
	response, err := session.client.Do(request)
	if err == nil {
		defer response.Body.Close()
		contents, err := ioutil.ReadAll(response.Body)
		if err == nil {
			err = ioutil.WriteFile(fileNameForComments(page), contents, 0644)
		}
		if err == nil {
			result := &RawCommentsResult{}
			err = json.Unmarshal(contents, result)
			if err != nil {
				fmt.Printf("error: %v\n", err)
			}
			return result, err
		}
	}
	return nil, err
}

func (session *Session) DownloadComments(sinceDate time.Time) (err error) {
	os.RemoveAll("Comments")
	os.Mkdir("Comments", 0755)
	cursor := ""
	for i := 1; ; i++ {
		commentResult, err := session.FetchComments(i, cursor)
		if err != nil {
			fmt.Printf("ERROR %+v\n", err)
			break
		} else {
			cursor = commentResult.Cursor
			count := len(commentResult.Comments)
			fmt.Printf("Comments[%d]: %s %d\n", i, commentResult.Cursor, count)
			if count == 0 {
				break
			} else {
				firstDate, _ := parseTime(commentResult.Comments[count-1].PostedAt)
				if firstDate.Before(sinceDate) {
					break
				}
			}
		}
	}
	return
}

/////////////////////////////////////////////////
// Local comment storage
/////////////////////////////////////////////////

func (session *Session) commentsFileName() string {
	return "comments.gob"
}

func (session *Session) SaveComments() error {
	f, err := os.Create(session.commentsFileName())
	if err != nil {
		return err
	}
	defer f.Close()
	enc := gob.NewEncoder(f)
	return enc.Encode(session.Comments)
}

func (session *Session) LoadComments() error {
	f, readerr := os.Open(session.commentsFileName())
	if readerr == nil {
		dec := gob.NewDecoder(f)
		session.Comments = make(map[int64]Comment)
		return dec.Decode(&session.Comments)
	} else {
		return nil
	}
}

func (session *Session) ImportComments() (err error) {

	session.Comments = make(map[int64]Comment)

	for page := 1; ; page++ {
		fmt.Printf("importing page %d\n", page)
		contents, err := ioutil.ReadFile(fileNameForComments(page))
		if err == nil {
			var result RawCommentsResult
			err = json.Unmarshal(contents, &result)
			if err != nil {
				fmt.Printf("error %v\n", err)
			}
			fmt.Printf("read %d comments\n", len(result.Comments))

			for _, raw := range result.Comments {
				var comment Comment
				comment.Number = raw.Identifier
				comment.UserName = raw.UserName
				comment.Subject = raw.Subject
				comment.Body = raw.Body
				comment.RadarNumber, _ = strconv.ParseInt(raw.RadarNumber, 10, 64)
				comment.IsReplyTo = raw.IsReplyTo
				comment.Created, err = parseTime(raw.PostedAt)
				comment.Modified, err = parseTime(raw.PostedAt)
				_, exists := session.Comments[comment.Number]
				if exists {
					fmt.Printf("DUPLICATE %d\n", comment.Number)
				} else {
					session.Comments[comment.Number] = comment
				}
			}

		} else {
			break
		}
	}
	return err
}

/////////////////////////////////////////////////
// This allows us to use the remote_api
/////////////////////////////////////////////////
func (session *Session) AppEngineContext() (c appengine.Context, err error) {
	return remote_api.NewRemoteContext(session.AppHost, session.client)
}

/////////////////////////////////////////////////
// Upload entities using the datastore API
/////////////////////////////////////////////////

func (session *Session) UploadRadars() (err error) {
	c, err := session.AppEngineContext()
	if err != nil {
		return err
	}
	keys := []*datastore.Key{}

	radars := make([]Radar, 0)

	fmt.Printf("Radars: %d\n", len(session.Radars))

	total := 0

	for number, radar := range session.Radars {
		radars = append(radars, radar)
		keys = append(keys, datastore.NewKey(c, "Radar", "", number, nil))
		if len(radars) == 100 {
			_, err = datastore.PutMulti(c, keys, radars)
			if err != nil {
				fmt.Printf("ERROR: %+v\n", err)
			} else {
				total = total + len(radars)
				fmt.Printf("Put %d (%d) OK\n", len(radars), total)
			}
			keys = []*datastore.Key{}
			radars = make([]Radar, 0)
		}
	}
	if len(radars) > 0 {
		_, err = datastore.PutMulti(c, keys, radars)
		if err != nil {
			fmt.Printf("ERROR: %+v\n", err)
		} else {
			total = total + len(radars)
			fmt.Printf("Put %d (%d) OK\n", len(radars), total)
		}
	}
	return
}

func (session *Session) UploadComments() (err error) {
	c, err := session.AppEngineContext()
	if err != nil {
		return err
	}
	keys := []*datastore.Key{}

	comments := make([]Comment, 0)

	fmt.Printf("Comments: %d\n", len(session.Comments))

	total := 0

	for number, comment := range session.Comments {
		comments = append(comments, comment)
		keys = append(keys, datastore.NewKey(c, "Comment", "", number, nil))
		if len(comments) == 100 {
			_, err = datastore.PutMulti(c, keys, comments)
			if err != nil {
				fmt.Printf("ERROR: %+v\n", err)
			} else {
				total = total + len(comments)
				fmt.Printf("Put %d (%d) OK\n", len(comments), total)
			}
			keys = []*datastore.Key{}
			comments = make([]Comment, 0)
		}
	}
	if len(comments) > 0 {
		_, err = datastore.PutMulti(c, keys, comments)
		if err != nil {
			fmt.Printf("ERROR: %+v\n", err)
		} else {
			total = total + len(comments)
			fmt.Printf("Put %d (%d) OK\n", len(comments), total)
		}
	}
	return
}

type ByNumber []Radar

func (a ByNumber) Len() int           { return len(a) }
func (a ByNumber) Swap(i, j int)      { a[i], a[j] = a[j], a[i] }
func (a ByNumber) Less(i, j int) bool { return a[i].Number < a[j].Number }

func (session *Session) ExportRadars() (err error) {

	radars := make([]Radar, 0)
	for k, _ := range session.Radars {
		radars = append(radars, session.Radars[k])
	}
	sort.Sort(ByNumber(radars))

	for _, r := range radars {
		fmt.Printf("%d,%v,%s,%s,%s\n", r.Number, r.Originated, r.Status, r.Product, r.Title)
	}

	fmt.Printf("Count: %d\n", len(session.Radars))

	return
}

/////////////////////////////////////////////////
// Get database info using the datastore API
/////////////////////////////////////////////////

const DatastoreKindName = "__Stat_Kind__"

type DatastoreKind struct {
	KindName            string    `datastore:"kind_name"`
	EntityBytes         int       `datastore:"entity_bytes"`
	BuiltinIndexBytes   int       `datastore:"builtin_index_bytes"`
	BuiltinIndexCount   int       `datastore:"builtin_index_count"`
	CompositeIndexBytes int       `datastore:"composite_index_bytes"`
	CompositeIndexCount int       `datastore:"composite_index_count"`
	Timestamp           time.Time `datastore:"timestamp"`
	Count               int       `datastore:"count"`
	Bytes               int       `datastore:"bytes"`
}

func (session *Session) DatastoreInfo() (err error) {
	c, err := session.AppEngineContext()
	if err != nil {
		log.Fatalf("Failed to create context: %v", err)
		return
	}
	log.Printf("App ID %q", appengine.AppID(c))

	q := datastore.NewQuery(DatastoreKindName).Order("kind_name")
	kinds := []*DatastoreKind{}
	if _, err := q.GetAll(c, &kinds); err != nil {
		log.Fatalf("Failed to fetch kind info: %v", err)
	}

	for _, k := range kinds {
		fmt.Printf("\nkind %q\t%d entries\t%d bytes\n", k.KindName, k.Count, k.Bytes)
		if false {
			props := datastore.PropertyList{}
			if _, err := datastore.NewQuery(k.KindName).Limit(1).Run(c).Next(&props); err != nil {
				log.Printf("Unable to fetch sample entity kind %q: %v", k.KindName, err)
				continue
			}
			for _, prop := range props {
				fmt.Printf("\t%s: %v\n", prop.Name, prop.Value)
			}
		}
	}
	return
}

func main() {
	usage := `openradar.
        Usage:
          openradar signin <username> <password>
          openradar info 
		  openradar sync --since=<date>
          openradar download radars --since=<date>
          openradar download comments --since=<date>
          openradar import radars
          openradar import comments
          openradar upload radars  
		  openradar upload comments
		  openradar export radars
          openradar -h | --help
          openradar --version
          
        Options:
          -h --help     Show this screen.
          --version     Show version.
          <username>    Username
          <password>    Password`

	arguments, _ := docopt.Parse(usage, nil, true, "tool", false)

	is := func(command string) bool {
		terms := strings.Split(command, " ")
		hasAll := true
		for _, term := range terms {
			if !arguments[term].(bool) {
				hasAll = false
			}
		}
		return hasAll
	}

	local := false
	app, err := ReadApp(".")
	session, err := NewSession(app, local)
	session.LoadRadars()
	session.LoadComments()
	if err != nil {
		return
	}

	switch {

	case is("signin"):
		err = session.Signin(arguments["<username>"].(string), arguments["<password>"].(string))

	case is("sync"):
		if sinceDate, err := time.Parse("2006-01-02", arguments["--since"].(string)); err != nil {
		} else if err = session.DownloadRadars(sinceDate); err != nil {
		} else if err = session.ImportRadars(); err != nil {
		} else if err = session.SaveRadars(); err != nil {
		} else if err = session.UploadRadars(); err != nil {
		} else if err = session.DownloadComments(sinceDate); err != nil {
		} else if err = session.ImportComments(); err != nil {
		} else if err = session.SaveComments(); err != nil {
		} else if err = session.UploadComments(); err != nil {
		}

	case is("download radars"):
		if sinceDate, err := time.Parse("2006-01-02", arguments["--since"].(string)); err != nil {
		} else if err = session.DownloadRadars(sinceDate); err != nil {
		}

	case is("download comments"):
		if sinceDate, err := time.Parse("2006-01-02", arguments["--since"].(string)); err != nil {
		} else if err = session.DownloadComments(sinceDate); err != nil {
		}

	case is("import radars"):
		if err = session.ImportRadars(); err != nil {
		} else if err = session.SaveRadars(); err != nil {
		}

	case is("import comments"):
		if err = session.ImportComments(); err != nil {
		} else if err = session.SaveComments(); err != nil {
		}

	case is("upload radars"):
		err = session.UploadRadars()

	case is("upload comments"):
		err = session.UploadComments()

	case is("export radars"):
		err = session.ExportRadars()

	case is("info"):
		err = session.DatastoreInfo()
	}

	if err != nil {
		fmt.Printf("ERROR: %+v\n", err)
	} else {
		fmt.Printf("OK\n")
	}
}
