from django.contrib import admin
from .models import (
    NNA,
    Institution,
    Person,
    Location,
    Solicitor,
    LegalQuality,
    Tribunal,
    Project,
)


# Register your models here.
class NNAdmin(admin.ModelAdmin):
    list_display = ("person_FK",)


admin.site.register(NNA, NNAdmin)


class InstitutionAdmin(admin.ModelAdmin):
    list_display = ("institution_name",)


admin.site.register(Institution, InstitutionAdmin)


class PersonAdmin(admin.ModelAdmin):
    list_display = ("name",)


admin.site.register(Person, PersonAdmin)


class LocationAdmin(admin.ModelAdmin):
    list_display = ("commune",)


admin.site.register(Location, LocationAdmin)


class SolicitorAdmin(admin.ModelAdmin):
    list_display = ("solicitor_name",)


admin.site.register(Solicitor, SolicitorAdmin)


class LegalQualityAdmin(admin.ModelAdmin):
    list_display = ("name_quality",)


admin.site.register(LegalQuality, LegalQualityAdmin)


class TribunalAdmin(admin.ModelAdmin):
    list_display = ("tribunal_name",)


admin.site.register(Tribunal, TribunalAdmin)


class ProjectAdmin(admin.ModelAdmin):
    list_display = ("project_name",)


admin.site.register(Project, ProjectAdmin)
