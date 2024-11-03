from django import forms


class ReportForm(forms.Form):
    document = forms.FileField()

    def clean_document(self):
        document = self.cleaned_data["document"]

        if not document.name.endswith((".xlsx",)):
            raise forms.ValidationError("El archivo debe ser de formato Excel (xlsx)")

        max_size = 50 * 1024 * 1024
        if document.size > max_size:
            raise forms.ValidationError(
                "El tamaño del archivo no puede ser mayor a 50 megabytes."
            )

        return document
