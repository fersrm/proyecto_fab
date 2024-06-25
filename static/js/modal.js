function abrir_modal(url, formId) {
  fetch(url)
    .then((response) => response.text())
    .then((data) => {
      const cleanData = DOMPurify.sanitize(data);
      document.getElementById("modalBody").innerHTML = cleanData;
      initializeForm(formId);
      document.getElementById("containerModal").style.display = "block";
    })
    .catch((error) => console.error("Error loading modal content:", error));
}

function abrir_modal_documento(url) {
  abrir_modal(url, "id_document");
}

function abrir_modal_pdf(url) {
  abrir_modal(url, "id_pdf");
}
