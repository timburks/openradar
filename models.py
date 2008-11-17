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
    modified = datetime.datetime.now() 
    db.Model.put(self)
