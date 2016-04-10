#!/usr/bin/env python
import os, datetime, re, simplejson
import urllib, base64, uuid

import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api.urlfetch import *
from google.appengine.api import memcache
from google.appengine.api import *

import openradar.api
import openradar.db
from openradar.models import *
from openradar.handlers import *

class IndexAction(Handler):
  def get(self):
    self.redirect("/page/1")
    
class OldIndexAction(Handler):
  def get(self):      
    biglist = memcache.get("biglist")
    if biglist is None:
      radars = db.GqlQuery("select * from Radar order by number_intvalue desc").fetch(100)
      path = os.path.join(os.path.dirname(__file__), os.path.join('templates', 'biglist.html'))
      biglist = template.render(path, {'radars':radars})
      memcache.add("biglist", biglist, 3600) # one hour, but we also invalidate on edits and adds
    self.respondWithTemplate('index.html', {"biglist": biglist})

PAGESIZE = 40
PAGE_PATTERN = re.compile("/page/([0-9]+)")

class RadarListByPageAction(Handler):
  def get(self):  
    m = PAGE_PATTERN.match(self.request.path)
    if m:
      number = m.group(1)
      if (int(number) > 500):
        self.error(404)
        self.respondWithText('Not found')
        return 
      if (int(number) > 1):
        showprev = int(number)-1
      else: 
        showprev = None
      shownext = int(number)+1
      pagename = "page" + number
      biglist = memcache.get(pagename)
      if biglist is None:
        radars = db.GqlQuery("select * from Radar order by number_intvalue desc").fetch(PAGESIZE,(int(number)-1)*PAGESIZE)
        if len(radars) > 0:
          path = os.path.join(os.path.dirname(__file__), os.path.join('templates', 'biglist.html'))
          biglist = template.render(path, {'radars':radars})
          memcache.add(pagename, biglist, 3600) # one hour, but we also invalidate on edits and adds
        else:
          biglist = "<p>That's all.</p>"
      self.respondWithTemplate('page.html', {'pagenumber':number, 'shownext':shownext, 'showprev':showprev, "biglist": biglist})
    else:
      self.respondWithText('invalid page request')

class FAQAction(Handler):
  def get(self):    
    self.respondWithTemplate('faq.html', {})

class RadarAddAction(Handler):
  def get(self):    
    user = self.GetCurrentUser()
    if (not user):
      self.respondWithTemplate('please-sign-in.html', {'action': 'add Radars'})
    else:
      self.respondWithTemplate('radar-add.html', {})
  def post(self):
    user = self.GetCurrentUser()
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
                    number_intvalue=int(number),
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
        #tweet = ("[rdar://%s] %s: %s" % (number, radar.username(), title))
        tweet = ("http://openradar.me/%s %s: %s" % (number, radar.username(), title))
        tweet = tweet[0:140]
        secrets = db.GqlQuery("select * from Secret where name = :1", "retweet").fetch(1)
        if len(secrets) > 0:
          secret = secrets[0].value
          form_fields = {
            "message": tweet,
            "secret": secret
          }
          form_data = urllib.urlencode(form_fields)
          try:
            result = fetch("http://sulfur.neontology.com/retweet.php", payload=form_data, method=POST)
          except Exception:
            None # let's not worry about downstream problems
      self.redirect("/myradars")

RADAR_PATTERN = re.compile("/([0-9]+)")
class RadarViewByPathAction(Handler):
  def get(self):    
    user = users.GetCurrentUser()
    if not user:
        page = memcache.get(self.request.path)
        if page:
            self.respondWithText(page)
            return
    m = RADAR_PATTERN.match(self.request.path)
    if m:
      bare = self.request.get("bare")
      number = m.group(1) 
      radars = Radar.gql("WHERE number = :1", number).fetch(1)
      if len(radars) != 1:
        self.respondWithTemplate('radar-missing.html', {"number":number})
        return
      radar = radars[0]
      if (not radar):
        self.respondWithTemplate('radar-missing.html', {"number":number})
      else:	
        path = os.path.join(os.path.dirname(__file__), os.path.join('templates', 'radar-view.html'))        
        page = template.render(path, {"mine":(user == radar.user), "radar":radar, "radars":radar.children(), "comments": radar.comments(), "bare":bare})
        if not user:	    
            memcache.add(self.request.path, page, 3600) # one hour, but we also invalidate on edits and adds
        self.respondWithText(page)
      return

class RadarViewByIdOrNumberAction(Handler):
  def get(self):
    user = users.GetCurrentUser()
    # we keep request-by-id in case there are problems with the radar number (accidental duplicates, for example)
    id = self.request.get("id")
    if id:
      radar = Radar.get_by_id(int(id))
      if (not radar):
        self.respondWithText('Invalid Radar id')
      else:
        self.respondWithTemplate('radar-view.html', {"mine":(user == radar.user), "radar":radar, "radars":radar.children(), "comments": radar.comments()})
      return
    number = self.request.get("number")
    if number:
      self.redirect("/"+number)
      return
    else:
      self.respondWithText('Please specify a Radar by number or openradar id')
    
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
        radar.number_intvalue = int(self.request.get("number"))
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
  
