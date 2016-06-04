//
// Helpers for templates
//
package openradar

import (
	"fmt"
	"github.com/microcosm-cc/bluemonday"
	"github.com/russross/blackfriday"
	"html/template"
	"strings"
	"time"
)

func DateFormat(d interface{}) (formattedDate string) {
	if d == nil {
		formattedDate = ""
	} else {
		date := d.(time.Time)
		formattedDate = fmt.Sprintf("%v, %v %d, %d", date.Weekday().String(), date.Month().String(), date.Day(), date.Year())
	}
	return
}

func ShortDateFormat(d interface{}) (formattedDate string) {
	if d == nil {
		formattedDate = ""
	} else {
		date := d.(time.Time)
		formattedDate = fmt.Sprintf("%d-%02d-%02d", date.Year(), date.Month(), date.Day())
	}
	return
}

func ScreenNameForUserName(name string) string {
	parts := strings.Split(name, "@")
	if len(parts) > 1 {
		return parts[0]
	} else {
		return name
	}
}

func templateHelper_truncate(in string) (out string) {
	limit := 18
	if len(in) <= limit {
		return in
	} else {
		return in[0:limit]
	}
}

func templateHelper_displayDate(in time.Time) (out string) {
	if in.IsZero() {
		return "Not Yet"
	} else {
		return in.Format("2006-01-02 15:04 (UTC)")
	}
}

func templateHelper_markdown(in string) (out template.HTML) {
	unsafe := blackfriday.MarkdownCommon([]byte(in))
	return template.HTML(string(bluemonday.UGCPolicy().SanitizeBytes(unsafe)))
}
