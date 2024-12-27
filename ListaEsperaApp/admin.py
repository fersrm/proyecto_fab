from django.contrib import admin
from .models import NNAEntrante

# Register your models here.


class NNAEntranteAdmin(admin.ModelAdmin):
    list_display = ("nna_FK",)


admin.site.register(NNAEntrante, NNAEntranteAdmin)
