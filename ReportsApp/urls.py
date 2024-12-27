from django.urls import path
from ReportsApp import views

urlpatterns = [
    path("", views.ReportNnaFormView.as_view(), name="Reports"),
    path("generar_pdf/<pk>/", views.GeneratePdfNnaView.as_view(), name="GeneratePdf"),
    path("lista/", views.ReportNnaListView.as_view(), name="ReportList"),
    path("graficos/", views.ChartsReportNnaTemplateView.as_view(), name="Charts"),
    path("eliminar/<int:pk>/", views.NnaDeleteView.as_view(), name="NnaDelete"),
    path("editar/<int:pk>/", views.NnaUpdateView.as_view(), name="NnaEdit"),
    path("tabla_fechas/", views.ReportListDateView.as_view(), name="ReportDate"),
]
