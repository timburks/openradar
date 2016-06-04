package openradar

import (
	"fmt"
)

type Field struct {
	Name  string
	Value string
}

func fieldsForRadar(radar *Radar) (fields []Field) {
	fields = make([]Field, 0)
	fields = []Field{{
		"Number",
		fmt.Sprintf("%d", radar.Number),
	}, {
		"Originator",
		ScreenNameForUserName(radar.UserName),
	}, {
		"Date Originated",
		templateHelper_displayDate(radar.Originated),
	}, {
		"Status",
		fmt.Sprintf("%v", radar.Status),
	}, {
		"Resolved",
		templateHelper_displayDate(radar.Resolved),
	}, {
		"Product",
		fmt.Sprintf("%v", radar.Product),
	}, {
		"Product Versions",
		fmt.Sprintf("%v", radar.ProductVersion),
	}, {
		"Classification",
		fmt.Sprintf("%v", radar.Classification),
	}, {
		"Reproducible",
		fmt.Sprintf("%v", radar.Reproducible),
	}}
	return fields
}
