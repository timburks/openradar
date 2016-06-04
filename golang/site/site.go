package openradar

import (
	_ "appengine/remote_api"
	"github.com/gorilla/mux"
	"net/http"
)

func init() {
	router := mux.NewRouter()

	// The OpenRadar web site
	router.HandleFunc("/", auth(false, pageHandler))
	router.HandleFunc("/about", auth(false, aboutHandler))
	router.HandleFunc("/apikey", auth(true, apiKeyHandler))
	router.HandleFunc("/comments", auth(false, recentCommentsHandler))
	router.HandleFunc("/radar", auth(false, radarHandler))
	router.HandleFunc("/radars", auth(false, pageHandler))
	router.HandleFunc("/radars/{user}", auth(false, radarsForUserHandler))
	router.HandleFunc("/signout", signoutHandler)
	router.HandleFunc("/{radar:[0-9]+}", auth(false, radarHandler))

	// AJAX Commenting support
	router.HandleFunc("/comment", auth(true, ajaxCommentHandler))
	router.HandleFunc("/comment/remove", auth(true, ajaxCommentRemoveHandler))

	// User Radar management
	router.HandleFunc("/myradars", auth(true, myRadarsHandler))
	router.HandleFunc("/myradars/add", auth(true, myRadarsAddHandler))
	router.HandleFunc("/myradars/{radar:[0-9]+}", auth(true, myRadarsEditHandler))
	router.HandleFunc("/myradars/{radar:[0-9]+}/delete", auth(true, myRadarsDeleteHandler))

	// The OpenRadar API
	router.HandleFunc("/api/comment", api(apiCommentHandler))
	router.HandleFunc("/api/comment/count", api(apiCommentCountHandler))
	router.HandleFunc("/api/comments", api(apiCommentsHandler))
	router.HandleFunc("/api/radar", api(apiRadarHandler))
	router.HandleFunc("/api/radar/count", api(apiRadarCountHandler))
	router.HandleFunc("/api/radars", api(apiRadarsHandler))
	router.HandleFunc("/api/radars/add", api(apiRadarsAddHandler))
	router.HandleFunc("/api/radars/numbers", api(apiRadarsNumbersHandler))
	router.HandleFunc("/api/radars/ids", api(apiRadarsIdsHandler))
	router.HandleFunc("/api/search", api(apiSearchHandler))
	router.HandleFunc("/api/test", api(apiTestHandler))
	router.HandleFunc("/api/test_authentication", api(apiTestAuthenticationHandler))
	router.HandleFunc("/api/radars/recent", api(apiRadarsRecentHandler))
	router.HandleFunc("/api/comments/recent", api(apiCommentsRecentHandler))

	router.HandleFunc("/api/selections", api(apiSelectionsHandler))


	// Service API (internal use only)
	router.HandleFunc("/api/updateprofiles", apiUpdateProfilesHandler)

	// Register the router
	http.Handle("/", router)
}
