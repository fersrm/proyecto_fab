import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.test import Client
from tests.factory import user_factory, create_nna_data


@pytest.mark.django_db
def test_report_nna_list_view_superuser(client, user_factory):
    # Crear un superusuario
    user = user_factory("testuser", "12345", position_id=2)

    # Iniciar sesión como superusuario
    client.force_login(user)

    # Hacer una solicitud GET a la vista de informes
    response = client.get(reverse("Reports"))

    # Verificar el código de estado de la respuesta
    assert response.status_code == 200

    # Verificar que la plantilla correcta se está utilizando
    assert "pages/reportes_nna/carga_excel.html" in [
        template.name for template in response.templates
    ]


@pytest.mark.django_db
def test_report_nna_list_view(client, user_factory):
    # Crear usuarios con diferentes posiciones y correos verificados
    user_with_permission_1 = user_factory("testuser1", "12345", position_id=1)
    user_with_permission_2 = user_factory("testuser2", "12345", position_id=2)
    user_without_permission = user_factory("testuser3", "12345", position_id=3)

    # Caso: Usuario con permisos (Admin)
    client.force_login(user_with_permission_1)
    response = client.get(reverse("Reports"))
    assert response.status_code == 200
    assert "pages/reportes_nna/carga_excel.html" in [
        template.name for template in response.templates
    ]

    # Caso: Usuario con permisos (Manager)
    client.force_login(user_with_permission_2)
    response = client.get(reverse("Reports"))
    assert response.status_code == 200
    assert "pages/reportes_nna/carga_excel.html" in [
        template.name for template in response.templates
    ]

    # Caso: Usuario con permisos (User)
    client.force_login(user_without_permission)
    response = client.get(reverse("Reports"))
    assert response.status_code == 302
    assert "pages/reportes_nna/carga_excel.html" not in [
        template.name for template in response.templates
    ]


@pytest.mark.django_db
def test_report_nna_form_view_get(client, user_factory):
    user = user_factory("testuser", "12345", position_id=3)

    # Iniciar sesión con el usuario
    client.force_login(user)

    # Realizar una solicitud GET a la vista de informes
    response = client.get(reverse("ReportList"))

    # Verificar el código de estado de la respuesta
    assert response.status_code == 200

    # Verificar que la plantilla correcta se está utilizando
    assert "pages/reportes_nna/reporte_lista.html" in [
        t.name for t in response.templates
    ]


@pytest.mark.django_db
def test_something_with_nna_data(create_nna_data):
    nna = create_nna_data
    # Realizar pruebas utilizando el objeto 'nna' creado por la fixture
    assert nna.cod_nna == "123"


@pytest.mark.django_db
def test_user_create_view_post_with_permission(user_factory):
    client = Client()

    user_with_permission_1 = user_factory("testuser1", "12345", position_id=1)
    user_with_permission_2 = user_factory("testuser2", "12345", position_id=2)
    user_without_permission = user_factory("testuser3", "12345", position_id=3)

    # Caso: Usuario con permisos (Admin)
    client.force_login(user_with_permission_1)
    response = client.post(
        reverse("Register"),
        {
            "username": "newuser",
            "position_FK": 3,
            "password1": "complexpassword123",
            "password2": "complexpassword123",
            "first_name": "First",
            "last_name": "Last",
            "email": "newuser@example.com",
        },
    )

    assert response.status_code == 302
    assert User.objects.filter(username="newuser").exists()

    # Caso: Usuario con permisos (Manager)
    client.logout()
    client.force_login(user_with_permission_2)
    response = client.post(
        reverse("Register"),
        {
            "username": "newuser2",
            "position_FK": 3,
            "password1": "complexpassword123",
            "password2": "complexpassword123",
            "first_name": "First",
            "last_name": "Last",
            "email": "newuser2@example.com",
        },
    )

    assert response.status_code == 302
    assert User.objects.filter(username="newuser2").exists()

    # Caso: Usuario sin permisos (User)
    client.logout()
    client.force_login(user_without_permission)
    response = client.post(
        reverse("Register"),
        {
            "username": "newuser3",
            "position_FK": 3,
            "password1": "complexpassword123",
            "password2": "complexpassword123",
            "first_name": "First",
            "last_name": "Last",
            "email": "newuser3@example.com",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("Home")
    assert not User.objects.filter(username="newuser3").exists()
