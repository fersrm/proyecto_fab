from django.urls import path
from ProjectApp import views

urlpatterns = [
    path("", views.ProjectLisView.as_view(), name="ProjectList"),
    path("agregar/", views.ProjectCreateView.as_view(), name="ProjectCreate"),
    path("editar/<int:pk>/", views.ProjectUpdateView.as_view(), name="ProjectEdit"),
    path("borrar/<int:pk>/", views.ProjectDeleteView.as_view(), name="ProjectDelete"),
    ##############  Extensiones NNA ###############################
    path(
        "extension/",
        views.ProjectExtensionListView.as_view(),
        name="ProjectExtensionList",
    ),
    path(
        "extension/detalle/<int:pk>/",
        views.ProjectExtensionDetailView.as_view(),
        name="ProjectExtensionDetail",
    ),
    path(
        "nna/<int:nna_pk>/project/<int:project_pk>/extension/agregar/",
        views.ProjectExtensionCreateView.as_view(),
        name="ProjectExtensionCreate",
    ),
    path(
        "extension/editar/<int:pk>/",
        views.ProjectExtensionUpdateView.as_view(),
        name="ProjectExtensionEdit",
    ),
    ##############  Notificaciones ###############################
    path(
        "extension/notificaciones/",
        views.NotificationListView.as_view(),
        name="NotificationList",
    ),
    ##############  Extensiones Proyectos ########################
    path(
        "extension_proyecto/",
        views.OnlyProjectExtensionListView.as_view(),
        name="OnlyProjectExtensionList",
    ),
    path(
        "extension_proyecto/detalle/<int:pk>/",
        views.OnlyProjectExtensionDetailView.as_view(),
        name="OnlyProjectExtensionDetail",
    ),
    path(
        "project/<int:project_pk>/extension_proyecto/agregar/",
        views.OnlyProjectExtensionCreateView.as_view(),
        name="OnlyProjectExtensionCreate",
    ),
    path(
        "extension_proyecto/editar/<int:pk>/",
        views.OnlyProjectExtensionUpdateView.as_view(),
        name="OnlyProjectExtensionEdit",
    ),
]
