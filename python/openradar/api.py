"""@package docstring
Provides the web service API.
"""

import google.appengine.api.memcache
import datetime
import simplejson
import db
import base
import models

import os, datetime, re, simplejson

from google.appengine.api import users
from google.appengine.api.urlfetch import *
from google.appengine.api import *

class Comment(base.RequestHandler):
    """Provides web service methods that handle requests to /api/comment."""
    
    def get(self):
        """Returns one or more comments.
        
        Parameters:
        
        count (optional): The number of results to return. Default is 100.
        page (optional): The page of results. Default is 1.
        user (optional): The email address of the comment submitter.
        
        Errors:
        
        400 Bad Request
        """
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
        
class CommentCount(base.RequestHandler):
    """Provides web service methods that handle requests to api/comment/count."""
    
    def get(self):
        """Returns the number of comments.
        
        Parameters:
        
        Errors:
        
        400 Bad Request
        """
        result = db.Comment().fetchCount()
        # Return the result
        self.respondWithDictionaryAsJSON({"result": result})
        
class Radar(base.RequestHandler):
    """Provides web service methods that handle requests to /api/radar."""
    
    def get(self):
        """Returns one or more radars.
        
        Parameters:
        
        count (optional): The number of results to return. Default is 100.
        page (optional): The page of results. Default is 1.
        id (optional): The radar identifier.
        number (optional): The radar number.
        user (optional): The email address of the radar submitter.
        
        Errors:
        
        400 Bad Request
        """
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
        """Add a radar.
        
        Parameters:
        
        number (required):
        classification (optional):
        description (optional):
        originated (optional):
        product (optional):
        product_version (optional):
        reproducible (optional):
        status (optional):
        title (optional):
        
        Errors:
        
        400 Bad Request
        401 Unauthorized
        
        Authentication:
        
        This service requires authentication.
        """
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
        radar.user = currentUser;
        
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
        
        google.appengine.api.memcache.flush_all()
        
        # Return the result
        self.respondWithDictionaryAsJSON({"result": result})
        
class RadarCount(base.RequestHandler):
    """Provides web service methods that handle requests to api/radar/count."""
    
    def get(self):
        """Returns the number of radars.
        
        Parameters:
        
        Errors:
        
        400 Bad Request
        """
        result = db.Radar().fetchCount()
        # Return the result
        self.respondWithDictionaryAsJSON({"result": result})
        
class Search(base.RequestHandler):
    """Provides web service methods that handle requests to api/search."""
    
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
        
class Test(base.RequestHandler):
    def get(self):
        result = {"foo":[1, 2, 3, {"bar": [4, 5, 6]}]}
        self.respondWithDictionaryAsJSON(result)

class TestAuthentication(base.RequestHandler):
    def get(self):
        user = self.GetCurrentUser()
        if user:
          result = {"user":user.nickname(), "foo":[1, 2, 3, {"bar": [4, 5, 6]}]}
          self.respondWithDictionaryAsJSON(result)
        else:
          self.error(401)
          self.respondWithDictionaryAsJSON({"error": "Authentication required."})


class Radars(base.RequestHandler):
  def get(self):
    user = self.GetCurrentUser()
    if (not user):
      self.respondWithDictionaryAsJSON({"error":"please authenticate by setting the Authorization header to your API key (http://www.openradar.me/apikey)"})
      return
    page = self.request.get("page")
    if page:
      page = int(page)
    else:
      page = 1
    if page > 10:
      self.respondWithText("")
      return
    count = self.request.get("count")
    if count:
      count = int(count)
    else:
      count = 100
    apiresult = memcache.get("apiresult")
    if apiresult is None:
      radars = db.GqlQuery("select * from Radar order by number desc").fetch(count,(page-1)*count)
      response = {"result":
                  [{"id":r.key().id(),
                    "classification":r.classification,
                    "created":str(r.created),
                    "description":r.description,
                    "modified":str(r.modified),
                    "number":r.number,
                    "originated":r.originated,
                    "parent":r.parent_number,
                    "product":r.product,
                    "product_version":r.product_version,
                    "reproducible":r.reproducible,
                    "resolved":r.resolved,
                    "status":r.status,
                    "title":r.title,
                    "user":r.user.email()}
                   for r in radars]}
      apiresult = simplejson.dumps(response)
      #memcache.add("apiresult", apiresult, 600) # ten minutes, but we also invalidate on edits and adds
    self.respondWithText(apiresult)

class Comments(base.RequestHandler):
  def get(self):
    user = self.GetCurrentUser()
    if (not user):
      self.respondWithDictionaryAsJSON({"error":"please authenticate by setting the Authorization header to your API key (http://www.openradar.me/apikey)"})
      return
    page = self.request.get("page")
    if page:
      page = int(page)
    else:
      page = 1
    if page > 10:
      self.respondWithText("")
      return
    count = self.request.get("count")
    if count:
      count = int(count)
    else:
      count = 100
    comments = db.GqlQuery("select * from Comment order by posted_at desc").fetch(count,(page-1)*count)
    result = []
    for c in comments:
      try:
        commentInfo = {
          "id":c.key().id(),
          "user":c.user.email(),
          "subject":c.subject,
          "body":c.body,
          "radar":c.radar.number,
          "created":str(c.posted_at),
        }
        if c.is_reply_to:
            commentInfo["is_reply_to"] = c.is_reply_to.key().id()
        result.append(commentInfo)
      except Exception:
        None # we'll get here if the corresponding radar was deleted
    response = {"result":result}
    apiresult = simplejson.dumps(response)
    self.respondWithText(apiresult)

