#!/usr/bin/env python
import os, datetime, re, simplejson
import urllib, base64

import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api.urlfetch import *
from google.appengine.api import memcache

from models import *
from handlers import *

class IndexAction(Handler):
  def get(self):  
    biglist = memcache.get("biglist")
    if biglist is None:
      radars = db.GqlQuery("select * from Radar order by number desc").fetch(1000)
      path = os.path.join(os.path.dirname(__file__), os.path.join('templates', 'biglist.html'))
      biglist = template.render(path, {'radars':radars})
      memcache.add("biglist", biglist, 600) # ten minutes, but we also invalidate on edits and adds
    self.respondWithTemplate('index.html', {"biglist": biglist})

class FAQAction(Handler):
  def get(self):    
    self.respondWithTemplate('faq.html', {})

class RadarAddAction(Handler):
  def get(self):    
    user = users.GetCurrentUser()
    if (not user):
      self.respondWithTemplate('please-sign-in.html', {'action': 'add Radars'})
    else:
      self.respondWithTemplate('radar-add.html', {})
  def post(self):
    user = users.GetCurrentUser()
    if (not user):
      self.respondWithTemplate('please-sign-in.html', {'action': 'add Radars'})
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
                    status=status,
                    user=user,
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
      # tweet this.
      if 1:
        tweet = ("[rdar://%s] %s: %s" % (number, radar.username(), title))
        tweet = tweet[0:140]
        secrets = db.GqlQuery("select * from Secret where name = :1", "retweet").fetch(1)
        if len(secrets) > 0:
          secret = secrets[0].value
          form_fields = {
            "message": tweet,
            "secret": secret
          }
          form_data = urllib.urlencode(form_fields)
          result = fetch("http://www.neontology.com/retweet.php", payload=form_data, method=POST)
      self.redirect("/myradars")

class RadarViewByIdAction(Handler):
  def get(self):    
    id = self.request.get("id")
    radar = Radar.get_by_id(int(id))
    if (not radar):
      self.respondWithText('Invalid Radar id')
      return
    
    comments = Comment.gql("WHERE radar = :1", radar)
      
    self.respondWithTemplate('radar-view.html', {"radar":radar, "comments": comments})

class RadarViewByNumberAction(Handler):
  def get(self):    
    number = self.request.get("number")
    radars = Radar.gql("WHERE number = :1", number).fetch(1)
    if len(radars) != 1:
      self.respondWithText('Invalid Radar id')
      return
    radar = radars[0]
    if (not radar):
      self.respondWithText('Invalid Radar id')
      return
    
    comments = Comment.gql("WHERE radar = :1 AND is_reply_to = :2", radar, None)
    
    self.respondWithTemplate('radar-view.html', {"radar":radar, "comments": comments})

class RadarEditAction(Handler):
  def get(self):    
    user = users.GetCurrentUser()
    if (not user):
      self.respondWithTemplate('please-sign-in.html', {'action': 'edit Radars'})
    else:
      id = self.request.get("id")
      radar = Radar.get_by_id(int(id))
      if (not radar):
        self.respondWithText('Invalid Radar id')
      else:
        self.respondWithTemplate('radar-edit.html', {"radar":radar})

  def post(self):
    user = users.GetCurrentUser()
    if (not user):
      self.respondWithTemplate('please-sign-in.html', {'action': 'edit Radars'})
    else:
      id = self.request.get("id")
      radar = Radar.get_by_id(int(id))
      if not radar:
        self.respondWithText('Invalid Radar id')
      elif radar.user != user:
        self.respondWithText('Only the owner of a Radar can edit it')
      else:
        radar.title = self.request.get("title")
        radar.number = self.request.get("number")
        radar.status = self.request.get("status")
        radar.description = self.request.get("description")
        radar.resolved = self.request.get("resolved")
        radar.product = self.request.get("product")
        radar.classification = self.request.get("classification")
        radar.reproducible = self.request.get("reproducible")
        radar.product_version = self.request.get("product_version")
        radar.originated = self.request.get("originated")
        radar.modified = datetime.datetime.now()
        radar.put()
        memcache.flush_all()
        self.redirect("/myradars")
        
