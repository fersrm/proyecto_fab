from django import forms
from .models import NNA, Person


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


class NnaEditForm(forms.ModelForm):
    ATTENTION_CHOICES = [
        (True, "Residencial"),
        (False, "Ambulatoria"),
    ]

    type_of_attention = forms.ChoiceField(
        choices=ATTENTION_CHOICES, widget=forms.RadioSelect, label="Tipo de Atención"
    )

    class Meta:
        model = NNA
        fields = ["type_of_attention", "location_FK"]
        labels = {"location_FK": "Ubicación"}


class PersonEditForm(forms.ModelForm):
    SEX_CHOICES = [
        (True, "Masculino"),
        (False, "Femenino"),
    ]

    sex = forms.ChoiceField(choices=SEX_CHOICES, widget=forms.RadioSelect, label="Sexo")

    class Meta:
        model = Person
        fields = [
            "name",
            "last_name_paternal",
            "last_name_maternal",
            "birthdate",
            "sex",
            "address",
            "nationality",
        ]
        labels = {
            "name": "Nombre",
            "last_name_paternal": "Apellido Paterno",
            "last_name_maternal": "Apellido Materno",
            "birthdate": "Fecha de Nacimiento",
            "address": "Dirección",
            "nationality": "Nacionalidad",
        }
