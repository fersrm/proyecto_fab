from django.views.generic import FormView, View, ListView, TemplateView, DeleteView
from .forms import ReportForm, NnaEditForm, PersonEditForm
from django.contrib import messages
from django.urls import reverse_lazy
import pandas as pd
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from .models import (
    Institution,
    Project,
    Person,
    Location,
    EntryDetails,
    Solicitor,
    LegalQuality,
    Tribunal,
    Legal,
    NNA,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Count
from django.db.models import Q
from utils.helpers import list_chats
from django.core.paginator import Paginator

# para crear PDF
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

from core.mixins import PermitsPositionMixin
from collections import defaultdict
from datetime import datetime

from utils.helpers import (
    formatea_ordena_fechas,
    calcular_duracion_total,
    convierte_anios,
)
from django.db import transaction
from adapters.excel_adapter import ExcelAdapter
from concurrent.futures import ThreadPoolExecutor

# Create your views here.


class ReportNnaFormView(LoginRequiredMixin, PermitsPositionMixin, FormView):
    model = NNA
    form_class = ReportForm
    template_name = "pages/reportes_nna/carga_excel.html"
    success_url = reverse_lazy("ReportList")

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
            return redirect("ReportList")
        except Exception as e:
            print(e)
            messages.error(self.request, "Error al procesar el documento")
            return self.form_invalid(form)

    def load_existing_data(self):
        self.institutions = {i.institution_name: i for i in Institution.objects.all()}
        self.projects = {p.code: p for p in Project.objects.all()}
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
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [
                executor.submit(self.process_row, index, row, user, error_list)
                for index, row in df.iterrows()
            ]
            for future in futures:
                future.result()
        return error_list

    def process_row(self, index, row, user, error_list):
        try:
            adapter = ExcelAdapter(row)
            institution = self.get_or_create_institution(adapter)
            location = self.get_or_create_location(adapter)
            project = self.get_or_create_project(adapter, location, institution)
            person = self.get_or_create_person(adapter)
            solicitor = self.get_or_create_solicitor(adapter)
            legal_quality = self.get_or_create_legal_quality(adapter)
            tribunal = self.get_or_create_tribunal(adapter)
            legal = self.get_or_create_legal(adapter, legal_quality, tribunal)
            nna = self.get_or_create_nna(
                adapter, person, location, solicitor, legal, user
            )
            self.create_or_update_entry(adapter, nna, project)
        except Exception as e:
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

    def get_or_create_institution(self, adapter):
        institution_name = adapter.get_institution_name()
        if institution_name not in self.institutions:
            self.institutions[institution_name] = Institution.objects.create(
                institution_name=institution_name
            )
        return self.institutions[institution_name]

    def get_or_create_project(self, adapter, location, institution):
        attention = adapter.get_attention()
        project_code = adapter.get_project_code()
        project_name = adapter.get_project_name()

        if project_code not in self.projects:
            self.projects[project_code] = Project.objects.create(
                code=project_code,
                project_name=project_name,
                type_of_attention=attention,
                location_FK=location,
                institution_FK=institution,
            )

        return self.projects[project_code]

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

        if cod_nna in self.existing_nn_as:
            nna = self.existing_nn_as[cod_nna]
            if nna.person_FK.rut == person.rut:
                nna.person_FK = person
                nna.location_FK = location
                nna.solicitor_FK = solicitor
                nna.legal_FK = legal
                nna.user_FK = user
                nna.save()
            else:
                return None
        else:
            nna = NNA.objects.create(
                cod_nna=cod_nna,
                person_FK=person,
                location_FK=location,
                solicitor_FK=solicitor,
                legal_FK=legal,
                user_FK=user,
            )
            self.existing_nn_as[cod_nna] = nna
        return nna

    def create_or_update_entry(self, adapter, nna, project):
        current = adapter.get_current()
        admission_date = adapter.get_admission_date()
        discharge_date = adapter.get_discharge_date()

        existing_entry = EntryDetails.objects.filter(
            nna_FK=nna, project_FK=project
        ).first()
        if existing_entry and existing_entry.current_status:
            existing_entry.date_of_entry = admission_date
            existing_entry.date_of_exit = discharge_date
            existing_entry.current_status = current
            existing_entry.save()
        else:
            EntryDetails.objects.create(
                date_of_entry=admission_date,
                date_of_exit=discharge_date,
                current_status=current,
                nna_FK=nna,
                project_FK=project,
            )

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{error}")
        return redirect("ReportList")


class ReportNnaListView(LoginRequiredMixin, ListView):
    model = NNA
    template_name = "pages/reportes_nna/reporte_lista.html"
    paginate_by = 8

    def get_queryset(self):
        queryset = super().get_queryset().order_by("cod_nna")
        search_query = self.request.GET.get("search")

        if search_query:
            if search_query.isdigit():
                queryset = queryset.filter(Q(cod_nna=search_query))
            else:
                queryset = queryset.filter(
                    Q(person_FK__name__icontains=search_query)
                    | Q(person_FK__last_name_paternal__icontains=search_query)
                    | Q(person_FK__rut=search_query)
                    | Q(location_FK__commune__icontains=search_query)
                )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(context["object_list"], self.paginate_by)
        page = self.request.GET.get("page")
        context["object_list"] = paginator.get_page(page)
        context["placeholder"] = "Buscar por código, nombre, apellido, rut o comuna"
        return context


class GeneratePdfNnaView(LoginRequiredMixin, View):
    def obtain_project_information(self, nna):
        project_information = []
        added_projects = set()

        for entry in nna.entrydetails_set.all():
            project = entry.project_FK
            if project.code not in added_projects:
                added_projects.add(project.code)

                institution_name = project.institution_FK.institution_name

                admission_date = entry.date_of_entry.strftime("%d-%m-%Y")
                discharge_date = (
                    entry.date_of_exit.strftime("%d-%m-%Y")
                    if entry.date_of_exit
                    else "N/A"
                )

                project_information.extend(
                    [
                        ["Institución", institution_name],
                        ["Proyecto", project.project_name],
                        ["Fecha de Ingreso", admission_date],
                        ["Fecha de Egreso", discharge_date],
                        [
                            "Tipo de Atención",
                            "RESIDENCIAL" if entry.current_status else "AMBULATORIA",
                        ],
                    ]
                )
        return project_information

    def generate_pdf(self, nna, cod_id, selected_info):
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="reporte_{cod_id}.pdf"'
        # Configurar el documento con márgenes personalizados
        doc = SimpleDocTemplate(
            response, pagesize=A4, topMargin=0.5 * inch, bottomMargin=1 * inch
        )
        elements = []

        # Titulo
        styles = getSampleStyleSheet()
        title = Paragraph(f"Reporte de NNA - {nna.cod_nna}", styles["Title"])
        elements.append(title)
        elements.append(Spacer(1, 0.1 * inch))

        # Fecha y hora
        current_datetime = datetime.now().strftime("%d-%m-%Y %H:%M")
        date_paragraph = Paragraph(
            f"Generado el: {current_datetime}",
            ParagraphStyle(name="Date", fontSize=12, alignment=1),
        )
        elements.append(date_paragraph)
        elements.append(Spacer(1, 0.2 * inch))

        # Subtítulos
        subtitle_style = ParagraphStyle(
            name="Subtitle",
            parent=styles["Normal"],
            fontSize=12,
            spaceBefore=0,
            spaceAfter=3,
            alignment=1,
        )

        def add_subtitle(text):
            subtitle = Paragraph(text, subtitle_style)
            elements.append(subtitle)
            elements.append(Spacer(1, 0.1 * inch))

        data_sections = {
            "personal": (
                "Información Personal",
                [
                    ["Nombre", nna.person_FK.name],
                    ["Apellido Paterno", nna.person_FK.last_name_paternal],
                    ["Apellido Materno", nna.person_FK.last_name_maternal],
                    [
                        "Fecha de Nacimiento",
                        nna.person_FK.birthdate.strftime("%d-%m-%Y"),
                    ],
                    ["RUT", nna.person_FK.rut],
                    ["Sexo", "Masculino" if nna.person_FK.sex else "Femenino"],
                    ["Nacionalidad", nna.person_FK.nationality],
                ],
            ),
            "ubicacion": (
                "Información de Ubicación",
                [
                    ["Dirección", nna.person_FK.address],
                    ["Región", nna.location_FK.region],
                    ["Comuna", nna.location_FK.commune],
                ],
            ),
            "proyecto": (
                "Información de Proyecto",
                self.obtain_project_information(nna),
            ),
            "legal": (
                "Información Legal",
                [
                    ["Solicitante de Ingreso", nna.solicitor_FK.solicitor_name],
                    ["Calidad Jurídica", nna.legal_FK.legal_quality_FK.name_quality],
                    ["Tribunal", nna.legal_FK.tribunal_FK.tribunal_name],
                    ["Expediente", nna.legal_FK.proceedings],
                    ["Causal de Ingreso", nna.legal_FK.cause_of_entry],
                ],
            ),
        }

        for section_key in selected_info:
            if section_key in data_sections:
                section_title, section_data = data_sections[section_key]
                add_subtitle(section_title)
                table = Table(section_data, colWidths=[2.5 * inch, 4 * inch])
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (0, -1), colors.grey),
                            ("TEXTCOLOR", (0, 0), (0, -1), colors.whitesmoke),
                            ("BACKGROUND", (1, 0), (1, -1), colors.whitesmoke),
                            ("TEXTCOLOR", (1, 0), (1, -1), colors.black),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                            ("FONTSIZE", (0, 0), (-1, -1), 9),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ]
                    )
                )
            elements.append(table)
            elements.append(Spacer(1, 0.1 * inch))

        # Footer
        footer_line1 = Paragraph(
            "Este reporte fue generado automáticamente.", styles["Normal"]
        )
        footer_line2 = Paragraph(f"Firmado por: {self.request.user}")
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(footer_line1)
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(footer_line2)

        doc.build(elements)
        return response

    def get(self, request, *args, **kwargs):
        cod_id = kwargs.get("pk")
        nna = get_object_or_404(NNA, id=cod_id)
        all_info_requested = request.GET.get("info")

        if all_info_requested == "all":
            selected_info = ["personal", "ubicacion", "proyecto", "legal"]
            return self.generate_pdf(nna, cod_id, selected_info)
        messages.error(self.request, "Parámetro no admitido")
        return redirect("ReportList")

    def post(self, request, *args, **kwargs):
        cod_id = kwargs.get("pk")
        nna = get_object_or_404(NNA, id=cod_id)

        selected_info = request.POST.getlist("info")

        if not selected_info:
            messages.error(self.request, "Tiene que marcar una opción")
            return redirect("ReportList")

        return self.generate_pdf(nna, cod_id, selected_info)


