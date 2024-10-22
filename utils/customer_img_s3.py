from io import BytesIO
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PIL import Image, ImageFile, UnidentifiedImageError


ImageFile.LOAD_TRUNCATED_IMAGES = True


def resize_image_s3(image_field, img_size):
    try:
        # Leer el archivo desde el almacenamiento
        with default_storage.open(image_field.name, "rb") as img_file:
            img = Image.open(img_file)
            ancho, alto = img.size

            if alto != img_size or ancho != img_size:
                if ancho > alto:
                    nuevo_alto = img_size
                    nuevo_ancho = int((ancho / alto) * nuevo_alto)
                    img = img.resize(
                        (nuevo_ancho, nuevo_alto), Image.Resampling.BILINEAR
                    )
                elif alto > ancho:
                    nuevo_ancho = img_size
                    nuevo_alto = int((alto / ancho) * nuevo_ancho)
                    img = img.resize(
                        (nuevo_ancho, nuevo_alto), Image.Resampling.BILINEAR
                    )
                else:
                    img.thumbnail((img_size, img_size))

                # Guardar la imagen redimensionada en S3
                img_io = BytesIO()
                img.save(img_io, format=img.format)
                image_field.save(
                    image_field.name, ContentFile(img_io.getvalue()), save=False
                )

    except (FileExistsError, UnidentifiedImageError):
        print("Error al Redimensionar la imagen")


def crop_image_s3(image_field, img_size):
    try:
        # Leer el archivo desde el almacenamiento
        with default_storage.open(image_field.name, "rb") as img_file:
            img = Image.open(img_file)
            ancho, alto = img.size

            if alto != img_size or ancho != img_size:
                lado = min(ancho, alto)
                left = (ancho - lado) / 2
                top = (alto - lado) / 2
                right = (ancho + lado) / 2
                bottom = (alto + lado) / 2
                img = img.crop((left, top, right, bottom))

                # Guardar la imagen recortada en S3
                img_io = BytesIO()
                img.save(img_io, format=img.format)
                image_field.save(
                    image_field.name, ContentFile(img_io.getvalue()), save=False
                )

    except (FileExistsError, UnidentifiedImageError):
        print("Error al Recortar la imagen")


def handle_old_image_s3(modelo, pk, image):
    default_image = "profile.webp"
    old_profile = modelo.objects.get(pk=pk)

    # Verifica si la imagen actual no es la por defecto ni la misma que la nueva
    if (
        old_profile.image
        and old_profile.image.name != image.name
        and old_profile.image.name != default_image
    ):
        # Elimina la imagen anterior del almacenamiento (S3)
        default_storage.delete(old_profile.image.name)
