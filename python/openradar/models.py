from google.appengine.ext import db
from google.appengine.ext import search
import datetime
import markdown

class Secret(db.Model):
    name = db.StringProperty()
    value = db.StringProperty()

class Radar(search.SearchableModel):
    # This first set of properties are user-specified.
    # For flexibility and robustness, we represent them all as strings.
    # The Radar Problem ID (we need an int form of this)
    number = db.StringProperty()
    number_intvalue = db.IntegerProperty()
    
    # The radar number this radar duplicates
    parent_number = db.StringProperty()
    title = db.StringProperty()
    # Radar state
    status = db.StringProperty()
    resolved = db.StringProperty()
    # App Engine user who created this entry
    user = db.UserProperty()
    product = db.StringProperty()
    classification = db.StringProperty()
    reproducible = db.StringProperty()
    product_version = db.StringProperty()
    # problem description plus anything else.
    description = db.TextProperty()
    # when the Radar was filed
    originated = db.StringProperty()
    # when the OpenRadar object was created
    created = db.DateTimeProperty()
    # These remaining properties are managed by the OpenRadar web app.
    # They are automatically set when put() is called.
    # We will add more as needed to allow better performance or to simplify
    # sorting and querying.
    # when the OpenRadar object was last modified
    modified = db.DateTimeProperty()
    
    def username(self):
        return self.user.nickname().split("@")[0]
    
    def put(self):
        self.modified = datetime.datetime.now()
        # Sanitize the data before storing
        self.sanitize()
        return db.Model.put(self)
    
    def comments(self):
        return Comment.gql("WHERE radar = :1 AND is_reply_to = :2 order by posted_at desc", self, None)
    
    def children(self):
        gqlQuery = Radar.gql("WHERE parent_number = :1 ORDER BY number ASC", self.number)
        
        return gqlQuery.fetch(gqlQuery.count())
    
    def parent(self):
        return Radar.gql("WHERE number = :1", self.parent_number).get()
    
    def sanitize(self):
        if (self.classification):
            self.classification = self.classification.strip()
        if (self.description):
            self.description = self.description.strip()
        if (self.number):
            self.number = self.number.strip()
        if (self.originated):
            self.originated = self.originated.strip()
        if (self.product):
            self.product = self.product.strip()
        if (self.product_version):
            self.product_version = self.product_version.strip()
        if (self.resolved):
            self.resolved = self.resolved.strip()
        if (self.reproducible):
            self.reproducible = self.reproducible.strip()
        
        # The most common format for duplicates is "Duplicate/<radar_number>"
        # If that format is found, extract the included radar number and store
        # it in self.parent_number
        if (self.status):
            current_status = self.status.strip()
            status_words = current_status.split("/")
            if (len(status_words) == 2):
                # Trim any leading or trailing whitespace from the status type
                status_type = status_words[0].strip()
                # Determine whether status_type equals "duplicate", ignore
                # case sensitivity
                if (status_type.lower() == "duplicate"):
                    status_type = "Duplicate"
                    parent_radar_number = status_words[1].strip()
                    if (parent_radar_number.isdigit()):
                        self.parent_number = parent_radar_number
                    # Put the components back together
                    current_status = status_type + "/" + parent_radar_number
            # Update self.status with the sanitized status
            self.status = current_status;
        
        if (self.title):
            self.title = self.title.strip()
    
    def toDictionary(self):
        return {
            "id":self.key().id(),
            "title":self.title,
            "number":self.number,
            "user":self.user.email(),
            "status":self.status,
            "description":self.description,
            "resolved":self.resolved,
            "product":self.product,
            "classification":self.classification,
            "reproducible":self.reproducible,
            "product_version":self.product_version,
            "originated":self.originated}
    

md = markdown.Markdown()

class Comment(search.SearchableModel):
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
    
  def username(self):
    return self.user.nickname().split("@")[0]
      
  def radar_exists(self):
    try:
      return self.radar != None 
    except db.Error:
      return False

  def radarnumber(self):
    return self.radar_exists() and self.radar.number or "Deleted"

  def radartitle(self):
    return self.radar_exists() and self.radar.title or "Deleted"

  def replies(self):
    return Comment.gql("WHERE is_reply_to = :1 order by posted_at desc", self)
  
  # I know this is a bad place to put it, but my only other idea is custom django template tags, and I just couldn't get those to work
  def draw(self, onlyInner = False):
    from google.appengine.ext.webapp import template
    import os
    directory = os.path.dirname(__file__)
    path = os.path.join(directory, os.path.join('../templates', "comment.html"))
    
    return template.render(path, {"comment": self, "onlyInner": onlyInner})
  
  def form(self):
    from google.appengine.ext.webapp import template
    import os
    directory = os.path.dirname(__file__)
    path = os.path.join(directory, os.path.join('../templates', "comment-form.html"))
    
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
    
  def toDictionary(self):
    result = {
      "id":self.key().id(),
      "user":self.user.email(), 
      "subject":self.subject,
      "body":self.body,
      "radar":self.radar.number,
    }
    if self.is_reply_to:
        result["is_reply_to"] = self.is_reply_to.key().id()
    return result
    

class Profile(db.Model):
  name = db.StringProperty()            # screen name
  twitter = db.StringProperty()         # twitter id
  user = db.UserProperty()
  radar_count = db.IntegerProperty()
  
class Bump(db.Model):
  radar = db.ReferenceProperty(Radar)   # users can bump radars to raise their profile
  user = db.UserProperty()              # the bumping user
  created = db.DateTimeProperty()	      # when the bump was added

class APIKey(db.Model):
  user = db.UserProperty()
  created = db.DateTimeProperty()
  apikey = db.StringProperty()
