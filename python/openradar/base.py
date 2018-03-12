"""@package docstring
Provides the base request handler.
"""

import wsgiref.handlers
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required

import openradar.db

import datetime
import os
import simplejson

class RequestHandler(webapp.RequestHandler):

  def respondWithDictionaryAsJSON(self, d):
    self.response.out.write(simplejson.dumps(d) + "\n")
      
  def respondWithText(self, text):
    self.response.out.write(unicode(text))
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
    path = os.path.join(directory, os.path.join('../templates', template_name))
    self.response.out.write(unicode(template.render(path, values)))

  def GetCurrentUser(self):
    if 'Authorization' in self.request.headers: 
        auth = self.request.headers['Authorization']
        if auth:
            apikey = openradar.db.APIKey().fetchByAPIKey(auth)
            if apikey:
                return apikey.user
    return users.GetCurrentUser()

    
