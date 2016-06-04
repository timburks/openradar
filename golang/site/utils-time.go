package openradar

import (
	"errors"
	"time"
)

func parseTime(s string) (t time.Time, err error) {
	if s == "" {
		return t, errors.New("empty time string")
	}

	timeFormats := []string{
		"2006-01-02 15:04 (UTC)",
		"2006-01-02 15:04",
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
