"""@package docstring
Provides the web request handlers.
"""

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
from openradar.base import *
from openradar.models import *

class Index(RequestHandler):
  def get(self):
    self.redirect("/page/1")

class OldIndex(RequestHandler):
  def get(self):
    biglist = memcache.get("biglist")
    if biglist is None:
      radars = db.GqlQuery("select * from Radar order by number_intvalue desc").fetch(100)
      path = os.path.join(os.path.dirname(__file__), os.path.join('../templates', 'biglist.html'))
      biglist = template.render(path, {'radars':radars})
      memcache.add("biglist", biglist, 3600) # one hour, but we also invalidate on edits and adds
    self.respondWithTemplate('index.html', {"biglist": biglist})

PAGESIZE = 40
PAGE_PATTERN = re.compile("/page/([0-9]+)")

class RadarListByPage(RequestHandler):
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
          path = os.path.join(os.path.dirname(__file__), os.path.join('../templates', 'biglist.html'))
          biglist = template.render(path, {'radars':radars})
          memcache.add(pagename, biglist, 3600) # one hour, but we also invalidate on edits and adds
        else:
          biglist = "<p>That's all.</p>"
      self.respondWithTemplate('page.html', {'pagenumber':number, 'shownext':shownext, 'showprev':showprev, "biglist": biglist})
    else:
      self.respondWithText('invalid page request')

class FAQ(RequestHandler):
  def get(self):
    self.respondWithTemplate('faq.html', {})

class RadarAdd(RequestHandler):
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

RADAR_PATTERN = re.compile("/((FB)?[0-9]+)")
class RadarViewByPath(RequestHandler):
  def get(self, _prefix):
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
        path = os.path.join(os.path.dirname(__file__), os.path.join('../templates', 'radar-view.html'))
        page = template.render(path, {"mine":(user == radar.user), "radar":radar, "radars":radar.children(), "comments": radar.comments(), "bare":bare, "user": user})
        if not user:
            memcache.add(self.request.path, page, 3600) # one hour, but we also invalidate on edits and adds
        self.respondWithText(page)
      return

class RadarViewByIdOrNumber(RequestHandler):
  def get(self):
    user = users.GetCurrentUser()
    # we keep request-by-id in case there are problems with the radar number (accidental duplicates, for example)
    id = self.request.get("id")
    if id:
      radar = Radar.get_by_id(int(id))
      if (not radar):
        self.respondWithText('Invalid Radar id')
      else:
        self.respondWithTemplate('radar-view.html', {"mine":(user == radar.user), "radar":radar, "radars":radar.children(), "comments": radar.comments(), "user": user})
      return
    number = self.request.get("number")
    if number:
      self.redirect("/"+number)
      return
    else:
      self.respondWithText('Please specify a Radar by number or openradar id')

class RadarEdit(RequestHandler):
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

class RadarFixNumber(RequestHandler):
  def post(self):
    id = self.request.get("id")
    radar = Radar.get_by_id(int(id))
    if not radar:
      self.respondWithText('Invalid Radar id')
    else:
      radar.put()
      memcache.flush_all()
      self.respondWithText('OK')

class RadarDelete(RequestHandler):
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

class RadarList(RequestHandler):
  def get(self):
    user = users.GetCurrentUser()
    if (not user):
      self.respondWithTemplate('please-sign-in.html', {'action': 'view your Radars'})
    else:
      radars = db.GqlQuery("select * from Radar where user = :1 order by number_intvalue desc", user).fetch(1000)
      self.respondWithTemplate('radar-list.html', {"radars": radars})

class NotFound(RequestHandler):
  def get(self):
    self.response.out.write("<h1>Resource not found</h1>")
    self.response.out.write("<pre>")
    self.response.out.write(str(self.request))
    self.response.out.write("</pre>")

class Refresh(RequestHandler):
  def get(self):
    memcache.flush_all()
    self.redirect("/")

class Hello(RequestHandler):
  def get(self):
    user = users.get_current_user()
    if not user:
      # The user is not signed in.
      print "Hello"
    else:
      print "Hello, %s!" % user.nickname()

class APIKey(RequestHandler):
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

class CommentsAJAXForm(RequestHandler):
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

class CommentsAJAXRemove(RequestHandler):
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

class CommentsRecent(RequestHandler):
  def get(self):
    comments = db.GqlQuery("select * from Comment order by posted_at desc").fetch(20)
    self.respondWithTemplate('comments-recent.html', {"comments": comments})

class RadarsByUser(RequestHandler):
  def get(self):
    username = self.request.get("user")
    user = users.User(username)
    searchlist = ""
    if user:
      query = db.GqlQuery("select * from Radar where user = :1 order by number_intvalue desc", user)
      radars = query.fetch(100)
      if len(radars) > 0:
        path = os.path.join(os.path.dirname(__file__), os.path.join('../templates', 'biglist.html'))
        searchlist = template.render(path, {'radars':radars})
      self.respondWithTemplate('byuser.html', {"radarlist": searchlist})
    else:
      self.respondWithText('unknown user')

class Search(RequestHandler):
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
      path = os.path.join(os.path.dirname(__file__), os.path.join('../templates', 'biglist.html'))
      searchlist = template.render(path, {'radars':radars})
    self.respondWithTemplate('search.html', {"query":keyword, "searchlist": searchlist})

class RePut(RequestHandler):
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

class Login(webapp.RequestHandler):
  def get(self):
    self.response.out.write(users.create_login_url("/"))
