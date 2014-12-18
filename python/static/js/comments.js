jQuery.noConflict()

jQuery(document).ready(function() {
  
  
  jQuery("#newcomment").click(function() {
    jQuery.ajax({
      url: "/comment",
      type: "get",
      data: {radar: jQuery("#radar").text()},
      success: function(commentForm) {
        jQuery(".comments").append(commentForm).children(":last").hide().slideDown()
      },
      error: function(xhr, textStatus, errorThrown) {
        showError(xhr.responseText)
      }
    })
  })
  
  jQuery("#error").click(function() {
    jQuery("#error").slideUp()
  })
  
})

function showError(reason) {
  jQuery("#error").text(reason)
  jQuery("#error").slideDown()
}

function submitComment(form, cancel) {
  var formdata = {
    radar: form.radar.value
  }
  if(form.key) // if it has key, it's already saved, so this is an edit
    formdata['key'] = form.key.value
  
  if(cancel == undefined) {
    formdata['is_reply_to']= form.is_reply_to.value
    formdata['subject']= form.subject.value
    formdata['body']= form.body.value
  } else {
    formdata['cancel']= true
  }
  
  jQuery.ajax({
    url: "/comment",
    type: "post",
    data: formdata,
    success: function(newComment) {
      jQuery(form).slideUp(function() {
        jQuery(form).after(newComment).next().hide().slideDown().end().remove()
      })
    },
    error: function(xhr, ts, error) {
      showError(xhr.responseText)
    }
  })
}

function cancelEdit(somethingInsideTheCommentForm) {
  if(!confirm("Are you sure you want to discard your changes to this comment? You can't undo this."))
    return
  
  var form = jQuery(somethingInsideTheCommentForm).parents("form")[0]
  submitComment(form, true)
}

function replyForm(somethingInsideTheComment) {
  var comment = jQuery(somethingInsideTheComment).parents(".comment")
  var parent_key = comment.children(".keyref")[0].name

  jQuery.ajax({
    url: "/comment",
    type: "get",
    data: {
      radar: jQuery("#radar").text(),
      is_reply_to: parent_key
    },
    success: function(commentForm) {
      comment.parent(".commentWithReplies").children(".indent").append(commentForm).children(":last").hide().slideDown()
    },
    error: function(xhr, textStatus, errorThrown) {
      showError(xhr.responseText)
    }
  }) 
}

function editForm(somethingInsideTheComment) {
  var comment = jQuery(somethingInsideTheComment).parents(".comment")
  var key = comment.children(".keyref")[0].name
  jQuery.ajax({
    url: "/comment",
    type: "get",
    data: { key: key },
    success: function(commentForm) {
      jQuery(comment).slideUp(function() {
        jQuery(comment).after(commentForm).next().hide().slideDown().end().remove()
      })
    },
    error: function(xhr, ts, et) {
      showError(xhr.responseText)
    }
  })
}

function removeComment(somethingInsideTheComment) {
  if(!confirm("Are you sure you want to remove this comment? You can't undo this."))
    return
  
  var comment = jQuery(somethingInsideTheComment).parents(".comment")
  var remove_key = comment.children(".keyref")[0].name
  jQuery.ajax({
    url: "/comment/remove",
    type: "post",
    data: {
      radar: jQuery("#radar").text(),
      key: remove_key
    },
    success: function(removalText) {
      if(removalText.indexOf("REMOVED")==0) {
        comment.parent(".commentWithReplies").slideUp(function() {
          comment.parent(".commentWithReplies").remove()
        })
      }else {
        comment.children("h3").text("(Removed)")
        comment.children(".commentbody").html(removalText)
      }
    },
    error: function(xhr, textStatus, errorThrown) {
      showError(xhr.responseText)
    }
  }) 
  
}

function cancelNew(somethingInsideTheComment) {
  var form = jQuery(somethingInsideTheComment).parents("form")[0]

  var written = form.subject.value + form.body.value

  if(written.length > 0 && !confirm("Are you sure you want to cancel this post? You can't undo this."))
    return
  
  jQuery(form).slideUp(function() { jQuery(form).remove() })
}