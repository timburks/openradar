import simplejson
import db
import handlers
import models

class Radar(handlers.Handler):
    def get(self):
        radar = None
        radarId = self.request.get("id")
        if radarId:
            radar = db.Radar().getById(radarId)
            if (radar):
                self.respondWithDictionaryAsJSON(radar.toDictionary())
            return
        radarNumber = self.request.get("number")
        if radarNumber:
            radar = db.Radar().getByNumber(radarNumber)
            if (radar):
                self.respondWithDictionaryAsJSON(radar.toDictionary())
            return
    
    def post(self):
        pass

class Test(handlers.Handler):
    def get(self):
        result = {"foo":[1, 2, 3, {"bar": [4, 5, 6]}]}
        self.respondWithDictionaryAsJSON(result)