class ChartsReportNnaTemplateView(LoginRequiredMixin, TemplateView):
    template_name = "pages/graficos_nna/graficos.html"

    def get_context_data(self, **kwargs):
        # Consulta para obtener los conteos de hombres y mujeres por regiones
        context = super().get_context_data(**kwargs)

        nnas_m = (
            NNA.objects.filter(person_FK__sex=True)
            .values("location_FK__region")
            .annotate(count=Count("id"))
        )

        nnas_f = (
            NNA.objects.filter(person_FK__sex=False)
            .values("location_FK__region")
            .annotate(count=Count("id"))
        )

        resul_m = list_chats(nnas_m)
        resul_f = list_chats(nnas_f)

        context["hombres"] = resul_m
        context["mujeres"] = resul_f

        # Consulta para obtener los conteos de diferentes causas judiciales por comuna y sexo
        top_communes = (
            NNA.objects.values("location_FK__commune")
            .annotate(person_count=Count("person_FK"))
            .order_by("-person_count")[:20]
        )

        top_commune_names = [
            commune["location_FK__commune"] for commune in top_communes
        ]

        legal_cases_by_commune_and_sex = (
            NNA.objects.filter(location_FK__commune__in=top_commune_names)
            .values(
                "location_FK__commune", "person_FK__sex", "legal_FK__cause_of_entry"
            )
            .annotate(count=Count("legal_FK", distinct=True))
            .values("location_FK__commune", "person_FK__sex")
            .annotate(legal_count=Count("legal_FK__cause_of_entry"))
            .order_by("location_FK__commune", "person_FK__sex")
        )

        # Crear diccionarios separados para hombres y mujeres
        male_commune_legal_count_dict = defaultdict(int)
        female_commune_legal_count_dict = defaultdict(int)

        for item in legal_cases_by_commune_and_sex:
            commune = item["location_FK__commune"]

            if item["person_FK__sex"]:
                male_commune_legal_count_dict[commune] += item["legal_count"]
            else:
                female_commune_legal_count_dict[commune] += item["legal_count"]

        all_communes = sorted(
            male_commune_legal_count_dict.keys()
            | female_commune_legal_count_dict.keys()
        )

        male_legal_counts = [
            male_commune_legal_count_dict[commune] for commune in all_communes
        ]
        female_legal_counts = [
            female_commune_legal_count_dict[commune] for commune in all_communes
        ]

        # añade las listas al contexto
        context["communes"] = all_communes
        context["male_legal_counts"] = male_legal_counts
        context["female_legal_counts"] = female_legal_counts

        return context


