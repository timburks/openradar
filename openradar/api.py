import google.appengine.api.memcache
import google.appengine.api.users
import datetime
import simplejson
import db
import handlers
import models

class Comment(handlers.Handler):
    def get(self):
        result = {}
        count = self.request.get("count")
        if (count):
            count = int(count)
        else:
            count = 100
        page = self.request.get("page")
        if (page):
            page = int(page)
        else:
            page = 1
        user = google.appengine.api.users.User(self.request.get("user"))
        if (user):
            comments = db.Comment().fetchByUser(user, page, count)
            if (comments):
                result = [comment.toDictionary() for comment in comments]
        
        # Return the result
        self.respondWithDictionaryAsJSON({"result": result})
        
    def post(self):
        pass

class Radar(handlers.Handler):
    def get(self):
        result = {}
        count = self.request.get("count", None)
        if (count):
            count = int(count)
        else:
            count = 100
        page = self.request.get("page", None)
        if (page):
            page = int(page)
        else:
            page = 1
        parameters = [];
        radarId = self.request.get("id")
        if (radarId):
            parameters.append(radarId)
            radar = db.Radar().fetchById(int(radarId))
            if (radar):
                result = radar.toDictionary()
        if (not result):
            radarNumber = self.request.get("number")
            if radarNumber:
                parameters.append(radarNumber)
                radar = db.Radar().fetchByNumber(radarNumber)
                if (radar):
                    result = radar.toDictionary()
        if (not result):
            userName = self.request.get("user")
            if (userName):
                parameters.append(userName)
                user = google.appengine.api.users.User(userName)
                if (user):
                    radars = db.Radar().fetchByUser(user, page, count)
                    if (radars):
                        result = [radar.toDictionary() for radar in radars]
        if (not result and not parameters):
            radars = db.Radar().fetchAll(page, count)
            if (radars):
                result = [radar.toDictionary() for radar in radars]
        
        # Return the result
        self.respondWithDictionaryAsJSON({"result": result})
        
    def post(self):
        result = {}
        
        currentUser = google.appengine.api.users.GetCurrentUser()
        if (not currentUser):
            # Unauthorized
            self.error(401)
            self.respondWithDictionaryAsJSON({"error": "Authentication required."})
            return
        
        radar = models.Radar(
            created = datetime.datetime.now(),
            modified = datetime.datetime.now())
        
        # Required
        radar.number = self.request.get("number", None)
        if (radar.number == None):
            # Bad Request
            self.error(400)
            self.respondWithDictionaryAsJSON({"error": "Missing required parameter."})
            return;
        
        # Optional
        radar.classification = self.request.get("classification", None)
        radar.description = self.request.get("description", None)
        radar.originated = self.request.get("originated", None)
        radar.product = self.request.get("product", None)
        radar.product_version = self.request.get("product_version", None)
        # radar.resolved = self.request.get("resolved", None)
        radar.reproducible = self.request.get("reproducible", None)
        radar.status = self.request.get("status", None)
        radar.title = self.request.get("title", None)
        
        # Save
        radar.put()
        
        if (radar.key() != None):
            result = radar.toDictionary();
        
        # Return the result
        self.respondWithDictionaryAsJSON({"result": result})
        
class Search(handlers.Handler):
    def get(self):
        result = {}
        radars = None
        
        count = self.request.get("count")
        if (count):
            count = int(count)
        else:
            count = 100
        
        page = self.request.get("page")
        if (page):
            page = int(page)
        else:
            page = 1
        
        scope = self.request.get("scope")
        if (not scope):
            scope = "all"
        
        searchQuery = self.request.get("q")
        keywords = searchQuery.split(" ")
        keyword = keywords[0]
        
        try:
            if (scope == "number"):
                radars = db.Radar().fetchByNumbers(keywords, page, count)
            elif (scope == "user"):
                users = []
                for userName in keywords:
                    user = google.appengine.api.users.User(userName)
                    if user:
                        users.append(user)
                radars = db.Radar().fetchByUsers(users, page, count);
            else:
                radars = models.Radar.all().search(keyword).order("-number").fetch(count, (page - 1) * count)
        except Exception:
            radars = None
        
        if (radars and len(radars) > 0):
            result = [radar.toDictionary() for radar in radars]
        
        # Return the result
        self.respondWithDictionaryAsJSON({"result": result})
        
class Test(handlers.Handler):
    def get(self):
        result = {"foo":[1, 2, 3, {"bar": [4, 5, 6]}]}
        self.respondWithDictionaryAsJSON(result)
        

