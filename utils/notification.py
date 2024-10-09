from django.db.models import Sum
from ReportsApp.models import Notification, NNA, ProjectExtension, Project
from concurrent.futures import ThreadPoolExecutor


def alertas_nna_proyecto(nna, project):
    ALERTA_AMARILLA_MESES = 13
    ALERTA_ROJA_MESES = 18

    # Obtener todas las extensiones aprobadas para el proyecto y el NNA actual
    approved_extensions = ProjectExtension.objects.filter(
        nna_FK=nna, project_FK=project, approved=True
    )
    # Sumar la duración base del proyecto y las extensiones aprobadas
    total_approved_extension_months = (
        approved_extensions.aggregate(Sum("extension"))["extension__sum"] or 0
    )
    total_duration_months = project.duration + total_approved_extension_months

    # Crear o actualizar la notificación según la duración total en meses
    if total_duration_months >= ALERTA_ROJA_MESES:
        # Eliminar notificaciones existentes del mismo tipo
        Notification.objects.filter(
            nna_FK=nna, project_FK=project, alert_type="ROJA"
        ).delete()

        Notification.objects.update_or_create(
            nna_FK=nna,
            project_FK=project,
            alert_type="ROJA",
            defaults={"is_active": True, "total_duration": total_duration_months},
        )
    elif total_duration_months >= ALERTA_AMARILLA_MESES:
        Notification.objects.filter(
            nna_FK=nna, project_FK=project, alert_type="ROJA"
        ).delete()

        Notification.objects.update_or_create(
            nna_FK=nna,
            project_FK=project,
            alert_type="AMARILLA",
            defaults={"is_active": True, "total_duration": total_duration_months},
        )
    else:
        Notification.objects.filter(
            nna_FK=nna, project_FK=project, alert_type__in=["AMARILLA", "ROJA"]
        ).update(is_active=False)


def generar_alertas_nna_proyectos():
    with ThreadPoolExecutor(max_workers=6) as executor:
        for nna in NNA.objects.all():
            nna_projects = Project.objects.filter(entrydetails__nna_FK=nna).distinct()
            # Ejecutar en paralelo para cada proyecto del NNA
            futures = [
                executor.submit(alertas_nna_proyecto, nna, project)
                for project in nna_projects
            ]
            for future in futures:
                future.result()  # Esperar la finalización de cada tarea
