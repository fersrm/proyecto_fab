from django.db.models import Sum
from ReportsApp.models import Notification, NNA, ProjectExtension, Project, EntryDetails
from concurrent.futures import ThreadPoolExecutor
from celery import shared_task
from django.utils import timezone
from dateutil.relativedelta import relativedelta


def alertas_nna_proyecto(nna, project):
    ALERTA_AMARILLA_MESES = 13
    ALERTA_ROJA_MESES = 18

    # Obtener las extensiones aprobadas para este proyecto y NNA
    approved_extensions = ProjectExtension.objects.filter(
        nna_FK=nna, project_FK=project, approved=True
    )
    total_approved_extension_months = (
        approved_extensions.aggregate(Sum("extension"))["extension__sum"] or 0
    )

    # Obtener los detalles de entrada del NNA en el proyecto
    entry_details = EntryDetails.objects.filter(nna_FK=nna, project_FK=project).first()

    # Si no hay detalles de entrada, no podemos calcular la duración
    if not entry_details:
        return

    # Calcular la duración base en meses del proyecto
    entry_date = entry_details.date_of_entry
    if entry_details.date_of_exit:
        exit_date = entry_details.date_of_exit
        nna_duration = relativedelta(exit_date, entry_date)
    else:
        nna_duration = relativedelta(timezone.now().date(), entry_date)

    time_in_project_months = (nna_duration.years * 12) + nna_duration.months

    # Sumar la duración base del proyecto y las extensiones aprobadas
    total_duration_months = time_in_project_months + total_approved_extension_months

    # Actualizar o crear notificación según el tipo de alerta
    if total_duration_months >= ALERTA_ROJA_MESES:
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


@shared_task
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
                future.result()
