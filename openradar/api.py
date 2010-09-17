import google.appengine.api.users
import simplejson
import db
import handlers
import models

class Radar(handlers.Handler):
    def get(self):
        result = {}
        count = self.request.get("count")
        if count:
            count = int(count)
        else:
            count = 100
        page = self.request.get("page")
        if page:
            page = int(page)
        else:
            page = 1
        radarId = self.request.get("id")
        if radarId:
            radar = db.Radar().fetchById(radarId)
            if (radar):
                result = radar.toDictionary()
        if not result:
            radarNumber = self.request.get("number")
            if radarNumber:
                radar = db.Radar().fetchByNumber(radarNumber)
                if (radar):
                    result = radar.toDictionary()
        if not result:
            user = google.appengine.api.users.User(self.request.get("user"))
            if user:
                radars = db.Radar().fetchByUser(user, page, count)
                if radars:
                    result = [radar.toDictionary() for radar in radars]
        self.respondWithDictionaryAsJSON({"result": result})
        
    def post(self):
        pass
        
class Search(handlers.Handler):
    def get(self):
        result = {}
        radars = None
        count = self.request.get("count")
        if count:
            count = int(count)
        else:
            count = 100
        page = self.request.get("page")
        if page:
            page = int(page)
        else:
            page = 1
        searchQuery = self.request.get("q")
        keywords = searchQuery.split("+")
        keyword = keywords[0]
        try:
            radars = models.Radar.all().search(keyword).order("-number").fetch(count, (page - 1) * count)
        except Exception:
            radars = None
        if radars and len(radars) > 0:
            result = [radar.toDictionary() for radar in radars]
        self.respondWithDictionaryAsJSON({"result": result})
        
class Test(handlers.Handler):
    def get(self):
        result = {"foo":[1, 2, 3, {"bar": [4, 5, 6]}]}
        self.respondWithDictionaryAsJSON(result)
        

