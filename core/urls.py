from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", include("SistemaApp.urls")),
    path("", include("UsuarioApp.urls")),
    path("documento/", include("DocumentoApp.urls")),
    path("reporte/", include("ReportsApp.urls")),
    path("proyectos/", include("ProjectApp.urls")),
    path("solicitantes/", include("ListaEsperaApp.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
