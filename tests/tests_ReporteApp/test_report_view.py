import pytest
from django.test import RequestFactory
from ReportsApp.forms import ReportForm
from django.core.files.uploadedfile import SimpleUploadedFile
from tests.factory import add_middleware, user_factory
from ReportsApp.views import ReportNnaFormView
import pandas as pd
from core.mixins import PermitsPositionMixin
from django.contrib import messages

# Successfully uploading a valid PDF file


# Form submission with valid Excel file processes correctly
@pytest.mark.django_db
def test_form_submission_with_valid_excel_file(mocker, user_factory):
    user = user_factory("testuser", "12345", position_id=2)
    factory = RequestFactory()
    request = factory.post(
        "/upload/", {"document": SimpleUploadedFile("example.xlsx", b"")}
    )

    request.user = user
    add_middleware(request)

    # Mocking the form and its validation
    form = mocker.Mock(spec=ReportForm)
    form.cleaned_data = {"document": request.FILES["document"]}
    form.is_valid.return_value = True

    # Mocking pandas read_excel
    mocker.patch(
        "pandas.read_excel",
        return_value=pd.DataFrame(
            {
                "institucion": ["Institution 1"],
                "CodProyecto": [1],
                "proyecto": ["Project 1"],
                "rut": ["12345678-9"],
                "sexo": ["M"],
                "fechanacimiento": ["01/01/2000"],
                "nombres": ["John"],
                "apellido_paterno": ["Doe"],
                "apellido_materno": ["Smith"],
                "DireccionNino": ["123 Street"],
                "Nacionalidad": ["Country"],
                "RegionNino": [1],
                "Comuna": ["Commune 1"],
                "SolicitanteIngreso": ["Solicitor 1"],
                "CalidadJuridica": ["Quality 1"],
                "Tribunal": ["Tribunal 1"],
                "Expediente": ["Proceeding 1"],
                "CausalIngreso_1": ["Cause 1"],
                "TipoAtencion": ["residencial"],
                "codNNA": [1],
                "vigencia": ["si"],
                "fechaingreso": ["01/01/2020"],
                "fechaegreso": [None],
            }
        ),
    )

    # Initialize and invoke the view
    class TestView(ReportNnaFormView):
        mixin = PermitsPositionMixin()

        def dispatch(self, request, *args, **kwargs):
            return super().dispatch(request, *args, **kwargs)

    view = TestView.as_view()
    response = view(request)
    # Assertions
    assert response.status_code == 302
    assert response.url == "/reporte/lista/"

    # view = ReportNnaFormView()
    # view.request = request
    # response = view.form_valid(form)


# Uploads an Excel file with invalid format (not .xlsx)


@pytest.mark.django_db
def test_invalid_file_format(mocker, user_factory):
    # Mock the request and user
    factory = RequestFactory()
    invalid_content = b"dummy content"
    document = SimpleUploadedFile(
        "example_document.txt", invalid_content, content_type="text/plain"
    )
    request = factory.post("/upload/", {"document": document})
    user = user_factory("testuser", "12345", position_id=2)
    request.user = user

    add_middleware(request)

    # Mock the form and simulate form validation failure
    form = mocker.Mock(spec=ReportForm)
    form.is_valid.return_value = False
    form.errors = {"document": ["El archivo debe ser de formato Excel (xlsx)"]}

    # Create an instance of the view and set up the request and form
    view = ReportNnaFormView()
    view.setup(request)
    view.request = request
    view.args = ()
    view.kwargs = {}
    view.form = form

    # Invoke the form_invalid method (assuming this handles invalid form submissions)
    response = view.form_invalid(form)

    assert response.status_code == 302
    assert "El archivo debe ser de formato Excel (xlsx)" in [
        str(msg) for msg in messages.get_messages(request)
    ]
