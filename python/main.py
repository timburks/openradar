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
    ('/api/comments',		openradar.web.APIComments),
    ('/api/comments/recent',	openradar.web.APIRecentComments),
    ('/api/radar',		openradar.api.Radar),
    ('/api/radar/count',	openradar.api.RadarCount),
    ('/api/radars',		openradar.web.APIRadars),
    ('/api/radars/add',		openradar.web.APIAddRadar),
    ('/api/radars/ids',		openradar.web.APIRadarsIDs),
    ('/api/radars/numbers',	openradar.web.APIRadarsNumbers),
    ('/api/radars/recent',	openradar.web.APIRecentRadars),
    ('/api/search',		openradar.api.Search),
    ('/api/test',		openradar.api.Test),
    ('/api/test_auth',		openradar.api.TestAuthentication),
    ('/apikey',			openradar.web.APIKey),
    ('/comment',		openradar.web.CommentsAJAXForm),
    ('/comment/remove',		openradar.web.CommentsAJAXRemove),
    ('/comments',		openradar.web.CommentsRecent),
    ('/faq',			openradar.web.FAQ),
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
    ('/search',			openradar.web.Search),
    # intentionally disabled
    # ('/api/secret',		openradar.web.APISecret),
    # ('/reput',		openradar.web.RePut),
    # ('/fixnumber',		openradar.web.RadarFixNumber),
    ('.*',			openradar.web.NotFound)
  ], debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