class RadarFixNumberAction(Handler): 
  def post(self):
    id = self.request.get("id")
    radar = Radar.get_by_id(int(id))
    if not radar:
      self.respondWithText('Invalid Radar id')
    else:
      radar.number_intvalue = int(radar.number)      
      radar.put()
      memcache.flush_all()
      self.respondWithText('OK')
     
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
      radars = db.GqlQuery("select * from Radar where user = :1 order by number_intvalue desc", user).fetch(1000)
      self.respondWithTemplate('radar-list.html', {"radars": radars})

class NotFoundAction(Handler):
  def get(self):
    self.response.out.write("<h1>Resource not found</h1>")
    self.response.out.write("<pre>")
    self.response.out.write(str(self.request))
    self.response.out.write("</pre>")

class RefreshAction(Handler):
  def get(self):
    memcache.flush_all()
    self.redirect("/")

class HelloAction(Handler):
  def get(self):
    user = users.get_current_user()
    if not user:
      # The user is not signed in.
      print "Hello"
    else:
      print "Hello, %s!" % user.nickname()

class APIKeyAction(Handler):
  def get(self):    
    user = users.GetCurrentUser()
    if (not user):
      self.respondWithTemplate('please-sign-in.html', {'action': 'view or regenerate your API key'})
    else:
      apikey = openradar.db.APIKey().fetchByUser(user)
      if not apikey:
        apikey = APIKey(user=user,
                        apikey=str(uuid.uuid1()),
                        created=datetime.datetime.now())
        apikey.put()
      self.respondWithTemplate('api-key.html', {'apikey': apikey})
  def post(self):
    user = users.GetCurrentUser()
    if (not user):
      self.respondWithTemplate('please-sign-in.html', {'action': 'regenerate your API key'})
    else:
      apikey = openradar.db.APIKey().fetchByUser(user)
      if apikey:
        apikey.delete()      
      self.redirect("/apikey")
      
    
class APIRadarsAction(Handler):
  def get(self):
    page = self.request.get("page")
    if page:
      page = int(page)
    else:
      page = 1
    count = self.request.get("count")
    if count:
      count = int(count)
    else:
      count = 100
    apiresult = memcache.get("apiresult")
    if apiresult is None:
      radars = db.GqlQuery("select * from Radar order by number_intvalue desc").fetch(count,(page-1)*count)
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

class APICommentsAction(Handler):
  def get(self):
    page = self.request.get("page")
    if page:
      page = int(page)
    else:
      page = 1
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
    
class APIRadarsNumbersAction(Handler):
  def get(self):
    page = self.request.get("page")
    if page:
      page = int(page)
    else:
      page = 1
    apiresult = memcache.get("apiresult")
    if apiresult is None:
      radars = db.GqlQuery("select * from Radar order by number_intvalue desc").fetch(100,(page-1)*100)
      response = {"result":[r.number for r in radars]}
      apiresult = simplejson.dumps(response)
    self.respondWithText(apiresult)
      
class APIRadarsIDsAction(Handler):
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
      
class APIAddRadarAction(Handler):
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
                    number_intvalue=int(number),
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


class CommentsAJAXFormAction(Handler):
  def _check(self):
    user = users.GetCurrentUser()
    if (not user):
      self.error(401)
      self.respondWithText("You must login to post a comment")
      return False, False, False
    
    radarKey = self.request.get("radar")
    radar = Radar.get(radarKey)
    
    if(not radar):
      self.error(400)
      self.respondWithText("Unknown radar key")
      return False, False, False
      
    
    replyKey = self.request.get("is_reply_to")
    replyTo = None
    if(replyKey):
      replyTo = Comment.get(replyKey)
    
    return user, radar, replyTo
    
  def get(self):
    
    # Edit
    commentKey = self.request.get("key")
    if(commentKey):
      comment = Comment.get(commentKey)
      if(not comment):
        self.error(400)
        self.respondWithText("Tried to edit a post that doesn't exist? Couldn't find post to edit.")
        return
      self.respondWithText(comment.form())
      return
      
    # New or reply
    user, radar, replyTo = self._check()
    if(not user): return
    
    args = {"radar": radar}
    
    if(replyTo):
      args["is_reply_to"] = replyTo
    
    self.respondWithText(Comment(**args).form())
    
    
  def post(self):
    user, radar, replyTo = self._check()
    if(not user): return
    
    commentKey = self.request.get("key")
    comment = None
    if(commentKey):
      comment = Comment.get(commentKey)
      if(not comment):
        self.error(400)
        self.respondWithText("Tried to edit a post that doesn't exist? Couldn't find post to edit.")
        return
    else:
      comment = Comment(user = user, radar = radar)
    
    if(not self.request.get("cancel")):
      comment.is_reply_to = replyTo
      comment.subject = self.request.get("subject")
      comment.body = self.request.get("body")
    comment.put()

    self.respondWithText(comment.draw(commentKey != ""))
    
