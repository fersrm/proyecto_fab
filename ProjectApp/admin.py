from django.contrib import admin
from ReportsApp.models import ProjectExtension


# Register your models here.
class ProjectExtensionAdmin(admin.ModelAdmin):
    list_display = ("nna_FK",)


admin.site.register(ProjectExtension, ProjectExtensionAdmin)
