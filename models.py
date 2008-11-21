from google.appengine.ext import db
import datetime

class Secret(db.Model):
  name = db.StringProperty()
  value = db.StringProperty()

class Radar(db.Model):
  # This first set of properties are user-specified. 
  # For flexibility and robustness, we represent them all as strings.
  number = db.StringProperty()		# the Radar Problem ID (we need an int form of this)
  title = db.StringProperty()		 
  status = db.StringProperty()		# Radar state
  resolved = db.StringProperty()
  user = db.UserProperty()		# App Engine user who created this entry
  product = db.StringProperty()		
  classification = db.StringProperty()
  reproducible = db.StringProperty()
  product_version = db.StringProperty()
  description = db.TextProperty()	# problem description plus anything else.
  originated = db.StringProperty()	# when the Radar was filed

  created = db.DateTimeProperty()	# when the OpenRadar object was created
  # These remaining properties are managed by the OpenRadar web app.
  # They are automatically set when put() is called.
  # We will add more as needed to allow better performance or to simplify sorting and querying.
  modified = db.DateTimeProperty()	# when the OpenRadar object was last modified

  def username(self):
    return self.user.nickname().split("@")[0]

  def put(self):
    self.modified = datetime.datetime.now() 
    db.Model.put(self)
    
  def comments(self):
    return Comment.gql("WHERE radar = :1 AND is_reply_to = :2", self, None)

import markdown
md = markdown.Markdown()

class Comment(db.Model):
  user = db.UserProperty() # App Engine user who wrote the comment
  subject = db.StringProperty()
  body = db.TextProperty() # as markdown
  posted_at = db.DateTimeProperty()
  radar = db.ReferenceProperty(Radar)
  is_reply_to = db.SelfReferenceProperty()
  
  def __init__(self, *args, **kwargs):
    super(Comment, self).__init__(*args, **kwargs)
    if(not self.posted_at): self.posted_at = datetime.datetime.now()
    if(not self.body): self.body = ""
    if(not self.subject): self.subject = ""
    
      
  def replies(self):
    return Comment.gql("WHERE is_reply_to = :1", self)
  
  # I know this is a bad place to put it, but my only other idea is custom django template tags, and I just couldn't get those to work
  def draw(self, onlyInner = False):
    from google.appengine.ext.webapp import template
    import os
    directory = os.path.dirname(__file__)
    path = os.path.join(directory, os.path.join('templates', "comment.html"))
    
    return template.render(path, {"comment": self, "onlyInner": onlyInner})
  
  def form(self):
    from google.appengine.ext.webapp import template
    import os
    directory = os.path.dirname(__file__)
    path = os.path.join(directory, os.path.join('templates', "comment-form.html"))
    
    return template.render(path, {"comment": self})
  
  def html_body(self):
    return md.convert(self.body)

  def editable_by_current_user(self):
    from google.appengine.api import users
    user = users.GetCurrentUser()
    return user == self.user or users.is_current_user_admin()
    
  def deleteOrBlank(self):
    if self.replies().count() > 0:
      self.subject = "(Removed)"
      self.body = "*This comment has been removed by its author or a moderator.*"
      self.put()
      return "blanked"
    else:
      self.delete()
      return "deleted"
  