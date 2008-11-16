#!/usr/bin/env python
import os, datetime, re, simplejson

import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users

from models import *
from handlers import *

class IndexAction(Handler):
  def get(self):    
    radars = db.GqlQuery("select * from Radar order by number desc").fetch(1000)
    self.respondWithTemplate('index.html', {"radars": radars})

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
      radar = Radar(title=title,
                    number=number,
                    status=status,
                    user=user,
                    description=description,
                    created=datetime.datetime.now(),
                    modified=datetime.datetime.now())
      radar.put()
      self.redirect("/myradars")

class RadarViewAction(Handler):
  def get(self):    
    id = self.request.get("id")
    radar = Radar.get_by_id(int(id))
    if (not radar):
      self.respondWithText('Invalid Radar id')
    else:
      self.respondWithTemplate('radar-view.html', {"radar":radar})

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
        radar.modified = datetime.datetime.now()
        radar.put()
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
    radars = db.GqlQuery("select * from Radar order by number desc").fetch(1000)
    response = {"result":
    		[{"title":r.title, 
                  "number":r.number, 
                  "user":r.username(), 
                  "status":r.status, 
                  "description":r.description} 
                 for r in radars]}
    self.respondWithDictionaryAsJSON(response)

def main():
  application = webapp.WSGIApplication([
    ('/', IndexAction),
    ('/faq', FAQAction),
    ('/radar', RadarViewAction),
    ('/myradars', RadarListAction),
    ('/myradars/add', RadarAddAction),
    ('/myradars/edit', RadarEditAction),
    ('/myradars/delete', RadarDeleteAction),
    ('/hello', HelloAction),
    ('/api/test', APITestAction),
    ('/api/radars', APIRadarsAction),
    ('.*', NotFoundAction)
  ], debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
