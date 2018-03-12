#!/usr/bin/env python

import wsgiref.handlers
from google.appengine.ext import webapp

import openradar.api
import openradar.web

def main():
  application = webapp.WSGIApplication([
    ('/',			openradar.web.Index),
    ('/[0-9]+',			openradar.web.RadarViewByPath),
    ('/api/comment',		openradar.api.Comment),
    ('/api/comment/count',	openradar.api.CommentCount),
    ('/api/comments',		openradar.api.Comments),
    ('/api/comments/recent',	openradar.api.CommentsRecent),
    ('/api/radar',		openradar.api.Radar),
    ('/api/radar/count',	openradar.api.RadarCount),
    ('/api/radars',		openradar.api.Radars),
    ('/api/radars/add',		openradar.api.RadarsAdd),
    ('/api/radars/ids',		openradar.api.RadarsIDs),
    ('/api/radars/numbers',	openradar.api.RadarsNumbers),
    ('/api/radars/recent',	openradar.api.RadarsRecent),
    #DISABLED ('/api/secret',	openradar.api.Secret),
    ('/api/search',		openradar.api.Search),
    ('/api/test',		openradar.api.Test),
    ('/api/test_auth',		openradar.api.TestAuthentication),
    ('/apikey',			openradar.web.APIKey),
    ('/comment',		openradar.web.CommentsAJAXForm),
    ('/comment/remove',		openradar.web.CommentsAJAXRemove),
    ('/comments',		openradar.web.CommentsRecent),
    ('/faq',			openradar.web.FAQ),
    #DISABLED ('/fixnumber',	openradar.web.RadarFixNumber),
    ('/hello',			openradar.web.Hello),
    ('/loginurl',		openradar.web.Login),
    ('/myradars',		openradar.web.RadarList),
    ('/myradars/add',		openradar.web.RadarAdd),
    ('/myradars/edit',		openradar.web.RadarEdit),
    ('/myradars/delete',	openradar.web.RadarDelete),
    ('/page/[0-9]+',		openradar.web.RadarListByPage),
    ('/radar',			openradar.web.RadarViewByIdOrNumber),
    ('/radarsby',		openradar.web.RadarsByUser),
    ('/rdar',			openradar.web.RadarViewByIdOrNumber),
    ('/refresh',		openradar.web.Refresh),
    #DISABLED ('/reput',	openradar.web.RePut),
    ('/search',			openradar.web.Search),
    ('.*',			openradar.web.NotFound)
  ], debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
