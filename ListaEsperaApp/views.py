from django.views.generic import ListView, DetailView, FormView, DeleteView
from .models import NNAEntrante, PriorityHistory
from ReportsApp.models import (
    Person,
    Location,
    Solicitor,
    LegalQuality,
    Tribunal,
    Legal,
    NNA,
    Project,
)
from django.shortcuts import redirect
from .forms import ReportForm
from django.contrib import messages
from django.urls import reverse_lazy
import pandas as pd
from django.db import transaction
from adapters.excel_adapter import ExcelAdapterApplicants
from django.http import Http404
from django.db.models import Count, Q
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.core.paginator import Paginator

# Premiosos
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import PermitsPositionMixin

# Create your views here.


class ApplicantsFormView(FormView):
    model = NNA
    form_class = ReportForm
    template_name = "pages/nna_entrantes/carga_excel.html"
    success_url = reverse_lazy("ApplicantsRegionList")

    def form_valid(self, form):
        document = form.cleaned_data["document"]
        user = self.request.user
        try:
            df = pd.read_excel(document)

            with transaction.atomic():
                self.load_existing_data()
                error_list = self.process_dataframe(df, user)

            if error_list:
                for error in error_list:
                    messages.error(self.request, error, extra_tags="excel_error")

            messages.success(self.request, "Documento Cargado")
            return redirect("ApplicantsRegionList")
        except Exception as e:
            print(e)
            messages.error(self.request, "Error al procesar el documento")
            return self.form_invalid(form)

    def load_existing_data(self):
        self.persons = {p.rut: p for p in Person.objects.all()}
        self.locations = {f"{l.region}-{l.commune}": l for l in Location.objects.all()}
        self.solicitors = {s.solicitor_name: s for s in Solicitor.objects.all()}
        self.legal_qualities = {
            lq.name_quality: lq for lq in LegalQuality.objects.all()
        }
        self.tribunals = {t.tribunal_name: t for t in Tribunal.objects.all()}
        self.existing_nn_as = NNA.objects.in_bulk(field_name="cod_nna")
        self.legals = {l.proceedings: l for l in Legal.objects.all()}

    def process_dataframe(self, df, user):
        error_list = []
        for index, row in df.iterrows():
            self.process_row(index, row, user, error_list)
        return error_list

    def process_row(self, index, row, user, error_list):
        try:
            adapter = ExcelAdapterApplicants(row)
            location = self.get_or_create_location(adapter)
            person = self.get_or_create_person(adapter)
            solicitor = self.get_or_create_solicitor(adapter)
            legal_quality = self.get_or_create_legal_quality(adapter)
            tribunal = self.get_or_create_tribunal(adapter)
            legal = self.get_or_create_legal(adapter, legal_quality, tribunal)
            nna = self.get_or_create_nna(
                adapter, person, location, solicitor, legal, user
            )
            self.create_or_update_NNAEntrante(adapter, nna)

        except Exception as e:
            print(e)
            cod_nna = adapter.get_cod_nna()
            if "valor nulo en la columna" in str(e):
                error_message = (
                    f"Error en la fila {index + 2}: El código NNA {cod_nna} no se pudo procesar porque falta un dato requerido en la columna. "
                    f"Por favor, revisa que todos los valores estén completos, o que no este duplicado el código NNA"
                )
            elif "llave duplicada viola restricción de unicidad" in str(e):
                error_message = (
                    f"Error en la fila {index + 2}: El código NNA {cod_nna} no se pudo procesar porque la persona ya está registrada con otro código. "
                    f"Verifica que no se esté ingresando información duplicada."
                )
            else:
                error_message = (
                    f"Error en la fila {index + 2} con el código NNA {cod_nna}: {str(e)}. "
                    f"Por favor, revisa la fila y corrige el error."
                )
            error_list.append(error_message)

    def get_or_create_person(self, adapter):
        rut = adapter.get_rut()
        if rut not in self.persons:
            self.persons[rut] = Person.objects.create(
                rut=rut,
                name=adapter.get_name(),
                last_name_paternal=adapter.get_last_name_paternal(),
                last_name_maternal=adapter.get_last_name_maternal(),
                birthdate=adapter.get_birthdate(),
                sex=adapter.get_sex(),
                address=adapter.get_address(),
                nationality=adapter.get_nationality(),
            )
        return self.persons[rut]

    def get_or_create_location(self, adapter):
        location_key = adapter.get_location_key()
        if location_key not in self.locations:
            self.locations[location_key] = Location.objects.create(
                region=adapter.get_region(),
                commune=adapter.get_commune(),
            )
        return self.locations[location_key]

    def get_or_create_solicitor(self, adapter):
        solicitor_name = adapter.get_solicitor_name()
        if solicitor_name not in self.solicitors:
            self.solicitors[solicitor_name] = Solicitor.objects.create(
                solicitor_name=solicitor_name
            )
        return self.solicitors[solicitor_name]

    def get_or_create_legal_quality(self, adapter):
        legal_quality_name = adapter.get_legal_quality_name()
        if legal_quality_name not in self.legal_qualities:
            self.legal_qualities[legal_quality_name] = LegalQuality.objects.create(
                name_quality=legal_quality_name
            )
        return self.legal_qualities[legal_quality_name]

    def get_or_create_tribunal(self, adapter):
        tribunal_name = adapter.get_tribunal_name()
        if tribunal_name not in self.tribunals:
            self.tribunals[tribunal_name] = Tribunal.objects.create(
                tribunal_name=tribunal_name
            )
        return self.tribunals[tribunal_name]

    def get_or_create_legal(self, adapter, legal_quality, tribunal):
        proceedings = adapter.get_proceedings()
        if proceedings not in self.legals:
            self.legals[proceedings] = Legal.objects.create(
                proceedings=proceedings,
                cause_of_entry=adapter.get_cause_of_entry(),
                legal_quality_FK=legal_quality,
                tribunal_FK=tribunal,
            )
        return self.legals[proceedings]

    def get_or_create_nna(self, adapter, person, location, solicitor, legal, user):
        cod_nna = adapter.get_cod_nna()

        if cod_nna not in self.existing_nn_as:
            nna = NNA.objects.create(
                cod_nna=cod_nna,
                person_FK=person,
                location_FK=location,
                solicitor_FK=solicitor,
                legal_FK=legal,
                user_FK=user,
                not_in_project=True,
            )
            self.existing_nn_as[cod_nna] = nna
        return self.existing_nn_as[cod_nna]

    def create_or_update_NNAEntrante(self, adapter, nna):
        tipo_proyecto = adapter.get_tipo_proyecto()
        date_of_application = adapter.get_date_of_application()
        priority = adapter.get_priority()

        nna_entrante = NNAEntrante.objects.filter(
            nna_FK=nna, tipo_proyecto=tipo_proyecto
        ).first()

        if nna_entrante:

            if (
                nna_entrante.priority != priority
                and date_of_application > nna_entrante.date_of_application
            ):
                nna_entrante.update_priority(priority, date_of_application)
        else:
            NNAEntrante.objects.create(
                nna_FK=nna,
                tipo_proyecto=tipo_proyecto,
                date_of_application=date_of_application,
                priority=priority,
            )

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{error}")
        return redirect("ApplicantsList")


