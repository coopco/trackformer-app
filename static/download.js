window.onload = () => {
  $('.progress').each((i, obj) => {
    name = obj.id.split('_')[1];
    update_progress(name);
  });

  $("#select-all").click(() => {
    $('.select').prop("checked", true);
  });

  $("#download-selected").click(() => {
    // Get names of all selected tasks
    names = []
    $('.download').each((i, obj) => {
      name = obj.id.split('_')[1];
      if ($('#select_' + name).is(':checked')) {
        names.push(name)
      }
    });

    // Make request to zip all
    // Download
  });

  //$("#cancel-selected").click(() => {
  //  $('.cancel').each((i, obj) => {
  //    name = obj.id.split('_')[1];
  //    if ($('#select_' + name).is(':checked')) {
  //      $(obj).click();
  //    }
  //  });
  //});

  //$(".cancel").click(() => {
  //  // Get uuid
  //  // Make cancel request
  //  // job.cancel()
  //  // job.delete()
  //  console.log('asd');
  //});

  // When the user clicks on the button, open the modal
    // https://www.w3schools.com/howto/howto_js_copy_clipboard.asp
    // https://www.w3schools.com/howto/howto_css_modals.asp
  $("#share-selected").click(() => {
    $("#myModal").css("display", "block");
    // TODO If no tasks selected
    url = window.location.origin + "/u/" + get_selected_uuids().join("-")
    $("#share-link").val(url);
  });

  // When the user clicks on <span> (x), close the modal
  $(".close").click(() => {
    $("#myModal").css("display", "none");
  })

  // When the user clicks anywhere outside of the modal, close it
  window.onclick = (e) => {
    if (e.target == document.getElementById("myModal")) {
      $("#myModal").css("display", "none");
    }
  };

  $("#share-link").click(() => {
    $("#share-link").select();
  })
};

function get_selected_uuids() {
  names = []
  $('.select').each((i, obj) => {
    name = obj.id.split('_')[1];
    if ($('#select_' + name).is(':checked')) {
      names.push(name)
    }
  });
  return names
}

async function update_progress(name) {
  // make request
  console.log(name);
  var progress_text = "";
  while (progress_text != "COMPLETE") {
    $.ajax({
        url: "/progress/" + name,
        type: "GET",
        cache: false,
        processData: false,
        contentType: false,
        error: function(data) {
          console.log("progress error", data);
          console.log(data.getAllResponseHeaders());
        },
        success: function(data) {
          progress_text = data;
          $("#progress_"+name).text(data)
        }
    });
    await new Promise(r => setTimeout(r, 500))
  }
  //$("#link").css("visibility", "visible");
  //$("#download").attr("href", "/uploads/" + name);
};

async function cancel_task(name) {
  // make request
}