class RadarDeleteAction(Handler):
  def get(self):
    user = users.GetCurrentUser()
    id = self.request.get("id")
    radar = Radar.get_by_id(int(id))
    if (not user):
      self.respondWithTemplate('please-sign-in.html', {'action': 'delete Radars'})
    elif (not radar):
      self.respondWithText('Invalid Radar id')
    else:
      radar.delete()
      memcache.flush_all()
      self.redirect("/myradars")

class RadarListAction(Handler):
  def get(self):    
    user = users.GetCurrentUser()
    if (not user):
      self.respondWithTemplate('please-sign-in.html', {'action': 'view your Radars'})
    else:
      radars = db.GqlQuery("select * from Radar where user = :1 ", user).fetch(1000)
      self.respondWithTemplate('radar-list.html', {"radars": radars})

class NotFoundAction(Handler):
  def get(self):
    self.response.out.write("<h1>Resource not found</h1>")
    self.response.out.write("<pre>")
    self.response.out.write(self.request)
    self.response.out.write("</pre>")

class HelloAction(Handler):
  def get(self):
    user = users.get_current_user()
    if not user:
      # The user is not signed in.
      print "Hello"
    else:
      print "Hello, %s!" % user.nickname()

class APITestAction(Handler):
  def get(self):
    response = {"foo":[1,2,3,{"bar":[4,5,6]}]}
    self.respondWithDictionaryAsJSON(response)

class APIRadarsAction(Handler):
  def get(self):
    apiresult = memcache.get("apiresult")
    if apiresult is None:
      radars = db.GqlQuery("select * from Radar order by number desc").fetch(1000)
      response = {"result":
                  [{"title":r.title, 
                    "number":r.number, 
                    "user":r.username(), 
                    "status":r.status, 
                    "description":r.description,
                    "resolved":r.resolved,
                    "product":r.product,
                    "classification":r.classification,
                    "reproducible":r.reproducible,
                    "product_version":r.product_version,
                    "originated":r.originated}
                   for r in radars]}
      apiresult = simplejson.dumps(response)
      memcache.add("apiresult", apiresult, 600) # ten minutes, but we also invalidate on edits and adds
    self.respondWithText(apiresult)

class APIAddRadarAction(Handler):
  def post(self):
    user = users.GetCurrentUser()
    if (not user):
      self.respondWithDictionaryAsJSON({"error":"you must authenticate to add radars"})
    else:
      title = self.request.get("title")
      number = self.request.get("number")
      status = self.request.get("status")
      description = self.request.get("description")
      product = self.request.get("product")
      classification = self.request.get("classification")
      reproducible = int(self.request.get("reproducible"))
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

class APISecretAction(Handler):
  def get(self):
    name = self.request.get("name")
    value = self.request.get("value")
    secret = Secret(name=name, value=value)
    secret.put()
    self.respondWithDictionaryAsJSON({"name":name, "value":value})


class CommentsAJAXForm(Handler):
  def get(self):
    user = users.GetCurrentUser()
    if (not user):
      self.error(500)
      self.respondWithText("You must login to post a comment")
      return
    
    radarKey = self.request.get("radar")
    radar = Radar.get(radarKey)
    
    if(not radar):
      self.error(500)
      self.respondWithText("Unknown radar key")
      return
      
    args = {"radar": radar}
    
    commentKey = self.request.get("is_reply_to")
    if(commentKey):
      post = Comment.get(commentKey)
      if(not post):
        self.error(500)
        self.respondWithText("Can't reply; there is no such post.")
        return
      args["is_reply_to"] = post
    
    
    self.respondWithText(Comment(**args).form())
    
    
  def post(self):
    pass



def main():
  application = webapp.WSGIApplication([
    ('/', IndexAction),
    ('/faq', FAQAction),
    ('/radar', RadarViewByIdAction),
    ('/rdar', RadarViewByNumberAction),
    ('/myradars', RadarListAction),
    ('/myradars/add', RadarAddAction),
    ('/myradars/edit', RadarEditAction),
    ('/myradars/delete', RadarDeleteAction),
    ('/hello', HelloAction),
    ('/api/test', APITestAction),
    ('/api/radars', APIRadarsAction),
    ('/api/radars/add', APIAddRadarAction),
    ('/comment', CommentsAJAXForm),
    # intentially disabled 
    # ('/api/secret', APISecretAction),
    ('.*', NotFoundAction)
  ], debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
