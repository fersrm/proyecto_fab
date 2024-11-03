from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from ReportsApp.models import NNA
from django.utils import timezone

# Create your models here.

PRIORIDAD_MIN = 10
PRIORIDAD_MAX = 100

TIPOS_PROYECTOS = [
    ("ABUSO", "Abuso"),
    ("RIESGO VITAL", "Riesgo vital"),
]


class NNAEntrante(models.Model):
    nna_FK = models.ForeignKey(NNA, on_delete=models.CASCADE)
    tipo_proyecto = models.CharField(
        max_length=20, choices=TIPOS_PROYECTOS, default="ABUSO"
    )
    date_of_application = models.DateField(default=timezone.now)
    priority = models.IntegerField(
        default=50,
        validators=[MinValueValidator(PRIORIDAD_MIN), MaxValueValidator(PRIORIDAD_MAX)],
    )

    class Meta:
        ordering = [
            "priority",
            "date_of_application",
        ]  # Ordena por prioridad primero, luego por fecha

    def __str__(self):
        return f"NNA: {self.nna_FK.person_FK.name} | Prioridad: {self.priority}"

    def update_priority(self, new_priority, new_date_of_application):
        # Guardamos el cambio en el historial, incluyendo la fecha de aplicación
        PriorityHistory.objects.create(
            nna_entrante_FK=self,
            old_priority=self.priority,
            new_priority=new_priority,
            old_date=self.date_of_application,
            changed_date=new_date_of_application,
            tipo_proyecto=self.tipo_proyecto,
        )
        # Actualizamos la prioridad y la fecha
        self.priority = new_priority
        self.date_of_application = new_date_of_application
        self.save()


class PriorityHistory(models.Model):
    nna_entrante_FK = models.ForeignKey(
        NNAEntrante, on_delete=models.CASCADE, related_name="history"
    )
    old_priority = models.IntegerField(
        validators=[MinValueValidator(PRIORIDAD_MIN), MaxValueValidator(PRIORIDAD_MAX)]
    )
    new_priority = models.IntegerField(
        validators=[MinValueValidator(PRIORIDAD_MIN), MaxValueValidator(PRIORIDAD_MAX)]
    )
    old_date = models.DateTimeField(default=timezone.now)
    changed_date = models.DateTimeField(default=timezone.now)
    tipo_proyecto = models.CharField(max_length=20)
    

    def __str__(self):
        return f"Cambio de prioridad de {self.old_priority} a {self.new_priority} en {self.changed_date}"

    class Meta:
        ordering = ["-changed_date"]  # Ordenar por fecha de cambio, descendente
