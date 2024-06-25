function initializeForm(id) {
  const uploadButton = document.getElementById("uploadButton");
  const fileInputDoc = document.getElementById(id);

  uploadButton.addEventListener("click", function () {
    const progress = document.getElementById("progress");
    const progressBar = document.getElementById("progressBar");
    const uploadForm = document.getElementById("uploadForm");
    const spanText = document.getElementById("spanText");
    const xhr = new XMLHttpRequest();
    const formData = new FormData();

    formData.append("document", fileInputDoc.files[0]);
    progress.style.display = "block";
    uploadForm.style.display = "none";

    xhr.open("POST", uploadForm.action, true);

    xhr.upload.onprogress = function (e) {
      if (e.lengthComputable) {
        let percentComplete = (e.loaded / e.total) * 100;
        progressBar.style.width = percentComplete + "%";
        spanText.innerHTML = percentComplete.toFixed(2) + "%";
        if (percentComplete === 100) {
          setTimeout(function () {
            tiempoLoader(progress);
          }, 1500);
        }
      }
    };

    xhr.send(formData);
  });

  function tiempoLoader(progress) {
    progress.style.display = "none";
    const loader = document.getElementById("loader");
    loader.classList.add("loader");
  }

  fileInputDoc.addEventListener("change", function () {
    const fileNameContainer = document.getElementById("file-name-container");
    const file = this.files[0];
    if (file) {
      fileNameContainer.textContent = "Nombre del archivo: " + file.name;
      uploadButton.style.display = "flex";
    } else {
      fileNameContainer.textContent = "";
    }
  });
}
