package openradar

func apiCommentHandler(request *APIRequest) (err error) {
	return
}

func apiCommentCountHandler(request *APIRequest) (err error) {
	return
}

func apiCommentsHandler(request *APIRequest) (err error) {
	return
}

func apiRadarHandler(request *APIRequest) (err error) {
	return
}

func apiRadarCountHandler(request *APIRequest) (err error) {
	return
}

func apiRadarsHandler(request *APIRequest) (err error) {
	return
}

func apiRadarsAddHandler(request *APIRequest) (err error) {
	return
}

func apiRadarsNumbersHandler(request *APIRequest) (err error) {
	return
}

func apiRadarsIdsHandler(request *APIRequest) (err error) {
	return
}

func apiSearchHandler(request *APIRequest) (err error) {
	return
}

func apiTestHandler(request *APIRequest) (err error) {
	return
}

func apiTestAuthenticationHandler(request *APIRequest) (err error) {
	return
}

func apiRadarsRecentHandler(request *APIRequest) (err error) {
	return
}

func apiCommentsRecentHandler(request *APIRequest) (err error) {
	return
}

type Selections struct {
	Reproducible   Selection        `json:"reproducible"`
	Status         Selection        `json:"status"`
	Classification Selection        `json:"classification"`
	Product        GroupedSelection `json:"product"`
}

func apiSelectionsHandler(request *APIRequest) (err error) {
	var selections Selections
	selections.Reproducible.Read("radar-reproducible.yaml")
	selections.Status.Read("radar-status.yaml")
	selections.Classification.Read("radar-classification.yaml")
	selections.Product.Read("radar-product.yaml")
	request.Set("selections", selections)
	return err
}
