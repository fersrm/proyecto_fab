import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.test import Client, RequestFactory
from UsuarioApp.models import Profile, Position
from tests.factory import user_factory, create_nna_data


@pytest.mark.django_db
def test_user_list_view(user_factory):
    factory = RequestFactory()
    request = factory.get(reverse("User"))
    user = user_factory("testuser", "12345", position_id=3)
    request.user = user

    client = Client()
    client.force_login(user)

    response = client.get(reverse("User"))

    assert response.status_code == 200
    assert "pages/usuarios/usuarios_lista.html" in [t.name for t in response.templates]
    assert "users" in response.context
    assert "verification_users" in response.context
    assert response.context["placeholder"] == "Buscar por usuario, nombre o apellido "


@pytest.mark.django_db
def test_user_create_view_get(user_factory):
    factory = RequestFactory()
    request = factory.get(reverse("Register"))
    user = user_factory("testuser", "12345", position_id=3)
    request.user = user

    client = Client()
    client.force_login(user)

    response = client.get(reverse("Register"))

    assert response.status_code == 302
    # Handle possible redirection
    redirect_url = response.url
    assert (
        redirect_url != "Home"
    ), "Redirection to login or home page. Ensure user has the correct permissions."


@pytest.mark.django_db
def test_user_creation_view_post():
    # Crear un objeto Position para usar en el formulario de creación de perfil
    position = Position.objects.create(user_position="Admin")
    position_test = Position.objects.create(user_position="test_position")

    # Crear un usuario y perfil inicial para login
    user = User.objects.create_user(
        username="admin",
        password="123qaz***",
    )
    Profile.objects.create(user_FK=user, position_FK=position)

    # Datos para el formulario de creación de usuario
    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password1": "complex_password123",
        "password2": "complex_password123",
    }

    # Datos para el formulario de creación de perfil
    profile_data = {
        "position_FK": position_test.id,
    }

    # Combinando ambos diccionarios de datos
    data = {**user_data, **profile_data}

    # Hacer una solicitud POST a la vista de creación de usuario
    client = Client()
    client.force_login(user)
    response = client.post(reverse("Register"), data)

    assert response.status_code == 302  # Redirección después de la creación exitosa
    assert User.objects.filter(username="testuser").exists()
    assert Profile.objects.filter(user_FK__username="testuser").exists()

    messages = list(response.wsgi_request._messages)
    assert len(messages) == 1
    assert str(messages[0]) == "Usuario creado con Éxito."


@pytest.mark.django_db
def test_profile_update_view_get(user_factory):
    factory = RequestFactory()
    request = factory.get(
        reverse("Profile")
    )  # Ajusta el nombre de la URL según sea necesario
    user = user_factory("testuser", "12345", position_id=3)
    request.user = user

    client = Client()
    client.force_login(user)

    response = client.get(reverse("Profile"))

    assert response.status_code == 200
    assert "pages/perfil/perfil.html" in [t.name for t in response.templates]
    assert "user_form" in response.context
    assert "profile_form" in response.context


@pytest.mark.django_db
def test_profile_update_view_post(user_factory):
    factory = RequestFactory()
    request = factory.post(
        reverse("Profile"),
        {
            "username": "updateduser",
            "first_name": "Updated",
            "last_name": "User",
            "email": "updateduser@example.com",
        },
    )  # Ajusta el nombre de la URL según sea necesario
    user = user_factory("testuser", "12345", position_id=3)
    request.user = user

    client = Client()
    client.force_login(user)

    response = client.post(
        reverse("Profile"),
        {
            "username": "updateduser",
            "first_name": "Updated",
            "last_name": "User",
            "email": "updateduser@example.com",
        },
    )

    assert response.status_code == 302  # Redirect after successful form submission
    user.refresh_from_db()
    assert user.username == "updateduser"
    assert user.first_name == "Updated"
    assert user.last_name == "User"
    assert user.email == "updateduser@example.com"
