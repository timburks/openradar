package openradar

import (
	"appengine"
	"appengine/datastore"
	"code.google.com/p/go-uuid/uuid"
	"time"
)

func getAPIKeyForUserName(context appengine.Context, username string) (apikey *APIKey, err error) {
	key := datastore.NewKey(context, "APIKey", username, 0, nil)
	apikey = &APIKey{}
	err = datastore.Get(context, key, apikey)
	if err == nil {
		context.Infof("Found key %s for username %s", apikey.APIKey, username)
		return apikey, nil
	} else {
		return nil, err
	}
}

func getOrCreateAPIKeyForUserName(context appengine.Context, username string) (apikey *APIKey, err error) {
	apikey, err = getAPIKeyForUserName(context, username)
	if err == datastore.ErrNoSuchEntity {
		key := datastore.NewKey(context, "APIKey", username, 0, nil)
		apikey = &APIKey{}
		apikey.UserName = username
		apikey.APIKey = uuid.New()
		apikey.Created = time.Now()
		_, err = datastore.Put(context, key, apikey)
		context.Infof("Generated key %s for username %s", apikey.APIKey, username)
	}
	return apikey, err
}

func deleteAPIKeyForUserName(context appengine.Context, username string) (err error) {
	key := datastore.NewKey(context, "APIKey", username, 0, nil)
	err = datastore.Delete(context, key)
	context.Infof("Deleted key for username %s", username)
	return err
}
