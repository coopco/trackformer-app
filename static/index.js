window.onload = () => {
  $("#uploadbutton").click(() => {
    link = $("#link");
    input = $("#fileinput")[0];

    if (input.files.length == 0) {
      // If user clicked upload without choosing any files
      alert('No selected file');
      return;
    }

    $("#download_upload").attr("href", "/u/");

    for (let i = 0; i < input.files.length; i++) {
      let formData = new FormData();
      formData.append("file", input.files[i]);
      formData.append("plotseq", $("#plotseq").is(":checked"))
      formData.append("debug", $("#debug").is(":checked"))
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
          url = $("#download_upload").attr("href")
          url = url + (url.length <= 3 ? '' : '-') + data
          $("#download_upload").attr("href", url);
          if (i >= input.files.length - 1) {
            // TODO upload progress
            console.log('test');
            $("#download_upload").css("visibility", "visible");
          }
        },
      });
    }
  });
};

