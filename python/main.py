#!/usr/bin/env python

import wsgiref.handlers
from google.appengine.ext import webapp

import openradar.api
import openradar.web

def main():
  application = webapp.WSGIApplication([
    ('/',			openradar.web.IndexAction),
    ('/[0-9]+',			openradar.web.RadarViewByPathAction),
    ('/api/comment',		openradar.api.Comment),
    ('/api/comment/count',	openradar.api.CommentCount),
    ('/api/comments',		openradar.web.APICommentsAction),
    ('/api/comments/recent',	openradar.web.APIRecentCommentsAction),
    ('/api/radar',		openradar.api.Radar),
    ('/api/radar/count',	openradar.api.RadarCount),
    ('/api/radars',		openradar.web.APIRadarsAction),
    ('/api/radars/add',		openradar.web.APIAddRadarAction),
    ('/api/radars/ids',		openradar.web.APIRadarsIDsAction),
    ('/api/radars/numbers',	openradar.web.APIRadarsNumbersAction),
    ('/api/radars/recent',	openradar.web.APIRecentRadarsAction),
    ('/api/search',		openradar.api.Search),
    ('/api/test',		openradar.api.Test),
    ('/api/test_auth',		openradar.api.TestAuthentication),
    ('/apikey',			openradar.web.APIKeyAction),
    ('/comment',		openradar.web.CommentsAJAXFormAction),
    ('/comment/remove',		openradar.web.CommentsAJAXRemoveAction),
    ('/comments',		openradar.web.CommentsRecentAction),
    ('/faq',			openradar.web.FAQAction),
    ('/hello',			openradar.web.HelloAction),
    ('/loginurl',		openradar.web.LoginAction),
    ('/myradars',		openradar.web.RadarListAction),
    ('/myradars/add',		openradar.web.RadarAddAction),
    ('/myradars/edit',		openradar.web.RadarEditAction),
    ('/myradars/delete',	openradar.web.RadarDeleteAction),
    ('/page/[0-9]+',		openradar.web.RadarListByPageAction),
    ('/radar',			openradar.web.RadarViewByIdOrNumberAction),
    ('/radarsby',		openradar.web.RadarsByUserAction),
    ('/rdar',			openradar.web.RadarViewByIdOrNumberAction),
    ('/refresh',		openradar.web.RefreshAction),
    ('/search',			openradar.web.SearchAction),
    # intentionally disabled
    # ('/api/secret',		openradar.web.APISecretAction),
    # ('/reput',		openradar.web.RePutAction),
    # ('/fixnumber',		openradar.web.RadarFixNumberAction),
    ('.*',			openradar.web.NotFoundAction)
  ], debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
