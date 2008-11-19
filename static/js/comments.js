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