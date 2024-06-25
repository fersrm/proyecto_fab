import pytest
from django.contrib.auth.models import User
from UsuarioApp.models import Profile, Position
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.db import transaction
from ReportsApp.models import (
    Person,
    Location,
    Solicitor,
    Tribunal,
    LegalQuality,
    Legal,
    NNA,
    Institution,
    Project,
    EntryDetails,
)
from datetime import date


@pytest.fixture
def user_factory(db):
    @transaction.atomic
    def create_user(username, password, position_id):
        # Crea posiciones si no existen
        if not Position.objects.filter(user_position="Admin").exists():
            Position.objects.create(user_position="Admin")
        if not Position.objects.filter(user_position="Manager").exists():
            Position.objects.create(user_position="Manager")
        if not Position.objects.filter(user_position="User").exists():
            Position.objects.create(user_position="User")

        # Crea el usuario
        user = User.objects.create_user(username=username, password=password)

        # Crea el perfil del usuario
        Profile.objects.create(user_FK=user, position_FK_id=position_id)

        return user

    return create_user


def add_middleware(request):
    """Add necessary middleware to the request"""
    session_middleware = SessionMiddleware(lambda req: None)
    session_middleware.process_request(request)
    request.session.save()

    message_middleware = MessageMiddleware(lambda req: None)
    message_middleware.process_request(request)
    request.session.save()


@pytest.fixture
def create_nna_data():
    person = Person.objects.create(
        name="John",
        last_name_paternal="Doe",
        last_name_maternal="Smith",
        birthdate=date(2000, 1, 1),
        rut="12345678-9",
        sex=True,
        nationality="Chilean",
        address="123 Main St",
    )
    location = Location.objects.create(region=1, commune="Commune")
    solicitor = Solicitor.objects.create(solicitor_name="Solicitor")
    tribunal = Tribunal.objects.create(tribunal_name="Court")
    legal_quality = LegalQuality.objects.create(name_quality="Quality")
    legal = Legal.objects.create(
        legal_quality_FK=legal_quality,
        tribunal_FK=tribunal,
        proceedings="12345",
        cause_of_entry="Entry cause",
    )
    nna = NNA.objects.create(
        person_FK=person,
        location_FK=location,
        solicitor_FK=solicitor,
        legal_FK=legal,
        cod_nna="123",
    )

    institution = Institution.objects.create(institution_name="Institution")
    project = Project.objects.create(code=123, project_name="Project")
    project.institution_FK.set([institution])

    entry_details = EntryDetails.objects.create(
        project_FK=project, date_of_entry=date(2000, 1, 1), nna_FK=nna
    )

    return nna
