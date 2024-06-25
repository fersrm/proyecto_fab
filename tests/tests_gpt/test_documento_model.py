import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from DocumentoApp.models import DocumentPDF
import os
from ReportsApp.views import GeneratePdfNnaView

from django.urls import reverse
from django.test import RequestFactory
from django.contrib.messages import get_messages


from tests.factory import add_middleware, user_factory, create_nna_data


@pytest.mark.django_db
def test_documentpdf_create(user_factory):
    # Crear un usuario de prueba
    user = user_factory("testuser", "12345", position_id=3)

    # Crear un documento PDF simulado
    pdf_file = SimpleUploadedFile(
        "test_pdf.pdf", b"dummy content", content_type="application/pdf"
    )

    # Crear una instancia de DocumentPDF
    document = DocumentPDF.objects.create(pdf=pdf_file, state=True, user_FK=user)

    # Verificar que la instancia se haya creado correctamente
    assert document.pk is not None
    assert document.user_FK == user
    assert document.state is True

    # Verificar la eliminación del archivo asociado al eliminar la instancia
    document.delete()  # Llama al método delete() personalizado
    assert not DocumentPDF.objects.filter(
        pk=document.pk
    ).exists()  # Verificar que la instancia se ha eliminado de la base de datos

    # Verificar que el archivo físico se haya eliminado
    assert not os.path.isfile(
        document.pdf.path
    ), f"El archivo {document.pdf.path} aún existe en el sistema"


@pytest.mark.django_db
def test_documentpdf_str_method():
    user = User.objects.create_user(username="testuser", password="password123")
    document = DocumentPDF.objects.create(
        pdf=SimpleUploadedFile(
            "test_pdf.pdf", b"dummy content", content_type="application/pdf"
        ),
        state=True,
        user_FK=user,
    )

    # Verificar el método __str__
    assert str(document) == user.username


@pytest.mark.django_db
def test_generate_pdf_view(create_nna_data, user_factory):
    user = user_factory("testuser", "12345", position_id=3)
    factory = RequestFactory()
    url = reverse("GeneratePdf", kwargs={"pk": create_nna_data.pk}) + "?info=all"

    request = factory.get(url)
    request.user = user
    add_middleware(request)

    view = GeneratePdfNnaView.as_view()
    response = view(request, pk=create_nna_data.pk)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response.has_header("Content-Disposition")
    assert (
        response["Content-Disposition"]
        == f'attachment; filename="reporte_{create_nna_data.pk}.pdf"'
    )


@pytest.mark.django_db
def test_generate_pdf_view_invalid_info_param(create_nna_data, user_factory):
    user = user_factory("testuser", "12345", position_id=3)
    factory = RequestFactory()
    url = reverse("GeneratePdf", kwargs={"pk": create_nna_data.pk}) + "?info=invalid"

    request = factory.get(url)
    request.user = user
    add_middleware(request)

    view = GeneratePdfNnaView.as_view()
    response = view(request, pk=create_nna_data.pk)

    assert response.status_code == 302

    storage = get_messages(request)
    assert any(message.message == "Parámetro no admitido" for message in storage)


@pytest.mark.django_db
def test_generate_pdf_view_post(create_nna_data, user_factory):
    user = user_factory("testuser", "12345", position_id=3)
    factory = RequestFactory()
    url = reverse("GeneratePdf", kwargs={"pk": create_nna_data.pk})

    request = factory.post(url, {"info": ["personal", "ubicacion"]})
    request.user = user
    add_middleware(request)

    view = GeneratePdfNnaView.as_view()
    response = view(request, pk=create_nna_data.pk)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response.has_header("Content-Disposition")
    assert (
        response["Content-Disposition"]
        == f'attachment; filename="reporte_{create_nna_data.pk}.pdf"'
    )


@pytest.mark.django_db
def test_generate_pdf_view_post_invalid_info_param(create_nna_data, user_factory):
    user = user_factory("testuser", "12345", position_id=3)
    factory = RequestFactory()
    url = reverse("GeneratePdf", kwargs={"pk": create_nna_data.pk})

    request = factory.post(url, {})  # Sin datos de 'info'
    request.user = user
    add_middleware(request)

    view = GeneratePdfNnaView.as_view()
    response = view(request, pk=create_nna_data.pk)

    assert response.status_code == 302

    storage = get_messages(request)
    assert any(message.message == "Tiene que marcar una opción" for message in storage)
