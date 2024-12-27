from django.db.models import Sum
from ReportsApp.models import (
    Notification,
    NNA,
    ProjectExtension,
    Project,
    EntryDetails,
    OnlyProjectExtension,
)
from ListaEsperaApp.models import NNAEntrante, PriorityHistory, RankingHistory
from concurrent.futures import ThreadPoolExecutor
from celery import shared_task
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from datetime import date
from django.db import transaction


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
    with ThreadPoolExecutor(max_workers=4) as executor:
        for nna in NNA.objects.all():
            nna_projects = Project.objects.filter(entrydetails__nna_FK=nna).distinct()
            # Ejecutar en paralelo para cada proyecto del NNA
            futures = [
                executor.submit(alertas_nna_proyecto, nna, project)
                for project in nna_projects
            ]
            for future in futures:
                future.result()


@shared_task
def desactivar_proyectos():
    projects = Project.objects.all()

    for project in projects:
        # Sumar extensiones aprobadas
        total_extension = (
            OnlyProjectExtension.objects.filter(project_FK=project, approved=True)
            .aggregate(total_extension=Sum("extension"))
            .get("total_extension")
            or 0
        )

        # Calcular duración total del proyecto
        total_duration = project.duration + total_extension

        # Calcular la fecha final real del proyecto usando relativedelta para sumar meses
        fecha_final_proyecto = project.date_project + relativedelta(
            months=total_duration
        )

        # Imprimir para depuración
        print(f"fecha_final_proyecto {fecha_final_proyecto}")
        print(f"hoy {date.today()}")

        # Desactivar si la fecha final del proyecto es menor que la fecha actual
        if fecha_final_proyecto < date.today():
            project.active = False
        else:
            project.active = True

        # Guardar cambios en el proyecto
        project.save()


@shared_task
def actualizar_rankings_task():
    """Task de Celery para actualizar los rankings de todos los solicitantes agrupados por comuna y tipo de proyecto."""

    solicitantes = NNAEntrante.objects.all().select_related("nna_FK__location_FK")

    grupos = {}
    for solicitante in solicitantes:
        comuna_id = solicitante.nna_FK.location_FK.id
        tipo_proyecto = solicitante.tipo_proyecto

        # Si la clave comuna_id, tipo_proyecto no existe en el diccionario, agregarla
        if (comuna_id, tipo_proyecto) not in grupos:
            grupos[(comuna_id, tipo_proyecto)] = []

        # Agregar el solicitante al grupo correspondiente
        grupos[(comuna_id, tipo_proyecto)].append(solicitante)

    # Para cada grupo, ordenar y actualizar los rankings
    for (comuna_id, tipo_proyecto), solicitantes_grupo in grupos.items():
        # Ordenar los solicitantes por prioridad (más alta primero) y luego por fecha
        solicitantes_grupo = sorted(
            solicitantes_grupo, key=lambda x: (-x.priority, x.date_of_application)
        )

        # Actualizar el ranking de cada solicitante
        for idx, solicitante in enumerate(solicitantes_grupo, start=1):
            if solicitante.ranking != idx:
                with transaction.atomic():
                    RankingHistory.objects.create(
                        nna_entrante=solicitante,
                        previous_ranking=solicitante.ranking,
                        new_ranking=idx,
                        changed_date=timezone.now(),
                    )
            # Actualizar el ranking en el modelo principal
            solicitante.ranking = idx
            solicitante.is_processed_ranking = True
            solicitante.save(update_fields=["ranking", "is_processed_ranking"])

    return "Rankings actualizados para todos los solicitantes por comuna y tipo de proyecto."


@shared_task
def reorganizar_historial_prioridades_task():
    """Reorganiza el historial de prioridades en la base de datos para cada NNAEntrante según el tipo de proyecto."""
    nna_entrantes = NNAEntrante.objects.all()

    for nna in nna_entrantes:
        # Filtrar historiales asociados al NNAEntrante
        history = PriorityHistory.objects.filter(nna_entrante_FK=nna)

        if not history.exists():
            print(f"No hay historial para el NNAEntrante con ID {nna.id}")
            continue

        # Agrupar por tipo de proyecto
        tipos_proyectos = history.values_list("tipo_proyecto", flat=True).distinct()

        for tipo in tipos_proyectos:
            # Filtrar historial por tipo de proyecto
            history_por_tipo = history.filter(tipo_proyecto=tipo)

            # Crear un set con todas las fechas y prioridades
            fechas_prioridades = set()
            for record in history_por_tipo:
                fechas_prioridades.add((record.old_date, record.old_priority))
                fechas_prioridades.add((record.changed_date, record.new_priority))

            # Ordenar por fecha
            fechas_prioridades_ordenadas = sorted(
                fechas_prioridades, key=lambda x: x[0]
            )

            if fechas_prioridades_ordenadas:
                # Obtener el último registro
                last_date, last_priority = fechas_prioridades_ordenadas[-1]

                # Actualizar NNAEntrante con los últimos datos
                nna.date_of_application = last_date
                nna.priority = last_priority
                nna.save()

            # Eliminar el historial actual para este tipo de proyecto
            history_por_tipo.delete()

            # Reorganizar los datos y guardarlos en la tabla
            print(
                f"Actualizando la tabla PriorityHistory para el tipo de proyecto: {tipo}..."
            )
            for i in range(len(fechas_prioridades_ordenadas) - 1):
                old_date, old_priority = fechas_prioridades_ordenadas[i]
                changed_date, new_priority = fechas_prioridades_ordenadas[i + 1]

                PriorityHistory.objects.create(
                    nna_entrante_FK=nna,
                    tipo_proyecto=tipo,
                    old_date=old_date,
                    old_priority=old_priority,
                    changed_date=changed_date,
                    new_priority=new_priority,
                )

                print(
                    f"Guardado para tipo proyecto '{tipo}': {old_date} ({old_priority}) -> {changed_date} ({new_priority})"
                )

    print("Reorganización completa.")
