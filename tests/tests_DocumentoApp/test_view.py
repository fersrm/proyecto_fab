import pytest
from DocumentoApp.models import DocumentPDF
from django.test import RequestFactory
from DocumentoApp.views import (
    DocumentPdfCreateView,
    DocumentPdfListView,
    DocumentPdfDeleteView,
)
from DocumentoApp.forms import DocumentPdfCreateForm
from django.core.files.uploadedfile import SimpleUploadedFile
from tests.factory import add_middleware, user_factory
from django.urls import reverse_lazy

# Successfully uploading a valid PDF file

######  test DocumentPdfCreateVies #######


@pytest.mark.django_db
def test_successfully_uploading_valid_pdf(user_factory):
    # Usa user_factory como una fixture
    user = user_factory("testuser", "12345", position_id=3)

    # Create a mock request
    factory = RequestFactory()
    request = factory.post(
        "/upload/",
        {
            "pdf": SimpleUploadedFile(
                "test.pdf", b"file_content", content_type="application/pdf"
            )
        },
    )
    request.user = user
    add_middleware(request)

    # Initialize the view with the mock request
    view = DocumentPdfCreateView()
    view.request = request

    # Create a form instance with the request data
    form = DocumentPdfCreateForm(request.POST, request.FILES)

    # Check if the form is valid and process it
    assert form.is_valid()
    response = view.form_valid(form)

    # Assert that the document was created and saved
    assert DocumentPDF.objects.filter(user_FK=user).exists()
    assert response.status_code == 302  # Redirect after successful upload


# Attempting to upload a file that is not a PDF
@pytest.mark.django_db
def test_attempting_to_upload_non_pdf_file(user_factory):
    # Create a mock user
    user = user_factory("testuser", "12345", position_id=3)

    # Create a mock request
    factory = RequestFactory()
    request = factory.post(
        "/upload/",
        {
            "pdf": SimpleUploadedFile(
                "test.txt", b"file_content", content_type="text/plain"
            )
        },
    )
    request.user = user
    add_middleware(request)
    # Initialize the view with the mock request
    view = DocumentPdfCreateView()
    view.request = request

    # Create a form instance with the request data
    form = DocumentPdfCreateForm(request.POST, request.FILES)

    # Check if the form is invalid and process it
    assert not form.is_valid()
    response = view.form_invalid(form)

    # Assert that the document was not created and an error message was added
    assert not DocumentPDF.objects.filter(user_FK=user).exists()
    assert "El archivo debe ser de formato PDF (pdf)" in form.errors["pdf"]


###################################################################################
##### test DocumentPdfListView ######


# Authenticated user with position_FK.id != 3 sees all documents
@pytest.mark.django_db
def test_authenticated_user_with_position_not_3_sees_all_documents(
    mocker, rf, user_factory
):
    # Crear un usuario y perfil utilizando los factories
    user = user_factory("testuser", "12345", position_id=2)

    mocker.patch(
        "DocumentoApp.views.DocumentPDF.objects.all", return_value="all_documents"
    )

    # Crear una solicitud GET
    request = rf.get("/fake-url/")
    request.user = user

    # Inicializar la vista con la solicitud
    view = DocumentPdfListView()
    view.request = request

    # Verificar que el queryset devuelto sea 'all_documents'
    assert view.get_queryset() == "all_documents"


# Authenticated user with no profile or position_FK
@pytest.mark.django_db
def test_authenticated_user_with_no_profile_or_position_fk(mocker, rf, user_factory):
    user = user_factory("testuser", "12345", position_id=3)

    mocker.patch(
        "DocumentoApp.views.DocumentPDF.objects.filter",
        return_value="filtered_documents",
    )

    request = rf.get("/fake-url/")
    request.user = user

    view = DocumentPdfListView()
    view.request = request

    assert view.get_queryset() == "filtered_documents"


###################################################################################
##### test DocumentPdfDeleteView ######
@pytest.mark.django_db
def test_delete_documentpdf(mocker, rf, user_factory):
    # Mock the request and user
    user = user_factory("testuser", "12345", position_id=None)
    # Mock the DocumentPDF instance
    document_pdf = mocker.Mock(spec=DocumentPDF)
    document_pdf.delete = mocker.Mock()
    user.has_perm = mocker.Mock(return_value=False)
    mocker.patch.object(DocumentPdfDeleteView, "get_object", return_value=document_pdf)

    request = rf.get("/fake-url/")
    request.user = user
    add_middleware(request)

    # Initialize the view and call the get method
    view = DocumentPdfDeleteView()
    view.request = request
    response = view.get(request)

    # Assertions
    document_pdf.delete.assert_called_once()
    assert response.status_code == 302
    assert response.url == reverse_lazy("PdfList")
