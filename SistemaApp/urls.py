from django.urls import path
from SistemaApp import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="Home"),
]