class SolicitudesPorProyectoListView(ListView):
    model = NNAEntrante
    template_name = "pages/nna_entrantes/solicitudes.html"
    context_object_name = "solicitantes"
    paginate_by = 7

    def get_queryset(self):
        # Obtener el parámetro de la región desde la URL
        region_id = self.kwargs.get("region_id")
        # Filtrar los solicitantes en la región específica y ordenar por prioridad y fecha
        return (
            NNAEntrante.objects.select_related("nna_FK__person_FK")
            .filter(nna_FK__location_FK__region=region_id)
            .order_by("priority", "date_of_application")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(context["solicitantes"], self.paginate_by)
        page = self.request.GET.get("page")
        context["solicitantes"] = paginator.get_page(page)
        return context


class HistorialSolicitanteDetailView(DetailView):
    model = NNAEntrante
    template_name = "pages/nna_entrantes/historial_solicitante.html"
    context_object_name = "solicitante"

    def get_object(self):
        nna_id = self.kwargs.get("nna_id")
        solicitantes = NNAEntrante.objects.filter(nna_FK_id=nna_id)

        if not solicitantes.exists():
            raise Http404("No se encontró historial para este solicitante.")

        return solicitantes

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        solicitantes = self.get_object()

        # Obtener el nombre del NNA (solo una vez, del primer solicitante)
        context["solicitante_name"] = solicitantes.first().nna_FK.person_FK.name

        # Agrupar historial por tipo de proyecto
        history_by_project_type = {}
        for solicitante in solicitantes:
            history = PriorityHistory.objects.filter(
                nna_entrante_FK=solicitante
            ).order_by("-changed_date")

            for entry in history:
                tipo_proyecto = entry.tipo_proyecto
                if tipo_proyecto not in history_by_project_type:
                    history_by_project_type[tipo_proyecto] = []
                history_by_project_type[tipo_proyecto].append(entry)

        context["history_by_nna_entrante"] = history_by_project_type

        return context


class SolicitantesPorRegionView(ListView):
    model = Location
    template_name = "pages/nna_entrantes/solicitantes_por_region.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        def get_region_display(region_code):
            for code, name in Location.REGION_CHOICES:
                if code == region_code:
                    return name
            return "Región desconocida"

        # Contar solicitantes agrupados por región y tipo de proyecto
        solicitantes_por_region_y_tipo = (
            NNAEntrante.objects.values("nna_FK__location_FK__region", "tipo_proyecto")
            .annotate(solicitantes_count=Count("id"))
            .order_by("nna_FK__location_FK__region", "tipo_proyecto")
        )

        # Obtener proyectos activos agrupados por región y tipo de proyecto
        proyectos_activos = Project.objects.filter(active=True).annotate(
            nna_activos=Count(
                "entrydetails", filter=Q(entrydetails__current_status=True)
            )
        )

        # Diccionario para almacenar información sobre los proyectos y cupos por región y tipo de proyecto
        proyectos_por_region_y_tipo = {}

        for proyecto in proyectos_activos:
            region = proyecto.location_FK.region
            tipo_proyecto = proyecto.tipo_proyecto

            # Calcular los cupos disponibles
            proyecto.cupos_disponibles = proyecto.ability - proyecto.nna_activos

            # Calcular el tiempo restante de vigencia del proyecto
            total_base_duration = proyecto.duration  # en meses
            approved_extensions = proyecto.onlyprojectextension_set.filter(
                approved=True
            )
            total_extension_months = sum(
                extension.extension for extension in approved_extensions
            )
            total_duration = total_base_duration + total_extension_months

            # Fecha de inicio del proyecto
            start_date = proyecto.date_project
            time_delta = relativedelta(timezone.now().date(), start_date)

            months_since_start = (time_delta.years * 12) + time_delta.months

            proyecto.remaining_months = total_duration - months_since_start

            # Agrupar proyectos por región y tipo de proyecto
            if region not in proyectos_por_region_y_tipo:
                proyectos_por_region_y_tipo[region] = {}
            if tipo_proyecto not in proyectos_por_region_y_tipo[region]:
                proyectos_por_region_y_tipo[region][tipo_proyecto] = []
            proyectos_por_region_y_tipo[region][tipo_proyecto].append(proyecto)

        # Crear una estructura de datos para el contexto con la información de cada región y tipo de proyecto
        regiones_info = []
        for item in solicitantes_por_region_y_tipo:
            region = item["nna_FK__location_FK__region"]
            tipo_proyecto = item["tipo_proyecto"]
            solicitantes_count = item["solicitantes_count"]
            proyectos_info = proyectos_por_region_y_tipo.get(region, {}).get(
                tipo_proyecto, []
            )

            # Total de cupos disponibles para este tipo de proyecto en la región
            cupos_disponibles_total = sum(
                proy.cupos_disponibles for proy in proyectos_info
            )

            # Proyectos con cupos disponibles
            proyectos_con_cupos = [
                proy for proy in proyectos_info if proy.cupos_disponibles > 0
            ]
            proyectos_con_cupos_info = [
                {
                    "proyecto": proy,
                    "cupos_disponibles": proy.cupos_disponibles,
                    "remaining_months": proy.remaining_months,
                    "region": region,
                }
                for proy in proyectos_con_cupos
            ]

            # Determinar cuántos solicitantes quedan sin cupo
            solicitantes_sin_cupo = max(0, solicitantes_count - cupos_disponibles_total)

            # Añadir la información al contexto
            regiones_info.append(
                {
                    "region": region,
                    "region_name": get_region_display(region),
                    "tipo_proyecto": tipo_proyecto,
                    "solicitantes_count": solicitantes_count,
                    "proyectos_info": proyectos_con_cupos_info,
                    "solicitantes_sin_cupo": solicitantes_sin_cupo,
                }
            )

        # Obtener los cinco tipos de proyecto con mayor demanda sin cupo en todas las regiones
        sin_cupo = [tipo for tipo in regiones_info if tipo["solicitantes_sin_cupo"] > 0]
        sin_cupo_ordenados = sorted(
            sin_cupo, key=lambda x: x["solicitantes_sin_cupo"], reverse=True
        )[:5]

        context["regiones_info"] = regiones_info
        context["sin_cupo_mayores"] = sin_cupo_ordenados
        return context


class SolicitanteDeleteView(LoginRequiredMixin, PermitsPositionMixin, DeleteView):
    model = NNA
    success_url = reverse_lazy("ApplicantsRegionList")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        messages.success(self.request, "Solicitante eliminado correctamente")
        self.object.delete()
        return redirect(self.get_success_url())
