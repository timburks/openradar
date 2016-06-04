package openradar

import (
	"appengine"
	"appengine/datastore"
	_ "appengine/remote_api"
	"appengine/user"
	"fmt"
	"github.com/gorilla/mux"
	"net/http"
	"net/url"
	"strconv"
)

func apiKeyHandler(p *PageRequest) (err error) {
	if p.r.Method == "GET" {
		apikey, err := getOrCreateAPIKeyForUserName(p.c, p.u.Email)
		if err == nil {
			p.Set("Title", "Your OpenRadar API Key")
			p.Set("APIKey", apikey.APIKey)
			err = p.Template("templates/apikey.html")
		}
	} else if p.r.Method == "POST" {
		err := deleteAPIKeyForUserName(p.c, p.u.Email)
		if err == nil {
			p.Redirect("/apikey")
		}
	}
	return
}

func pageHandler(p *PageRequest) (err error) {
	data := url.Values{}

	query := datastore.NewQuery("Radar")

	product := p.r.FormValue("Product")
	if product != "" {
		query = query.Filter("Product = ", product)
		data.Set("Product", product)
	}

	status := p.r.FormValue("Status")
	if status != "" {
		query = query.Filter("Status = ", status)
		data.Set("Status", status)
	}

	query = query.Order("-Number")

	if query, err = applyCursor(query, p.r.FormValue("c")); err != nil {
		return err
	}

	radars, cursor, err := getRadarsFromQuery(p.c, query, 25)
	if err == nil {
		data.Set("c", cursor)

		p.Template("templates/panel.html")
		p.Template("templates/list.html")
		p.Set("Title", "Open Radar")
		p.Set("Radars", radars)
		if cursor != "" {
			p.Set("MoreLink", "/radars?"+data.Encode())
		}
	}
	return
}

func radarHandler(p *PageRequest) (err error) {
	vars := mux.Vars(p.r)
	radarNumber, err := strconv.ParseInt(vars["radar"], 10, 64)
	if err != nil {
		fmt.Fprintf(p.w, "Invalid Radar Number")
		return
	}

	radar, err := getRadar(p.c, radarNumber)
	if err == nil {
		username := ""
		if p.u != nil {
			username = p.u.Email
		}
		err = getCommentsForRadar(p.c, username, radar)
		fields := fieldsForRadar(radar)

		p.Template("templates/radar.html")
		p.Template("templates/panel.html")
		p.Template("templates/field.html")
		p.Template("templates/comment.html")

		p.Set("Radar", radar)
		p.Set("Title", fmt.Sprintf("%d: %s", radar.Number, radar.Title))
		p.Set("Fields", fields)
	}
	return
}

func radarsForUserHandler(p *PageRequest) (err error) {
	query := datastore.NewQuery("Radar").Order("-Number")
	if query, err = applyCursor(query, p.r.FormValue("c")); err != nil {
		return err
	}
	radars, cursor, err := getRadarsFromQuery(p.c, query, 50)
	if err == nil {
		p.Template("templates/panel.html")
		p.Template("templates/list.html")
		p.Set("Title", "Open Radar")
		p.Set("Radars", radars)
		p.Set("MoreLink", "/radars?c="+cursor)
	}
	return
}

func aboutHandler(p *PageRequest) (err error) {
	p.Set("Title", "About Open Radar")
	err = p.Template("templates/about.html")
	return
}

func recentCommentsHandler(p *PageRequest) (err error) {
	q := datastore.NewQuery("Comment").Order("-Created").Limit(100)
	var comments []Comment
	commentKeys, err := q.GetAll(p.c, &comments)
	// get the radars for each comment
	radarKeys := make([]*datastore.Key, len(comments), len(comments))
	for i, comment := range comments {
		radarKeys[i] = datastore.NewKey(p.c, "Radar", "", comment.RadarNumber, nil)
	}
	radars := make([]Radar, len(comments), len(comments))
	err = datastore.GetMulti(p.c, radarKeys, radars)
	if err != nil {
		return err
	}
	for i, _ := range comments {
		comments[i].Radar = &radars[i]
		comments[i].Key = commentKeys[i]
		comments[i].Number = comments[i].Key.IntID()
	}
	if err == nil {
		p.Set("Comments", comments)
		p.Set("Title", "Recent Comments")
		err = p.Template("templates/comments.html")
		err = p.Template("templates/comment.html")
	}
	return
}

func signoutHandler(w http.ResponseWriter, r *http.Request) {
	c := appengine.NewContext(r)
	url, err := user.LogoutURL(c, "/")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Location", url)
	w.WriteHeader(http.StatusFound)
}

/// helpers

func applyCursor(query_in *datastore.Query, cursor_in string) (query_out *datastore.Query, err error) {
	if cursor_in != "" {
		cursor, err := datastore.DecodeCursor(cursor_in)
		if err == nil {
			return query_in.Start(cursor), nil
		} else {
			return query_in, err
		}
	} else {
		return query_in, nil
	}
}

func getRadarsFromQuery(
	c appengine.Context,
	query *datastore.Query,
	limit int) (radars []Radar, cursor_out string, err error) {

	radars = make([]Radar, 0, limit)
	count := 0
	iterator := query.Run(c)
	for {
		var radar Radar
		_, err := iterator.Next(&radar)
		if err == datastore.Done {
			return radars, "", nil
		} else if err != nil {
			c.Errorf("Radar iterator error: %v", err)
			continue
		} else {
			radars = append(radars, radar)
		}
		count = count + 1
		if count == limit {
			break
		}
	}
	// in case there are more radars, continue using a cursor based on the current position
	if cursor, err := iterator.Cursor(); err == nil {
		cursor_out = cursor.String()
	}
	return radars, cursor_out, nil
}
