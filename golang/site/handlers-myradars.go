package openradar

import (
	"appengine/datastore"
	"errors"
	"fmt"
	"github.com/gorilla/mux"
	"strconv"
	"strings"
	"time"
)

func myRadarsHandler(p *PageRequest) (err error) {
	query := datastore.NewQuery("Radar").Filter("UserName =", p.u.Email).Order("-Number")
	if query, err = applyCursor(query, p.r.FormValue("c")); err != nil {
		return err
	}
	radars, cursor, err := getRadarsFromQuery(p.c, query, 1000)
	if err == nil {
		p.Template("templates/myradars.html")
		p.Set("Title", "My Radars")
		p.Set("Radars", radars)
		if cursor != "" {
			p.Set("MoreLink", "/myradars?c="+cursor)
		}
	}
	return
}

func myRadarsAddHandler(p *PageRequest) (err error) {
	p.Template("templates/myradars-add.html")
	p.Set("Title", "Add a Radar")
	p.Set("Action", "/myradars/add")
	if p.r.Method == "GET" {
		p.Set("Message", "Please only post radars that you have filed yourself, and do not include Apple confidential information in your posts.")
		p.Set("Number", "")
		return
	} else if p.r.Method == "POST" {
		number := strings.TrimSpace(p.r.FormValue("number"))
		p.Set("Number", number)
		// parse and validate the radar number
		radarNumber, err := strconv.ParseInt(number, 10, 64)
		if (err != nil) || (radarNumber <= 0) {
			p.Set("Message", "That's not a valid radar number. Radar numbers must be positive integers.")
			return nil
		}
		// look for an existing radar with this number
		radar, err := getRadar(p.c, radarNumber)
		if err == nil {
			if radar.UserName == p.u.Email {
				// if it belongs to this user, go edit it
				p.Redirect(fmt.Sprintf("/myradars/%d", radarNumber))
			} else {
				// if it belongs to someone else, display a message
				p.Set("Message", "A radar with this number exists and was created by another user.")
				return nil
			}
		} else if err == datastore.ErrNoSuchEntity {
			// there was no radar; this isn't an error
			err = nil
		} else {
			// handle possible errors in datastore reading
			p.Set("Message", fmt.Sprintf("An error occurred reading the datastore. (%v)", err))
			return nil
		}
		// create a radar with this number and the current user; initially it will be unpublished
		radar, err = createRadar(p.c, radarNumber, p.u.Email)
		if err != nil {
			// handle possible errors in datastore writing
			p.Set("Message", fmt.Sprintf("An error occurred trying to create this radar. (%v)", err))
			return nil
		} else {
			// go edit the radar
			p.Redirect(fmt.Sprintf("/myradars/%d", radarNumber))
		}
		return err
	} else {
		return err
	}
}

func myRadarsEditHandler(p *PageRequest) (err error) {
	vars := mux.Vars(p.r)
	radarNumber, err := strconv.ParseInt(vars["radar"], 10, 64)
	if err != nil {
		fmt.Fprintf(p.w, "Invalid Radar Number")
		return err
	}
	radar, err := getRadar(p.c, radarNumber)
	if err == nil {
		if radar.UserName == p.u.Email {
			// if it belongs to this user, pass through
		} else {
			// if it belongs to someone else, display a message
			return errors.New("This radar belongs to another user.")
		}
	} else if err == datastore.ErrNoSuchEntity {
		// there was no radar; this isn't an error
		return errors.New("This radar doesn't exist. Do you want to add it?")
	} else {
		// handle possible errors in datastore reading
		return err
	}

	if p.r.Method == "GET" {
		p.Set("Radar", radar)
		p.Set("Message", nil)
	} else if p.r.Method == "POST" {
		radar.ProductVersion = p.r.FormValue("product_version")
		radar.Classification = p.r.FormValue("classification")
		radar.Reproducible = p.r.FormValue("reproducible")
		radar.Status = p.r.FormValue("status")
		radar.Resolved, err = parseTime(p.r.FormValue("resolved"))
		radar.Product = p.r.FormValue("product")
		radar.Title = p.r.FormValue("title")
		radar.Description = p.r.FormValue("description")
		originated, err := parseTime(p.r.FormValue("originated"))
		if err == nil {
			radar.Originated = originated
		}
		radar.Modified = time.Now()
		radar.Published = true
		err = updateRadar(p.c, radar)
		p.Set("Message", "Radar successfully updated.")
		p.Set("Radar", radar)
	} else {
		return errors.New("Unsupported method")
	}

	var repro Selection
	repro.Read("radar-reproducible.yaml")
	repro.Value = radar.Reproducible
	
	var status Selection
	status.Read("radar-status.yaml")
	status.Value = radar.Status

	var classification Selection
	classification.Read("radar-classification.yaml")
	classification.Value = radar.Classification

	var product GroupedSelection
	product.Read("radar-product.yaml")
	product.Value = radar.Product

	p.Template("templates/myradars-edit.html")
	p.Template("templates/selection.html")
	p.Template("templates/selection-grouped.html")
	p.Set("Title", fmt.Sprintf("rdar://%d", radar.Number))
	p.Set("Action", fmt.Sprintf("/myradars/%d", radar.Number))
	p.Set("Reproducibility", repro)
	p.Set("Status", status)
	p.Set("Classification", classification)
	p.Set("Product", product)

	return err
}

func myRadarsDeleteHandler(p *PageRequest) (err error) {
	vars := mux.Vars(p.r)
	radarNumber, err := strconv.ParseInt(vars["radar"], 10, 64)
	if err != nil {
		fmt.Fprintf(p.w, "Invalid Radar Number")
		return err
	}
	radar, err := getRadar(p.c, radarNumber)
	if err == nil {
		if radar.UserName == p.u.Email {
			// if it belongs to this user, pass through
		} else {
			// if it belongs to someone else, display a message
			return errors.New("This radar belongs to another user.")
		}
	} else if err == datastore.ErrNoSuchEntity {
		// there was no radar; this isn't an error
		return errors.New("This radar doesn't exist.")
	} else {
		// handle possible errors in datastore reading
		return err
	}

	err = deleteRadar(p.c, radarNumber)
	p.Redirect("/myradars")
	return err
}
