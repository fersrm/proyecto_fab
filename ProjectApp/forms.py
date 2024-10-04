from django import forms
from ReportsApp.models import Project


class ProjectBaseForm(forms.ModelForm):
    ATTENTION_CHOICES = [
        (True, "Residencial"),
        (False, "Ambulatoria"),
    ]

    type_of_attention = forms.ChoiceField(
        choices=ATTENTION_CHOICES, widget=forms.RadioSelect, label="Tipo de Atención"
    )

    class Meta:
        model = Project
        fields = [
            "project_name",
            "type_of_attention",
            "ability",
            "duration",
            "institution_FK",
            "location_FK",
        ]
        labels = {
            "project_name": "Nombre de Proyecto",
            "type_of_attention": "Tipo de Atención",
            "ability": "Capacidad",
            "duration": "Duración",
            "institution_FK": "Institución",
            "location_FK": "Comuna",
        }


class ProjectCreateForm(ProjectBaseForm):
    class Meta(ProjectBaseForm.Meta):
        fields = ["code"] + ProjectBaseForm.Meta.fields + ["date_project"]
        labels = {
            **ProjectBaseForm.Meta.labels,
            "code": "Código",
            "date_project": "Fecha de Proyecto",
        }


class ProjectUpdateForm(ProjectBaseForm):
    pass
