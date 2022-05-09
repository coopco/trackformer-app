window.onload = () => {
  $('.progress').each((i, obj) => {
    name = obj.id.split('_')[1];
    update_progress(name)
  });
};

// Code you want to run when processing is finished
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
