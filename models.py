from google.appengine.ext import db

class Secret(db.Model):
  name = db.StringProperty()
  value = db.StringProperty()

class Radar(db.Model):
  number = db.StringProperty()		# the Radar Problem ID (we need an int form of this)
  title = db.StringProperty()		 
  status = db.StringProperty()		# Radar state
  user = db.UserProperty()		# App Engine user who created this entry
  product = db.StringProperty()		
  classification = db.StringProperty()
  reproducible = db.BooleanProperty()
  product_version = db.StringProperty()
  description = db.TextProperty()	# problem description plus anything else.
  originated = db.DateTimeProperty()	# when the Radar was filed
  created = db.DateTimeProperty()	# when the OpenRadar object was created
  modified = db.DateTimeProperty()	# when the OpenRadar object was last modified

  def username(self):
    return self.user.nickname().split("@")[0]