class NnaDeleteView(LoginRequiredMixin, PermitsPositionMixin, DeleteView):
    model = NNA
    success_url = reverse_lazy("ReportList")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        messages.success(self.request, "NNA eliminado correctamente")
        self.object.delete()
        return redirect(self.get_success_url())


class NnaUpdateView(LoginRequiredMixin, PermitsPositionMixin, View):
    template_name = "pages/reportes_nna/nna_editar.html"

    def get(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        nna = get_object_or_404(NNA, pk=pk)
        person = nna.person_FK

        nna_form = NnaEditForm(instance=nna)
        person_form = PersonEditForm(instance=person)

        context = {"nna_form": nna_form, "person_form": person_form}

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        nna = get_object_or_404(NNA, pk=pk)
        person = nna.person_FK

        nna_form = NnaEditForm(request.POST, instance=nna)
        person_form = PersonEditForm(request.POST, instance=person)

        if nna_form.is_valid() and person_form.is_valid():
            try:
                nna_form.save()
                person_form.save()
                messages.success(request, "NNA actualizado con éxito.")
            except Exception as e:
                print(e)
                print("*" * 30)
                messages.error(request, "Error al actualizar NNA")

            return redirect("ReportList")

        context = {"nna_form": nna_form, "person_form": person_form}

        return render(request, self.template_name, context)


## Funcionalidad fechas desde la db


class ReportListDateView(LoginRequiredMixin, ListView):
    model = NNA
    template_name = "pages/fechas_nna/tabla_fechas.html"
    paginate_by = 8

    def get_queryset(self):
        queryset = super().get_queryset().order_by("cod_nna")
        search_query = self.request.GET.get("search")

        if search_query:
            if search_query.isdigit():
                queryset = queryset.filter(Q(cod_nna=search_query))
            else:
                queryset = queryset.filter(
                    Q(person_FK__name__icontains=search_query)
                    | Q(person_FK__rut=search_query)
                    | Q(location_FK__commune__icontains=search_query)
                )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(context["object_list"], self.paginate_by)
        page = self.request.GET.get("page")
        nna_page = paginator.get_page(page)

        # Obtener los códigos de NNA de la página actual
        codes_nna = [nna.cod_nna for nna in nna_page]

        # Obtener los detalles de entrada para estos códigos
        entry_details = EntryDetails.objects.filter(
            nna_FK__cod_nna__in=codes_nna
        ).values(
            "nna_FK__cod_nna",
            "date_of_entry",
            "date_of_exit",
            "current_status",
            "project_FK__project_name",
        )

        if not entry_details.exists():
            return context

        # Convertir los datos a un DataFrame de pandas
        df = pd.DataFrame(entry_details)

        cod_nna = "nna_FK__cod_nna"
        date_of_entry = "date_of_entry"
        date_of_exit = "date_of_exit"
        current_status = "current_status"
        project = "project_FK__project_name"

        columnas_deseadas = [
            cod_nna,
            date_of_entry,
            date_of_exit,
            current_status,
            project,
        ]
        df_resultado = df[columnas_deseadas]
        tablas_por_correlativo = {}

        # Itera sobre cada correlativo y filtra los datos
        for correlativo in df_resultado[cod_nna].unique():
            tabla_correlativo = df_resultado[df_resultado[cod_nna] == correlativo]
            tablas_por_correlativo[correlativo] = tabla_correlativo

        resultados_list = []

        for correlativo, tabla in tablas_por_correlativo.items():
            data = tabla[
                [
                    date_of_entry,
                    date_of_exit,
                    current_status,
                    project,
                ]
            ]
            df = formatea_ordena_fechas(data)

            duracion_total = calcular_duracion_total(df)
            anios, meses, dias = convierte_anios(duracion_total)
            aproximadamente_str = f"{anios} años, {meses} meses y {dias} días"

            df_ultima_fila = df.sort_values(by=date_of_exit)
            ultima_fila = df_ultima_fila.iloc[-1]
            ultima_fecha_egreso = ultima_fila[date_of_exit].date()
            vigente = ultima_fila[current_status]
            ultimo_proyecto = ultima_fila[project]

            # Agregar los resultados a la lista
            resultados_list.append(
                {
                    "correlativo": correlativo,
                    "duracion_total_dias": duracion_total,
                    "tiempo_aproximado": aproximadamente_str,
                    "ultima_fecha": ultima_fecha_egreso,
                    "vigente": vigente,
                    "ultimo_proyecto": ultimo_proyecto,
                }
            )

        for nna in nna_page:
            resultado = next(
                (
                    item
                    for item in resultados_list
                    if item["correlativo"] == nna.cod_nna
                ),
                None,
            )
            nna.duracion_total_dias = (
                resultado["duracion_total_dias"] if resultado else None
            )
            nna.tiempo_aproximado = (
                resultado["tiempo_aproximado"] if resultado else None
            )
            nna.ultima_fecha = resultado["ultima_fecha"] if resultado else None
            nna.vigente = resultado["vigente"] if resultado else None
            nna.ultimo_proyecto = resultado["ultimo_proyecto"] if resultado else None

        context["object_list"] = nna_page
        context["placeholder"] = "Buscar por código, nombre, apellido, rut o comuna"

        return context
