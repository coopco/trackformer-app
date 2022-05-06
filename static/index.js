window.onload = () => {
  $("#uploadbutton").click(() => {
    $("#progress").text("Processing...")
    link = $("#link");
    input = $("#fileinput")[0];
    console.log(input.files);
    if (input.files && input.files[0]) {
      let formData = new FormData();
      formData.append("file", input.files[0]);
      formData.append("plotseq", $("#plotseq").is(":checked"))
      $.ajax({
        url: "/",
        type: "POST",
        data: formData,
        cache: false,
        processData: false,
        contentType: false,
        error: function (data) {
          console.log("upload error", data);
          console.log(data.getAllResponseHeaders());
        },
        success: function (data) {
          update_progress(data);
        },
      });
    }
  });
};

// Code you want to run when processing is finished
async function update_progress(name) {
  $("#progress").text("")
  $("#link").css("visibility", "visible");
  $("#download").attr("href", "/uploads/" + name);
};

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
          $("#progress").text(data)
        }
    });
    await new Promise(r => setTimeout(r, 500))
  }
  $("#link").css("visibility", "visible");
  $("#download").attr("href", "/uploads/" + name);
};
