package openradar

import (
	"appengine"
	"appengine/datastore"
	"appengine/delay"
	"appengine/urlfetch"
	"fmt"
	"net/http"
	"net/url"
	"runtime"
	"strconv"
)

func getProfileForUserName(context appengine.Context, username string) (profile *Profile, err error) {
	profile = &Profile{}
	// does the username have a profile?
	key := datastore.NewKey(context, "Profile", username, 0, nil)
	err = datastore.Get(context, key, &profile)
	if err == nil {
		return profile, nil // we have a profile for this username
	}
	// if not, create it and use the first part of the username as the screen name
	profile.UserName = username
	profile.ScreenName = ScreenNameForUserName(username)
	_, err = datastore.Put(context, key, profile)
	return profile, err
}

func createProfile(username string, generation string) (profile *Profile) {
	profile = &Profile{}
	profile.UserName = username
	profile.RadarCount = 0
	profile.CommentCount = 0
	profile.ScreenName = ScreenNameForUserName(username)
	profile.Generation = generation
	return profile
}

func logMemoryUsage(context appengine.Context) {
	var s runtime.MemStats
	runtime.ReadMemStats(&s)
	context.Infof("Memory usage: %d bytes (%d system).", s.Alloc, s.Sys)
}

func updateProfileEntities(
	context appengine.Context, 
	profiles map[string]*Profile, 
	generation string, 
	kind string,
	count int) {
	// collect keys and new profile values into arrays
	keys := make([]*datastore.Key, 0)
	newvalues := make([]*Profile, 0)
	for username, profile := range profiles {
		key := datastore.NewKey(context, "Profile", username, 0, nil)
		keys = append(keys, key)
		newvalues = append(newvalues, profile)
	}
	// get all of the old profile values
	oldvalues := make([]*Profile, len(keys))
	err := datastore.GetMulti(context, keys, oldvalues)
	// if the old values are from the current generation, add their counts into the new values
	for i := 0; i < len(keys); i++ {
		if (oldvalues[i] != nil) && (oldvalues[i].Generation == generation) {
			newvalues[i].RadarCount += oldvalues[i].RadarCount
			newvalues[i].CommentCount += oldvalues[i].CommentCount
		}
	}
	// store all of the new values
	_, err = datastore.PutMulti(context, keys, newvalues)
	if err == nil {
		context.Infof("Updated %d profiles for %d %s", len(profiles), count, kind)
	} else {
		context.Infof("Error updating %d profiles for %d %s (%v)", len(profiles), count, kind, err)
	}
}

func updateProfilesFromRadars(
	context appengine.Context,
	generation string,
	cursor_string string,
	chunk int) (count int, err error) {

	context.Infof("Radars Chunk %d", chunk)

	profiles := make(map[string]*Profile)

	query := datastore.NewQuery("Radar").Project("UserName")
	if cursor_string != "" {
		cursor, err := datastore.DecodeCursor(cursor_string)
		if err == nil {
			query = query.Start(cursor)
		} else {
			return count, err
		}
	}

	iterator := query.Run(context)
	count = 0
	for {
		var radar Radar
		_, err := iterator.Next(&radar)
		if err == datastore.Done {
			break
		} else if err != nil {
			context.Errorf("Radar iterator error: %v", err)
			continue
		} else {
			username := radar.UserName
			profile, found := profiles[username]
			if !found {
				profile = createProfile(username, generation)
				profiles[username] = profile
			}
			profile.RadarCount++
		}
		count = count + 1
		// we can't write more than 500 entities in a single call to PutMulti,
		// so we stop after 500 radars
		if count == 500 {
			break
		}
	}

	updateProfileEntities(context, profiles, generation, "radars", count)

	if count == 500 {
		// in case there are more radars, continue using a cursor based on the current position
		if cursor, err := iterator.Cursor(); err == nil {
			data := url.Values{}
			data.Set("generation", generation)
			data.Set("cursor", cursor.String())
			data.Set("chunk", strconv.Itoa(chunk+1))
			client := urlfetch.Client(context)
			request, _ := http.NewRequest("GET", "http://openradar-golang.appspot.com/api/updateprofiles"+"?"+data.Encode(), nil)
			response, err := client.Do(request)
			context.Infof("response %+v (%+v)", response, err)
		}
	} else {
		// if this was our last time through, start looping through comments
		data := url.Values{}
		data.Set("generation", generation)
		data.Set("source", "comments")
		client := urlfetch.Client(context)
		request, _ := http.NewRequest("GET", "http://openradar-golang.appspot.com/api/updateprofiles"+"?"+data.Encode(), nil)
		response, err := client.Do(request)
		context.Infof("response %+v (%+v)", response, err)
	}
	logMemoryUsage(context)
	return count, err
}

func updateProfilesFromComments(
	context appengine.Context,
	generation string,
	cursor_string string,
	chunk int) (count int, err error) {

	context.Infof("Comments Chunk %d", chunk)

	profiles := make(map[string]*Profile)

	query := datastore.NewQuery("Comment").Project("UserName")
	if cursor_string != "" {
		cursor, err := datastore.DecodeCursor(cursor_string)
		if err == nil {
			query = query.Start(cursor)
		} else {
			return count, err
		}
	}

	iterator := query.Run(context)
	count = 0
	for {
		var comment Comment
		_, err := iterator.Next(&comment)
		if err == datastore.Done {
			break
		} else if err != nil {
			context.Errorf("Comment iterator error: %v", err)
			continue
		} else {
			username := comment.UserName
			profile, found := profiles[username]
			if !found {
				profile = createProfile(username, generation)
				profiles[username] = profile
			}
			profile.CommentCount++
		}
		count = count + 1
		// we can't write more than 500 entities in a single call to PutMulti,
		// so we stop after 500 comments
		if count == 500 {
			break
		}
	}

	updateProfileEntities(context, profiles, generation, "comments", count)

	if count == 500 {
		// in case there are more comments, continue using a cursor based on the current position
		if cursor, err := iterator.Cursor(); err == nil {
			data := url.Values{}
			data.Set("generation", generation)
			data.Set("cursor", cursor.String())
			data.Set("chunk", strconv.Itoa(chunk+1))
			data.Set("source", "comments")
			client := urlfetch.Client(context)
			request, _ := http.NewRequest("GET", "http://openradar-golang.appspot.com/api/updateprofiles"+"?"+data.Encode(), nil)
			response, err := client.Do(request)
			context.Infof("response %+v (%+v)", response, err)
		}
	} else {
		// if this was our last time through, delete any profiles that aren't in the current generation
		context.Infof("TODO: delete stale profiles")
	}
	logMemoryUsage(context)
	return count, err
}

var delayedUpdateProfilesFromRadarsHandler = delay.Func("update-profiles-1", updateProfilesFromRadars)
var delayedUpdateProfilesFromCommentsHandler = delay.Func("update-profiles-2", updateProfilesFromComments)

func apiUpdateProfilesHandler(w http.ResponseWriter, r *http.Request) {
	context := appengine.NewContext(r)
	cursor := r.FormValue("cursor")
	generation := r.FormValue("generation")
	source := r.FormValue("source")
	chunk, _ := strconv.Atoi(r.FormValue("chunk"))
	if source == "comments" {
		delayedUpdateProfilesFromCommentsHandler.Call(context, generation, cursor, chunk)
	} else {
		delayedUpdateProfilesFromRadarsHandler.Call(context, generation, cursor, chunk)
	}
	fmt.Fprintf(w, "OK generation=%s cursor=%s chunk=%d\n", generation, cursor, chunk)
}
