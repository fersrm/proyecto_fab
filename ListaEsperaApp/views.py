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
                and date_of_application != nna_entrante.date_of_application
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


###################################
from utils.tasks import actualizar_rankings_task, reorganizar_historial_prioridades_task


class SolicitudesPorProyectoListView(ListView):
    model = NNAEntrante
    template_name = "pages/nna_entrantes/solicitudes.html"
    context_object_name = "solicitantes"
    paginate_by = 7

    def get_queryset(self):
        actualizar_rankings_task()
        reorganizar_historial_prioridades_task()
        # Obtener el parámetro de la región desde la URL
        commune_id = self.kwargs.get("commune_id")
        tipo_proyecto = self.kwargs.get("proyecto")
        # Filtrar los solicitantes en la región específica y ordenar por prioridad y fecha
        return (
            NNAEntrante.objects.select_related("nna_FK__person_FK")
            .filter(
                nna_FK__location_FK=commune_id,
                tipo_proyecto=tipo_proyecto,
                is_processed_ranking=True,
            )
            .order_by("-priority", "date_of_application")
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
    template_name = "pages/nna_entrantes/solicitantes_por_comuna.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Datos procesados
        context["regiones_info"] = self._obtener_regiones_info()
        context["comunas_por_region"] = self._obtener_comunas_por_region(
            context["regiones_info"]
        )

        return context

    def _obtener_regiones_info(self):
        """Construye la estructura principal de regiones_info."""
        solicitantes_por_region_comuna_y_tipo = (
            NNAEntrante.objects.values(
                "nna_FK__location_FK__region",
                "nna_FK__location_FK__commune",
                "nna_FK__location_FK__id",
                "tipo_proyecto",
            )
            .annotate(solicitantes_count=Count("id"))
            .order_by(
                "nna_FK__location_FK__region",
                "nna_FK__location_FK__commune",
                "tipo_proyecto",
            )
        )

        proyectos_activos = self._obtener_proyectos_activos()
        proyectos_por_region_comuna_y_tipo = self._organizar_proyectos_por_region(
            proyectos_activos
        )

        regiones_info = []
        for item in solicitantes_por_region_comuna_y_tipo:
            self._procesar_solicitantes(
                item, regiones_info, proyectos_por_region_comuna_y_tipo
            )
        return regiones_info

    def _obtener_proyectos_activos(self):
        """Obtiene proyectos activos y calcula cupos y duración restante."""
        proyectos_activos = Project.objects.filter(active=True).annotate(
            nna_activos=Count(
                "entrydetails", filter=Q(entrydetails__current_status=True)
            )
        )

        for proyecto in proyectos_activos:
            proyecto.cupos_disponibles = proyecto.ability - proyecto.nna_activos

            total_duration = proyecto.duration + sum(
                ext.extension
                for ext in proyecto.onlyprojectextension_set.filter(approved=True)
            )
            months_since_start = self._calcular_meses_desde_inicio(
                proyecto.date_project
            )
            proyecto.remaining_months = max(0, total_duration - months_since_start)

        return proyectos_activos

    def _organizar_proyectos_por_region(self, proyectos):
        """Agrupa los proyectos por región, comuna y tipo."""
        proyectos_por_region = {}
        for proyecto in proyectos:
            region, comuna, tipo = (
                proyecto.location_FK.region,
                proyecto.location_FK.commune,
                proyecto.tipo_proyecto,
            )

            if region not in proyectos_por_region:
                proyectos_por_region[region] = {}
            if comuna not in proyectos_por_region[region]:
                proyectos_por_region[region][comuna] = {}
            if tipo not in proyectos_por_region[region][comuna]:
                proyectos_por_region[region][comuna][tipo] = []

            proyectos_por_region[region][comuna][tipo].append(proyecto)
        return proyectos_por_region

    def _procesar_solicitantes(self, item, regiones_info, proyectos_por_region):
        region, comuna, comuna_id, tipo, count = (
            item["nna_FK__location_FK__region"],
            item["nna_FK__location_FK__commune"],
            item["nna_FK__location_FK__id"],  # ID de la comuna
            item["tipo_proyecto"],
            item["solicitantes_count"],
        )

        proyectos_info = (
            proyectos_por_region.get(region, {}).get(comuna, {}).get(tipo, [])
        )
        cupos_disponibles = sum(proy.cupos_disponibles for proy in proyectos_info)
        solicitantes_sin_cupo = max(0, count - cupos_disponibles)

        region_data = next((r for r in regiones_info if r["region"] == region), None)
        if not region_data:
            region_data = {
                "region": region,
                "region_name": self._get_region_display(region),
                "comunas": [],
            }
            regiones_info.append(region_data)

        comuna_data = next(
            (c for c in region_data["comunas"] if c["commune"] == comuna), None
        )
        if not comuna_data:
            comuna_data = {
                "commune": comuna,
                "commune_id": comuna_id,
                "tipos_proyecto": [],
            }
            region_data["comunas"].append(comuna_data)

        comuna_data["tipos_proyecto"].append(
            {
                "tipo_proyecto": tipo,
                "solicitantes_count": count,
                "proyectos_info": proyectos_info,
                "solicitantes_sin_cupo": solicitantes_sin_cupo,
            }
        )

    def _top_comunas_por_region(self, regiones_info):
        """Construye la lista de comunas por región para mostrar."""
        top_cinco_por_region = {}

        for region_data in regiones_info:
            region = region_data["region"]
            for comuna in region_data["comunas"]:
                for tipo_proyecto in comuna["tipos_proyecto"]:
                    solicitantes_sin_cupo = tipo_proyecto["solicitantes_sin_cupo"]
                    if solicitantes_sin_cupo > 0:
                        if region not in top_cinco_por_region:
                            top_cinco_por_region[region] = []
                        top_cinco_por_region[region].append(
                            {
                                "commune": comuna["commune"],
                                "commune_id": comuna["commune_id"],
                                "tipo_proyecto": tipo_proyecto["tipo_proyecto"],
                                "solicitantes_sin_cupo": solicitantes_sin_cupo,
                            }
                        )

        return top_cinco_por_region

    def _obtener_comunas_por_region(self, regiones_info):
        top_cinco_por_region = self._top_comunas_por_region(regiones_info)

        for region, proyectos in top_cinco_por_region.items():
            top_cinco_por_region[region] = sorted(
                proyectos, key=lambda x: x["solicitantes_sin_cupo"], reverse=True
            )[:5]

        return [
            {
                "region_name": self._get_region_display(region),
                "region_id": region,
                "comunas": [
                    {
                        "commune": comuna["commune"],
                        "commune_id": comuna["commune_id"],
                        "proyectos": proyectos,
                    }
                    for comuna in proyectos
                ],
            }
            for region, proyectos in top_cinco_por_region.items()
        ]

    @staticmethod
    def _calcular_meses_desde_inicio(fecha_inicio):
        """Calcula la cantidad de meses desde la fecha de inicio hasta la actualidad."""
        delta = relativedelta(timezone.now().date(), fecha_inicio)
        return (delta.years * 12) + delta.months

    @staticmethod
    def _get_region_display(region_code):
        for code, name in Location.REGION_CHOICES:
            if code == region_code:
                return name
        return "Región desconocida"


class SolicitanteDeleteView(LoginRequiredMixin, PermitsPositionMixin, DeleteView):
    model = NNA
    success_url = reverse_lazy("ApplicantsRegionList")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        messages.success(self.request, "Solicitante eliminado correctamente")
        self.object.delete()
        return redirect(self.get_success_url())


#######################################


class RankingHistoryView(DetailView):
    model = NNAEntrante
    template_name = "pages/nna_entrantes/ranking_history.html"
    context_object_name = "nna"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["history"] = self.object.ranking_history.order_by("-changed_date")
        return context
