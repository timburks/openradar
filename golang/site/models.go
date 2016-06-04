//
// Models
//
package openradar

import (
	"appengine/datastore"
	"time"
)

type Radar struct {
	Number         int64     `json:"number"`
	UserName       string    `json:"user"`
	Title          string    `json:"title"`
	Status         string    `json:"status"`
	Duplicating	   int64     `json:"duplicating"`
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
	// internal
	Key      *datastore.Key `datastore:"-"`
	Comments []*Comment     `datastore:"-"`
}

type Comment struct {
	UserName    string `json:"user"`
	Subject     string `json:"subject"`
	Body        string `json:"body"`
	RadarNumber int64  `json:"radar"`
	IsReplyTo   int64  `json:"is_reply_to"`
	Created     time.Time
	Modified    time.Time
	// internal
	Key          *datastore.Key `datastore:"-"`
	Number       int64          `datastore:"-"`
	Radar        *Radar         `datastore:"-"`
	Replies      []*Comment     `datastore:"-"`
	IsSaved      bool           `datastore:"-"` // true if the comment has been saved in the datastore
	IsEditable   bool           `datastore:"-"` // true if the comment is owned by the current logged-in user
	AllowReplies bool           `datastore:"-"` // true if there is a logged-in user
}

type Profile struct {
	UserName     string `json:"user"`
	ScreenName   string `json:"screen_name"`
	RadarCount   int    `json:"radar_count"`
	CommentCount int    `json:"comment_count"`
	Generation   string `json:"generation"`
}

type APIKey struct {
	UserName string `json:"user"`
	APIKey   string `json:"apikey"`
	Created  time.Time
}

//// Search API documents

type RadarDocument struct {
	Number     string
	SearchText string
}

type CommentDocument struct {
	Number     string
	SearchText string
}
