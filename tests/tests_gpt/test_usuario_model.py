import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image
import tempfile
import os
from UsuarioApp.models import Position, Profile


@pytest.mark.django_db
def test_position_creation():
    position = Position.objects.create(user_position="Developer")
    assert position.user_position == "Developer"
    assert str(position) == "Developer"


@pytest.mark.django_db
def test_profile_creation():
    user = User.objects.create_user(username="testuser", password="12345")
    position = Position.objects.create(user_position="Developer")
    profile = Profile.objects.create(user_FK=user, position_FK=position)

    assert profile.user_FK.username == "testuser"
    assert profile.position_FK.user_position == "Developer"
    assert profile.image.name == "profile.webp"
    assert str(profile) == "testuser"


@pytest.mark.django_db
def test_profile_last_activity_update():
    user = User.objects.create_user(username="testuser", password="12345")
    profile = Profile.objects.create(user_FK=user)

    old_last_activity = profile.last_activity
    profile.update_last_activity()

    assert profile.last_activity != old_last_activity
    assert profile.last_activity <= timezone.now()


@pytest.mark.django_db
def test_profile_image_resizing():
    user = User.objects.create_user(username="testuser", password="12345")

    # Create a temporary image file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
        img = Image.new("RGB", (500, 500), color="red")
        img.save(temp_file, format="JPEG")
        temp_file.seek(0)

        profile = Profile.objects.create(
            user_FK=user,
            image=SimpleUploadedFile(
                name="test_image.jpg",
                content=temp_file.read(),
                content_type="image/jpeg",
            ),
        )

        # Reload the profile to refresh the image path
        profile.refresh_from_db()

        # Ensure the image has been resized
        with Image.open(profile.image.path) as img:
            assert img.size == (300, 300)

    # Clean up the temporary file
    os.remove(profile.image.path)


@pytest.mark.django_db
def test_profile_image_cropping():
    user = User.objects.create_user(username="testuser", password="12345")

    # Create a temporary image file with a different size
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
        img = Image.new("RGB", (400, 600), color="blue")
        img.save(temp_file, format="JPEG")
        temp_file.seek(0)

        profile = Profile.objects.create(
            user_FK=user,
            image=SimpleUploadedFile(
                name="test_image.jpg",
                content=temp_file.read(),
                content_type="image/jpeg",
            ),
        )

        # Reload the profile to refresh the image path
        profile.refresh_from_db()

        # Ensure the image has been resized and cropped
        with Image.open(profile.image.path) as img:
            assert img.size == (300, 300)

    # Clean up the temporary file
    os.remove(profile.image.path)