class RadarsNumbers(base.RequestHandler):
  def get(self):
    page = self.request.get("page")
    if page:
      page = int(page)
    else:
      page = 1
    apiresult = memcache.get("apiresult")
    if apiresult is None:
      radars = db.GqlQuery("select * from Radar order by number desc").fetch(100,(page-1)*100)
      response = {"result":[r.number for r in radars]}
      apiresult = simplejson.dumps(response)
    self.respondWithText(apiresult)

class RadarsIDs(base.RequestHandler):
  def get(self):
    page = self.request.get("page")
    if page:
      page = int(page)
    else:
      page = 1
    apiresult = memcache.get("apiresult")
    if apiresult is None:
      radars = db.GqlQuery("select * from Radar order by number desc").fetch(100,(page-1)*100)
      response = {"result":[r.key().id() for r in radars]}
      apiresult = simplejson.dumps(response)
    self.respondWithText(apiresult)

class RadarsAdd(base.RequestHandler):
  def post(self):
    user = self.GetCurrentUser()
    if (not user):
      self.respondWithDictionaryAsJSON({"error":"you must authenticate to add radars"})
    else:
      title = self.request.get("title")
      number = self.request.get("number")
      status = self.request.get("status")
      description = self.request.get("description")
      resolved = self.request.get("resolved")
      product = self.request.get("product")
      classification = self.request.get("classification")
      reproducible = self.request.get("reproducible")
      product_version = self.request.get("product_version")
      originated = self.request.get("originated")
      radar = Radar(title=title,
                    number=number,
                    user=user,
                    status=status,
                    description=description,
                    resolved=resolved,
                    product=product,
                    classification=classification,
                    reproducible=reproducible,
                    product_version=product_version,
                    originated=originated,
                    created=datetime.datetime.now(),
                    modified=datetime.datetime.now())
      radar.put()
      memcache.flush_all()
      response = {"result":
                   {"title":title,
                    "number":number,
                    "status":status,
                    "description":description}}
      self.respondWithDictionaryAsJSON(response)

class Secret(base.RequestHandler):
  def get(self):
    name = self.request.get("name")
    value = self.request.get("value")
    secret = Secret(name=name, value=value)
    secret.put()
    self.respondWithDictionaryAsJSON({"name":name, "value":value})

class RadarsRecent(base.RequestHandler):
  def get(self):
    user = self.GetCurrentUser()
    if (not user):
      self.respondWithDictionaryAsJSON({"error":"please authenticate by setting the Authorization header to your API key (http://www.openradar.me/apikey)"})
      return
    cursor = self.request.get("cursor")
    if cursor:
      cursor = cursor
    else:
      cursor = None
    radars = db.GqlQuery("select * from Radar order by modified desc")
    if cursor:
      radars.with_cursor(start_cursor=cursor)
    results = []
    for r in radars:
      results.append({"id":r.key().id(),
                      "title":r.title,
                      "number":r.number,
                      "user":r.user.email(),
                      "status":r.status,
                      "description":r.description,
                      "resolved":r.resolved,
                      "product":r.product,
                      "classification":r.classification,
                      "reproducible":r.reproducible,
                      "product_version":r.product_version,
		      "created":str(r.created),
                      "modified":str(r.modified),
                      "originated":r.originated})
      if len(results) == 100:
        break
    response = {"result":results, "cursor":radars.cursor()}
    apiresult = simplejson.dumps(response)
    self.respondWithText(apiresult)

class CommentsRecent(base.RequestHandler):
  def get(self):
    user = self.GetCurrentUser()
    if (not user):
      self.respondWithDictionaryAsJSON({"error":"please authenticate by setting the Authorization header to your API key (http://www.openradar.me/apikey)"})
      return
    cursor = self.request.get("cursor")
    if cursor:
      cursor = cursor
    else:
      cursor = None
    comments = db.GqlQuery("select * from Comment order by posted_at desc")
    if cursor:
      comments.with_cursor(start_cursor=cursor)
    results = []
    for c in comments:
      try:
        results.append({"id":c.key().id(),
                        "user":c.user.email(),
                        "subject":c.subject,
                        "body":c.body,
                        "radar":c.radar.number,
                        "posted_at":str(c.posted_at),
                        "is_reply_to":c.is_reply_to and c.is_reply_to.key().id() or None})
      except Exception:
        None
      if len(results) == 100:
        break
    response = {"result":results, "cursor":comments.cursor()}
    apiresult = simplejson.dumps(response)
    self.respondWithText(apiresult)
