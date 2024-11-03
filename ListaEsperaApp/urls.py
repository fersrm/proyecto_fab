from django.urls import path
from ListaEsperaApp import views

urlpatterns = [
    path("", views.ApplicantsFormView.as_view(), name="Applicants"),
    path(
        "lista/", views.SolicitudesPorProyectoListView.as_view(), name="ApplicantsList"
    ),
    path(
        "detalle/<int:nna_id>/",
        views.HistorialSolicitanteDetailView.as_view(),
        name="ApplicantsDetail",
    ),
]
