from django.db import models
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
import os


class DocumentPDF(models.Model):
    pdf = models.FileField(upload_to="document/")
    state = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    user_FK = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ["-id"]

    def __str__(self):
        return self.user_FK.username

    def delete(self, *args, **kwargs):
        if self.pdf and os.path.isfile(self.pdf.path):
            os.remove(self.pdf.path)
        # Cambiar os.path.isfile a default_storage.exists:
        # y os.remove(self.pdf.path) por default_storage.delete(self.pdf.name)
        # para AWS S3
        super(DocumentPDF, self).delete(*args, **kwargs)
