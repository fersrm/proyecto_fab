import pytest
from django.contrib.auth.models import User
from ReportsApp.models import (
    Institution,
    Person,
    Location,
    Solicitor,
    LegalQuality,
    Tribunal,
    Legal,
    NNA,
    Project,
    EntryDetails,
)
from django.utils.dateparse import parse_date


@pytest.mark.django_db
def test_create_institution():
    # Crea una instancia de Institution y verifica que se haya guardado correctamente en la base de datos
    institution = Institution.objects.create(institution_name="Test Institution")
    assert Institution.objects.count() == 1
    assert institution.institution_name == "Test Institution"


@pytest.mark.django_db
def test_create_person():
    # Crea una instancia de Person y verifica que se haya guardado correctamente en la base de datos
    birthdate = parse_date("2000-01-01")
    person = Person.objects.create(
        rut="12345678-9",
        name="John",
        last_name_paternal="Doe",
        last_name_maternal="Smith",
        birthdate=birthdate,
        sex=True,
        address="123 Test St",
        nationality="Testland",
    )
    assert Person.objects.count() == 1
    assert person.name == "John"


@pytest.mark.django_db
def test_create_location():
    # Crea una instancia de Location y verifica que se haya guardado correctamente en la base de datos
    location = Location.objects.create(region=1, commune="Test Commune")
    assert Location.objects.count() == 1
    assert location.commune == "Test Commune"


@pytest.mark.django_db
def test_create_solicitor():
    # Crea una instancia de Solicitor y verifica que se haya guardado correctamente en la base de datos
    solicitor = Solicitor.objects.create(solicitor_name="Test Solicitor")
    assert Solicitor.objects.count() == 1
    assert solicitor.solicitor_name == "Test Solicitor"


@pytest.mark.django_db
def test_create_legal_quality():
    # Crea una instancia de LegalQuality y verifica que se haya guardado correctamente en la base de datos
    legal_quality = LegalQuality.objects.create(name_quality="Test Quality")
    assert LegalQuality.objects.count() == 1
    assert legal_quality.name_quality == "Test Quality"


@pytest.mark.django_db
def test_create_tribunal():
    # Crea una instancia de Tribunal y verifica que se haya guardado correctamente en la base de datos
    tribunal = Tribunal.objects.create(tribunal_name="Test Tribunal")
    assert Tribunal.objects.count() == 1
    assert tribunal.tribunal_name == "Test Tribunal"


@pytest.mark.django_db
def test_create_legal():
    # Crea una instancia de Legal y verifica que se haya guardado correctamente en la base de datos
    legal_quality = LegalQuality.objects.create(name_quality="Test Quality")
    tribunal = Tribunal.objects.create(tribunal_name="Test Tribunal")
    legal = Legal.objects.create(
        proceedings="Test Proceedings",
        cause_of_entry="Test Cause",
        legal_quality_FK=legal_quality,
        tribunal_FK=tribunal,
    )
    assert Legal.objects.count() == 1
    assert legal.proceedings == "Test Proceedings"


@pytest.mark.django_db
def test_create_nna():
    # Crea una instancia de NNA y verifica que se haya guardado correctamente en la base de datos
    birthdate = parse_date("2000-01-01")
    person = Person.objects.create(
        rut="12345678-9",
        name="John",
        last_name_paternal="Doe",
        last_name_maternal="Smith",
        birthdate=birthdate,
        sex=True,
        address="123 Test St",
        nationality="Testland",
    )
    location = Location.objects.create(region=1, commune="Test Commune")
    solicitor = Solicitor.objects.create(solicitor_name="Test Solicitor")
    legal_quality = LegalQuality.objects.create(name_quality="Test Quality")
    tribunal = Tribunal.objects.create(tribunal_name="Test Tribunal")
    legal = Legal.objects.create(
        proceedings="Test Proceedings",
        cause_of_entry="Test Cause",
        legal_quality_FK=legal_quality,
        tribunal_FK=tribunal,
    )
    user = User.objects.create_user(username="testuser", password="12345")
    nna = NNA.objects.create(
        cod_nna=1,
        type_of_attention=True,
        person_FK=person,
        location_FK=location,
        solicitor_FK=solicitor,
        legal_FK=legal,
        user_FK=user,
    )
    assert NNA.objects.count() == 1
    assert nna.cod_nna == 1


@pytest.mark.django_db
def test_create_project():
    # Crea una instancia de Project, la asocia con una Institution, y verifica que se haya guardado correctamente en la base de datos
    institution = Institution.objects.create(institution_name="Test Institution")
    project = Project.objects.create(code=1, project_name="Test Project")
    project.institution_FK.add(institution)
    assert Project.objects.count() == 1
    assert project.project_name == "Test Project"


@pytest.mark.django_db
def test_create_entry_details():
    # Crea una instancia de EntryDetails y verifica que se haya guardado correctamente en la base de datos
    birthdate = parse_date("2000-01-01")
    person = Person.objects.create(
        rut="12345678-9",
        name="John",
        last_name_paternal="Doe",
        last_name_maternal="Smith",
        birthdate=birthdate,
        sex=True,
        address="123 Test St",
        nationality="Testland",
    )
    location = Location.objects.create(region=1, commune="Test Commune")
    solicitor = Solicitor.objects.create(solicitor_name="Test Solicitor")
    legal_quality = LegalQuality.objects.create(name_quality="Test Quality")
    tribunal = Tribunal.objects.create(tribunal_name="Test Tribunal")
    legal = Legal.objects.create(
        proceedings="Test Proceedings",
        cause_of_entry="Test Cause",
        legal_quality_FK=legal_quality,
        tribunal_FK=tribunal,
    )
    user = User.objects.create_user(username="testuser", password="12345")
    nna = NNA.objects.create(
        cod_nna=1,
        type_of_attention=True,
        person_FK=person,
        location_FK=location,
        solicitor_FK=solicitor,
        legal_FK=legal,
        user_FK=user,
    )
    project = Project.objects.create(code=1, project_name="Test Project")
    entry_details = EntryDetails.objects.create(
        date_of_entry=parse_date("2022-01-01"),
        date_of_exit=parse_date("2022-06-01"),
        current_status=True,
        nna_FK=nna,
        project_FK=project,
    )
    assert EntryDetails.objects.count() == 1
    assert entry_details.nna_FK == nna
