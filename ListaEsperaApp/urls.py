from django.urls import path
from ListaEsperaApp import views

urlpatterns = [
    path("", views.ApplicantsFormView.as_view(), name="Applicants"),
    path(
        "lista/<int:region_id>/",
        views.SolicitudesPorProyectoListView.as_view(),
        name="ApplicantsList",
    ),
    path(
        "detalle/<int:nna_id>/",
        views.HistorialSolicitanteDetailView.as_view(),
        name="ApplicantsDetail",
    ),
    path(
        "lista_region/",
        views.SolicitantesPorRegionView.as_view(),
        name="ApplicantsRegionList",
    ),
    path(
        "borrar/<int:pk>/",
        views.SolicitanteDeleteView.as_view(),
        name="SolicitanteDelete",
    ),
]
