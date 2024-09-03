from django.db import models
from .choices import PERMISOS

# Create your models here.

from django.contrib.auth.models import User
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone
import uuid
import os
from PIL import Image, ImageFile, UnidentifiedImageError

ImageFile.LOAD_TRUNCATED_IMAGES = True


def profile_picture_path(instance, filename):
    random_filename = str(uuid.uuid4())
    extension = os.path.splitext(filename)[1]
    return f"users/{instance.user_FK.username}/{random_filename}{extension}"


# Create your models here.
class Position(models.Model):
    user_position = models.CharField(max_length=45, unique=True)
    permission_code = models.CharField(
        max_length=25, choices=PERMISOS, default="RESTRICTED"
    )

    class Meta:
        db_table = "position"

    def __str__(self):
        return f"{self.user_position}"


class Profile(models.Model):
    last_activity = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(upload_to=profile_picture_path, default="profile.webp")
    user_FK = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    position_FK = models.ForeignKey(
        Position, on_delete=models.SET_NULL, null=True, blank=True
    )

    def save(self, *args, **kwargs):
        update_last_activity = kwargs.pop("update_last_activity", False)

        if update_last_activity:
            self.last_activity = timezone.now()
            kwargs["update_fields"] = ["last_activity"]

        if self.pk:
            self.handle_old_image()

        super(Profile, self).save(*args, **kwargs)

        if self.image and os.path.exists(self.image.path):
            self.resize_image()
            self.crop_image()

    def update_last_activity(self):
        self.save(update_last_activity=True)

    def handle_old_image(self):
        default_image = "profile.webp"
        old_profile = Profile.objects.get(pk=self.pk)
        default_image_path = os.path.join(settings.MEDIA_ROOT, default_image)

        if (
            old_profile.image.path != self.image.path
            and old_profile.image.path != default_image_path
        ):
            default_storage.delete(old_profile.image.path)

    def resize_image(self):
        try:
            with Image.open(self.image.path) as img:
                ancho, alto = img.size
                if alto != 300 or ancho != 300:
                    if ancho > alto:
                        nuevo_alto = 300
                        nuevo_ancho = int((ancho / alto) * nuevo_alto)
                        img = img.resize(
                            (nuevo_ancho, nuevo_alto), Image.Resampling.BILINEAR
                        )
                    elif alto > ancho:
                        nuevo_ancho = 300
                        nuevo_alto = int((alto / ancho) * nuevo_ancho)
                        img = img.resize(
                            (nuevo_ancho, nuevo_alto), Image.Resampling.BILINEAR
                        )
                    else:
                        img.thumbnail((300, 300))
                    img.save(self.image.path)
        except (FileExistsError, UnidentifiedImageError):
            print("Error al Redimensionar la imagen")

    def crop_image(self):
        try:
            with Image.open(self.image.path) as img:
                ancho, alto = img.size
                if alto != 300 or ancho != 300:
                    lado = min(ancho, alto)
                    left = (ancho - lado) / 2
                    top = (alto - lado) / 2
                    right = (ancho + lado) / 2
                    bottom = (alto + lado) / 2
                    img = img.crop((left, top, right, bottom))
                    img.save(self.image.path)
        except (FileExistsError, UnidentifiedImageError):
            print("Erro al Recortar la imagen")

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"
        ordering = ["-id"]

    def __str__(self):
        return self.user_FK.username
