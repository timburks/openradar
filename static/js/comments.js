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

function submitComment(form) {
  var formdata = {
    radar: form.radar.value,
    is_reply_to: form.is_reply_to.value,
    subject: form.subject.value,
    body: form.body.value
  }
  if(form.key)
    formdata['key'] = form.key.value
  
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