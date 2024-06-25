from django.urls import path
from DocumentoApp import views

urlpatterns = [
    path("lista_pdf/", views.DocumentPdfListView.as_view(), name="PdfList"),
    path("carga_pdf/", views.DocumentPdfCreateView.as_view(), name="PdfAdd"),
    path("eliminar/<int:pk>/", views.DocumentPdfDeleteView.as_view(), name="PdfDelete"),
    path("actualizar/", views.DocumentPdfUpdateView.as_view(), name="PdfEdit"),
]
