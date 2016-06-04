//
// Readers for YAML files that describe selection values for enumerated properties
//
package openradar

import (
	"gopkg.in/yaml.v2"
	"io/ioutil"
)

// a simple list of values
type Selection struct {
	Title  string   `yaml:"title" json:"title"`
	Id     string   `yaml:"id" json:"id"`
	Values []string `yaml:"values" json:"values"`
	Value  string   `json:"-"`
}

// a list of grouped values
type GroupedSelection struct {
	Title  string      `yaml:"title" json:"title"`
	Id     string      `yaml:"id" json:"id"`
	Groups []Selection `yaml:"groups" json:"groups"`
	Value  string      `json:"-"`
}

func (selection *Selection) Read(filename string) (err error) {
	data, err := ioutil.ReadFile(filename)
	if err != nil {
		return err
	}
	return yaml.Unmarshal(data, selection)
}

func (selection *GroupedSelection) Read(filename string) (err error) {
	data, err := ioutil.ReadFile(filename)
	if err != nil {
		return err
	}
	return yaml.Unmarshal(data, selection)
}
