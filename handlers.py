import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required


from models import *
import datetime
import os
import simplejson

class Handler(webapp.RequestHandler):

  def respondWithDictionaryAsJSON(self, d):
    self.response.out.write(simplejson.dumps(d) + "\n")
      
  def respondWithText(self, text):
    self.response.out.write(text)
    self.response.out.write("\n")
    
  """Supplies a common template generation function.
  When you call generate(), we augment the template variables supplied with
  the current user in the 'user' variable and the current webapp request
  in the 'request' variable.
  """
  def respondWithTemplate(self, template_name, template_values={}):
    values = {
      'request': self.request,
      'debug': self.request.get('debug'),
      'application_name': 'Open Radar',
      'user': users.GetCurrentUser(),
      'login_url': users.CreateLoginURL(self.request.uri),
      'logout_url': users.CreateLogoutURL('http://' + self.request.host + '/'),
    }
    values.update(template_values)
    directory = os.path.dirname(__file__)
    path = os.path.join(directory, os.path.join('templates', template_name))
    self.response.out.write(template.render(path, values))
    
