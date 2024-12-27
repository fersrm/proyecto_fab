from django import forms
from ReportsApp.models import Project, ProjectExtension, OnlyProjectExtension


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
            "duration": "Duración (En meses)",
            "institution_FK": "Institución",
            "location_FK": "Comuna",
        }

    def clean_duration(self):
        duration = self.cleaned_data.get("duration")
        if duration <= 0:
            raise forms.ValidationError("La duración debe ser mayor a 0.")
        return duration

    def clean_ability(self):
        ability = self.cleaned_data.get("ability")
        if ability <= 0:
            raise forms.ValidationError("La cantidad de cupos debe ser mayor a 0.")
        return ability


class ProjectCreateForm(ProjectBaseForm):
    date_project = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}), label="Fecha de Inicio"
    )

    class Meta(ProjectBaseForm.Meta):
        fields = (
            [
                "code",
                "tipo_proyecto",
            ]
            + ProjectBaseForm.Meta.fields
            + ["date_project"]
        )
        labels = {
            **ProjectBaseForm.Meta.labels,
            "code": "Código",
        }


class ProjectUpdateForm(ProjectBaseForm):
    pass


################################
## Extensiones Proyecto NNA ####
################################


class ProjectExtensionCreateForm(forms.ModelForm):
    class Meta:
        model = ProjectExtension
        fields = ["extension", "reason"]
        widgets = {
            "extension": forms.NumberInput(attrs={"min": 1}),
            "reason": forms.Textarea(
                attrs={
                    "rows": 7,
                }
            ),
        }
        labels = {
            "extension": "Extensión en Meses",
            "reason": "Motivo",
        }


class ProjectExtensionUpdateForm(forms.ModelForm):
    class Meta:
        model = ProjectExtension
        fields = ["reason", "approved"]
        widgets = {
            "reason": forms.Textarea(attrs={"rows": 7, "readonly": "readonly"}),
        }
        labels = {
            "approved": "Aprobado",
            "reason": "Motivo",
        }


#############################
## Extensiones Proyecto  ####
#############################


class OnlyProjectExtensionCreateForm(forms.ModelForm):
    class Meta:
        model = OnlyProjectExtension
        fields = ["extension", "reason"]
        widgets = {
            "extension": forms.NumberInput(attrs={"min": 1}),
            "reason": forms.Textarea(
                attrs={
                    "rows": 7,
                }
            ),
        }
        labels = {
            "extension": "Extensión en Meses",
            "reason": "Motivo",
        }

    def clean_extension(self):
        extension = self.cleaned_data.get("extension")
        if extension <= 0:
            raise forms.ValidationError("La extensión debe ser mayor a 0.")
        return extension


class OnlyProjectExtensionUpdateForm(forms.ModelForm):
    class Meta:
        model = OnlyProjectExtension
        fields = ["reason", "approved"]
        widgets = {
            "reason": forms.Textarea(attrs={"rows": 7, "readonly": "readonly"}),
        }
        labels = {
            "approved": "Aprobado",
            "reason": "Motivo",
        }
