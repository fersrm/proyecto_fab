from django.urls import path
from ProjectApp import views

urlpatterns = [
    path("", views.ProjectLisView.as_view(), name="ProjectList"),
    path("agregar/", views.ProjectCreateView.as_view(), name="ProjectCreate"),
    path("editar/<int:pk>/", views.ProjectUpdateView.as_view(), name="ProjectEdit"),
    path("borrar/<int:pk>/", views.ProjectDeleteView.as_view(), name="ProjectDelete"),
]
