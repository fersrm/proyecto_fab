from django import forms
from .models import DocumentPDF


class DocumentPdfCreateForm(forms.ModelForm):
    class Meta:
        model = DocumentPDF
        fields = [
            "pdf",
        ]

    def clean_pdf(self):
        pdf = self.cleaned_data["pdf"]

        if not pdf.name.endswith((".pdf",)):
            raise forms.ValidationError("El archivo debe ser de formato PDF (pdf)")

        max_size = 5 * 1024 * 1024
        if pdf.size > max_size:
            raise forms.ValidationError(
                "El tamaño del archivo no puede ser mayor a 5 megabytes."
            )

        return pdf


class DocumentPdfUpdateForm(forms.ModelForm):
    class Meta:
        model = DocumentPDF
        fields = [
            "state",
        ]
        labels = {"state": "Cambiar Estado"}