class CommentsAJAXRemoveAction(Handler):
  def post(self):
    user = users.GetCurrentUser()
    if (not user):
      self.error(401)
      self.respondWithText("You must login to remove a comment")
      return
    
    commentKey = self.request.get("key")
    comment = Comment.get(commentKey)
    if(not comment):
      self.error(400)
      self.respondWithText("Tried to remove a post that doesn't exist? Couldn't find post to remove.")
      return
    
    if(not comment.editable_by_current_user()):
      self.error(401)
      self.respondWithText("You must be the comment's owner, or an admin, to remove this comment.")
      return
    
    if(comment.deleteOrBlank() == "blanked"):
      self.respondWithText(comment.html_body())
    else:
      self.respondWithText("REMOVED")
    
class CommentsRecentAction(Handler):
  def get(self):
    comments = db.GqlQuery("select * from Comment order by posted_at desc").fetch(20)
    self.respondWithTemplate('comments-recent.html', {"comments": comments})

class RadarsByUserAction(Handler):
  def get(self):
    username = self.request.get("user")
    user = users.User(username)
    searchlist = ""
    if user:
      query = db.GqlQuery("select * from Radar where user = :1 order by number_intvalue desc", user)
      radars = query.fetch(100)
      if len(radars) > 0:
        path = os.path.join(os.path.dirname(__file__), os.path.join('templates', 'biglist.html'))
        searchlist = template.render(path, {'radars':radars})
      self.respondWithTemplate('byuser.html', {"radarlist": searchlist})
    else:
      self.respondWithText('unknown user')

class SearchAction(Handler):
  def get(self):
    querystring = self.request.get("query")
    keywords = querystring.split(" ")
    keyword = keywords[0]
    searchlist = ""
    try:
      query = Radar.all().search(keyword).order("-number")
      radars = query.fetch(100)
    except Exception:
      self.respondWithTemplate('search.html', {"query":keyword, "searchlist":searchlist})
      return
    if len(radars) > 0:
      path = os.path.join(os.path.dirname(__file__), os.path.join('templates', 'biglist.html'))
      searchlist = template.render(path, {'radars':radars})
    self.respondWithTemplate('search.html', {"query":keyword, "searchlist": searchlist})

class RePutAction(Handler):
  def get(self):
    offset = self.request.get("offset")
    if offset:
      offset = int(offset)
    else:
      offset = 0
    radars = Radar.all().fetch(50,offset)
    for radar in radars:
      radar.put()
    self.respondWithText("done")

class LoginAction(webapp.RequestHandler):
  def get(self):
    self.response.out.write(users.create_login_url("/"))

class APIRecentRadarsAction(Handler):
  def get(self):
    user = self.GetCurrentUser()
    if (not user):
      self.respondWithDictionaryAsJSON({"error":"please authenticate by setting the Authorization header to your API key"})
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

class APIRecentCommentsAction(Handler):
  def get(self):
    user = self.GetCurrentUser()
    if (not user):
      self.respondWithDictionaryAsJSON({"error":"please authenticate by setting the Authorization header to your API key"})
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
    
def main():
  application = webapp.WSGIApplication([
    ('/', IndexAction),
    ('/[0-9]+', RadarViewByPathAction),
    ('/api/comment', openradar.api.Comment),
    ('/api/comment/count', openradar.api.CommentCount),
    ('/api/comments', APICommentsAction),
    ('/api/radar', openradar.api.Radar),
    ('/api/radar/count', openradar.api.RadarCount),
    ('/api/radars', APIRadarsAction),
    ('/api/radars/add', APIAddRadarAction),
    ('/api/radars/numbers', APIRadarsNumbersAction),
    ('/api/radars/ids', APIRadarsIDsAction),
    ('/api/search', openradar.api.Search),
    ('/api/test', openradar.api.Test),
    ('/api/test_authentication', openradar.api.TestAuthentication),
    ('/api/radars/recent', APIRecentRadarsAction),
    ('/api/comments/recent', APIRecentCommentsAction),
    ('/comment', CommentsAJAXFormAction),
    ('/comment/remove', CommentsAJAXRemoveAction),
    ('/comments', CommentsRecentAction),
    ('/faq', FAQAction),
    ('/hello', HelloAction),
    ('/loginurl', LoginAction),
    ('/myradars', RadarListAction),
    ('/myradars/add', RadarAddAction),
    ('/myradars/edit', RadarEditAction),
    ('/myradars/delete', RadarDeleteAction),
    ('/page/[0-9]+', RadarListByPageAction),
    ('/radar', RadarViewByIdOrNumberAction),
    ('/radarsby', RadarsByUserAction),
    ('/rdar', RadarViewByIdOrNumberAction),
    ('/refresh', RefreshAction),
    ('/search', SearchAction),
    ('/fixnumber', RadarFixNumberAction),
    ('/apikey', APIKeyAction),
    # intentially disabled 
    # ('/api/secret', APISecretAction),
    # ('/reput', RePutAction),
    ('.*', NotFoundAction)
  ], debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
