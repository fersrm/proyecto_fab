from django.contrib import admin
from .models import DocumentPDF


# Register your models here.
class DocumentPdfAdmin(admin.ModelAdmin):
    list_display = ("user_FK", "state", "date")


admin.site.register(DocumentPDF, DocumentPdfAdmin)
