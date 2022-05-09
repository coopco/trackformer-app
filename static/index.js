window.onload = () => {
  $("#uploadbutton").click(() => {
    $("#link").css("visibility", "visible");
    link = $("#link");
    input = $("#fileinput")[0];
    console.log(input.files);
    for (let i = 0; i < input.files.length; i++) {
      console.log(input.files[i]);
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
          url = $("#download").attr("href")
          url = url + (url.length <= 3 ? '' : '-') + data
          $("#download").attr("href", url);
        },
      });
    }
  });
};

