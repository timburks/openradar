import simplejson
import db
import handlers
import models

class Radar(handlers.Handler):
    def get(self):
        result = {}
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
        self.respondWithDictionaryAsJSON({"result": result})
        
    def post(self):
        pass
        

class Test(handlers.Handler):
    def get(self):
        result = {"foo":[1, 2, 3, {"bar": [4, 5, 6]}]}
        self.respondWithDictionaryAsJSON(result)
        

