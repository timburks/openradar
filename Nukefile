
(task "run" is
      (SH "/usr/local/google_appengine/dev_appserver.py ."))

(task "deploy" is
      (SH "/usr/local/google_appengine/appcfg.py update ."))

(task "default" => "run")

(task "backup" is
      (SH "mkdir -pv backup")
      (1 upTo:20 do:
         (do (i)
             (SH "curl http://openradar.appspot.com/api/radars?page=#{i} > backup/radars#{i}.json")))
      (1 upTo:10 do:
         (do (i)
             (SH "curl http://openradar.appspot.com/api/comments?page=#{i} > backup/comments#{i}.json"))))

