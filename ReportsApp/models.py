from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

# Create your models here.


class Institution(models.Model):
    institution_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.institution_name


class Person(models.Model):
    rut = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    last_name_paternal = models.CharField(max_length=100)
    last_name_maternal = models.CharField(max_length=100)
    birthdate = models.DateField()
    sex = models.BooleanField(default=True)
    address = models.CharField(max_length=100)
    nationality = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} {self.last_name_paternal} {self.last_name_maternal}"


# unique=True a comuna ahora no se puede por la forma del Excel
class Location(models.Model):
    region = models.IntegerField()
    commune = models.CharField(max_length=100)

    def __str__(self):
        return self.commune


class Solicitor(models.Model):
    solicitor_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.solicitor_name


# Calidad Jurídica
class LegalQuality(models.Model):
    name_quality = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name_quality


class Tribunal(models.Model):
    tribunal_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.tribunal_name


# Une lo legal
class Legal(models.Model):
    proceedings = models.CharField(max_length=50, unique=True)
    cause_of_entry = models.CharField(max_length=200)
    legal_quality_FK = models.ForeignKey(LegalQuality, on_delete=models.CASCADE)
    tribunal_FK = models.ForeignKey(Tribunal, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.proceedings


# se une todo
class NNA(models.Model):
    cod_nna = models.IntegerField(unique=True)
    person_FK = models.OneToOneField(Person, on_delete=models.CASCADE)
    location_FK = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    solicitor_FK = models.ForeignKey(Solicitor, on_delete=models.SET_NULL, null=True)
    legal_FK = models.ForeignKey(Legal, on_delete=models.SET_NULL, null=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    user_FK = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return str(self.person_FK.name)

    def delete(self, *args, **kwargs):
        if self.person_FK:
            self.person_FK.delete()
        super().delete(*args, **kwargs)

# Después quitar default datetime.now
class Project(models.Model):
    code = models.IntegerField(unique=True)
    project_name = models.CharField(max_length=100)
    type_of_attention = models.BooleanField(default=True)
    date_project = models.DateField(default=datetime.now)
    ability = models.IntegerField(default=30)
    duration = models.IntegerField(default=12)
    institution_FK = models.ForeignKey(
        Institution, on_delete=models.CASCADE, related_name="projects"
    )
    location_FK = models.ForeignKey(Location, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("institution_FK", "code")

    def __str__(self):
        return self.project_name


class EntryDetails(models.Model):
    date_of_entry = models.DateField()
    date_of_exit = models.DateField(null=True, blank=True)
    current_status = models.BooleanField(default=True)
    nna_FK = models.ForeignKey(NNA, on_delete=models.CASCADE)
    project_FK = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return f"Entro en {self.date_of_entry}"


class ProjectExtension(models.Model):
    extension = models.IntegerField()
    approved = models.BooleanField(default=False)
    date = models.DateField(auto_now_add=True)
    reason = models.TextField(max_length=1000)
    nna_FK = models.ForeignKey(NNA, on_delete=models.CASCADE)
    project_FK = models.ForeignKey(Project, on_delete=models.CASCADE)
    user_FK = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return str(self.nna_FK.cod_nna)


class Notification(models.Model):
    TIPOS_ALERTA = [
        ("AMARILLA", "Amarilla"),
        ("ROJA", "Roja"),
    ]

    alert_type = models.CharField(max_length=10, choices=TIPOS_ALERTA)
    creation_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    total_duration = models.IntegerField()
    nna_FK = models.ForeignKey(
        NNA, on_delete=models.CASCADE, related_name="notificaciones"
    )
    project_FK = models.ForeignKey(Project, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.alert_type} para {self.nna_FK}"


class OnlyProjectExtension(models.Model):
    extension = models.IntegerField(default=6)
    approved = models.BooleanField(default=False)
    date = models.DateField(auto_now_add=True)
    reason = models.TextField(max_length=1000)
    project_FK = models.ForeignKey(Project, on_delete=models.CASCADE)
    user_FK = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return str(self.project_FK.code)
