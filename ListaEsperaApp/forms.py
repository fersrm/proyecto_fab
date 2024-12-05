from django import forms
from ReportsApp.models import EntryDetails


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


class EntryDetailsForm(forms.ModelForm):
    duration_in_months = forms.ChoiceField(
        choices=[(3, "3 meses"), (6, "6 meses"), (12, "12 meses")],
        label="Duración",
        widget=forms.Select(attrs={"class": "form-control"}),
        required=True,
    )

    class Meta:
        model = EntryDetails
        fields = ["project_FK", "date_of_entry"]
        widgets = {
            "date_of_entry": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "project_FK": "Proyecto",
            "date_of_entry": "Fecha de Inicio",
        }
