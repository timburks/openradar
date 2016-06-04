package openradar

import (
	"errors"
	"fmt"
	"html/template"
	"strconv"
	"time"
)

func ajaxCommentGetHandler(p *PageRequest) (err error) {
	// GET returns a form for creating a new comment or for editing an existing one
	var comment *Comment
	var commentNumber int64
	commentId := p.r.FormValue("comment_id")
	if commentId != "" {
		// if a comment_id was specified, we are editing a comment so look it up
		commentNumber, err = strconv.ParseInt(commentId, 10, 64)
		comment, err = getComment(p.c, p.u.Email, commentNumber)
	} else {
		// if we are creating a comment, create a new one with the specified radar number
		comment = &Comment{}
		// get the radar number
		radarNumber, err := strconv.ParseInt(p.r.FormValue("radar_id"), 10, 64)
		if err != nil {
			fmt.Fprintf(p.w, "Invalid Radar Number")
			return err
		}
		comment.RadarNumber = radarNumber
		// if a parent_id was specified, this is a reply
		parentId := p.r.FormValue("parent_id")
		if parentId != "" {
			parentNumber, err := strconv.ParseInt(parentId, 10, 64)
			if err == nil {
				comment.IsReplyTo = parentNumber
			}
		}
	}
	// render a form for the comment we've read or created
	p.Set("Comment", comment)
	p.render = false
	t := template.New("")
	_, err = t.ParseFiles("templates/comment-form.html")
	if err != nil {
		return err
	}
	return t.ExecuteTemplate(p.w, "comment-form", p.m)
}

func ajaxCommentPostHandler(p *PageRequest) (err error) {
	// POST accepts a new or edited comment
	var comment *Comment

	radarNumber, err := strconv.ParseInt(p.r.FormValue("radar_id"), 10, 64)
	if err != nil {
		fmt.Fprintf(p.w, "Invalid Radar Number")
		return err
	}

	isReplyTo := p.r.FormValue("parent_id")
	var parentNumber int64
	if isReplyTo != "" {
		parentNumber, err = strconv.ParseInt(isReplyTo, 10, 64)
	} else {
		parentNumber = 0
	}

	var commentNumber int64
	commentId := p.r.FormValue("comment_id")
	if (commentId != "") && (commentId != "0") {
		commentNumber, err = strconv.ParseInt(commentId, 10, 64)
		comment, err = getComment(p.c, p.u.Email, commentNumber)
		if err != nil {
			return err
		}
	} else {
		comment = &Comment{}
		comment.Created = time.Now()
	}

	// if "cancel" is sent, don't make any changes
	cancel := p.r.FormValue("cancel")
	if cancel == "" {
		comment.UserName = p.u.Email
		comment.Subject = p.r.FormValue("subject")
		comment.Body = p.r.FormValue("body")
		comment.RadarNumber = radarNumber
		comment.IsReplyTo = parentNumber
		comment.Modified = time.Now()
		err = saveComment(p.c, comment)
	}

	comment.IsEditable = true
	comment.AllowReplies = true

	p.Set("Number", comment.Number)
	p.Set("Subject", comment.Subject)
	p.Set("Body", comment.Body)
	p.Set("UserName", comment.UserName)
	p.Set("RadarNumber", comment.RadarNumber)
	p.Set("IsEditable", comment.IsEditable)
	p.Set("IsReplyTo", comment.IsReplyTo)
	p.Set("IsSaved", comment.IsSaved)
	p.Set("Created", comment.Created)
	p.Set("Modified", comment.Modified)
	p.Set("AllowReplies", comment.AllowReplies)

	if err != nil {
		return err
	}

	p.render = false
	err = p.Template("templates/comment.html")
	if err != nil {
		return err
	}
	err = p.t.ExecuteTemplate(p.w, "comment", p.m)

	return err
}

func ajaxCommentHandler(p *PageRequest) (err error) {
	if p.r.Method == "GET" {
		return ajaxCommentGetHandler(p)
	} else if p.r.Method == "POST" {
		return ajaxCommentPostHandler(p)
	} else {
		return err
	}
}

func ajaxCommentRemovePostHandler(p *PageRequest) (err error) {
	p.render = false
	// POST removes a comment
	commentId := p.r.FormValue("comment_id")
	if commentId == "" {
		return errors.New("No Comment Specified")
	}
	commentNumber, err := strconv.ParseInt(commentId, 10, 64)
	if err != nil {
		return errors.New("Invalid Comment Number")
	}
	comment, err := getComment(p.c, p.u.Email, commentNumber)
	if err != nil {
		return err
	}
	if comment.UserName != p.u.Email {
		return errors.New("Only the comment's creator can remove a comment.")
	}
	err = deleteComment(p.c, comment)
	if err == nil {
		// return REMOVED to indicate success
		fmt.Fprintf(p.w, "REMOVED")
	}
	return err
}


func ajaxCommentRemoveHandler(p *PageRequest) (err error) {
	if p.r.Method == "POST" {
		return ajaxCommentRemovePostHandler(p)
	} else {
		return err
	}
}
