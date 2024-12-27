from django_celery_beat.models import PeriodicTask, CrontabSchedule


schedule, _ = CrontabSchedule.objects.get_or_create(
    minute="0", hour="0"  # Ejecuta a las 12:00 AM
)

PeriodicTask.objects.get_or_create(
    crontab=schedule,
    name="Tarea diaria a medianoche",
    task="utils.tasks.generar_alertas_nna_proyectos",
)
