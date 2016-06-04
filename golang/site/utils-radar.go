package openradar

import (
	"appengine"
	"appengine/datastore"
	"time"
)

func getRadar(context appengine.Context, radarNumber int64) (radar *Radar, err error) {
	key := datastore.NewKey(context, "Radar", "", radarNumber, nil)
	radar = &Radar{}
	err = datastore.Get(context, key, radar)
	radar.Key = key
	return radar, err
}

func createRadar(context appengine.Context, radarNumber int64, username string) (radar *Radar, err error) {
	key := datastore.NewKey(context, "Radar", "", radarNumber, nil)
	radar = &Radar{}
	radar.Number = radarNumber
	radar.UserName = username
	radar.Published = false
	now := time.Now()
	radar.Originated = now
	radar.Created = now
	radar.Modified = now
	_, err = datastore.Put(context, key, radar)
	radar.Key = key
	return radar, err
}

func deleteRadar(context appengine.Context, radarNumber int64) (err error) {
	key := datastore.NewKey(context, "Radar", "", radarNumber, nil)
	return datastore.Delete(context, key)
}

func updateRadar(context appengine.Context, radar *Radar) (err error) {
	key := radar.Key
	_, err = datastore.Put(context, key, radar)
	return err
}

func getCommentsForRadar(context appengine.Context, username string, radar *Radar) (err error) {
	q2 := datastore.NewQuery("Comment").Filter("RadarNumber =", radar.Number).Order("Created")
	var comments []Comment
	keys, err := q2.GetAll(context, &comments)

	// build a map of comments by number
	commentsByNumber := make(map[int64]*Comment)
	for i, _ := range comments {
		comment := &comments[i]
		comment.Replies = make([]*Comment, 0)
		comment.Key = keys[i]
		comment.Number = comment.Key.IntID()
		if comment.UserName == username {
			comment.IsEditable = true
		}
		if username != "" {
			comment.AllowReplies = true
		}
		commentsByNumber[comment.Number] = comment
	}

	// resolve threading and build a map holding the comments that were threaded
	commentsThatWereThreaded := make(map[int64]*Comment)
	for i, _ := range comments {
		comment := &comments[i]
		isReplyTo := comment.IsReplyTo
		if isReplyTo != 0 {
			parent, found := commentsByNumber[isReplyTo]
			if found {
				parent.Replies = append(parent.Replies, comment)
				commentsThatWereThreaded[comment.Number] = comment
			}
		}
	}

	// attach top-level comments to the radar
	radar.Comments = make([]*Comment, 0)
	for i, _ := range comments {
		comment := &comments[i]
		_, found := commentsThatWereThreaded[comment.Number]
		if !found {
			radar.Comments = append(radar.Comments, comment)
		}
	}

	return err
}

func getComment(context appengine.Context, username string, commentNumber int64) (comment *Comment, err error) {
	key := datastore.NewKey(context, "Comment", "", commentNumber, nil)
	comment = &Comment{}
	err = datastore.Get(context, key, comment)
	comment.Number = key.IntID()
	comment.Key = key
	comment.IsSaved = true
	if comment.UserName == username {
		comment.IsEditable = true
	}
	if username != "" {
		comment.AllowReplies = true
	}
	return comment, err
}

func saveComment(context appengine.Context, comment *Comment) (err error) {
	key := datastore.NewKey(context, "Comment", "", comment.Number, nil)
	now := time.Now()
	comment.Modified = now
	context.Infof("Saving comment %+v", comment)
	key, err = datastore.Put(context, key, comment)
	comment.Number = key.IntID()
	comment.Key = key
	return err
}

func deleteComment(context appengine.Context, comment *Comment) (err error) {	
	return datastore.Delete(context, comment.Key)
}

