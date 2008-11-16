from google.appengine.ext import db

class Radar(db.Model):
  number = db.StringProperty()
  title = db.StringProperty()
  status = db.StringProperty()
  user = db.UserProperty()
  description = db.TextProperty()
  created = db.DateTimeProperty()
  modified = db.DateTimeProperty()
  def username(self):
    return self.user.nickname().split("@")[0]

