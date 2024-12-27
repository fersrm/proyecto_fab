from ReportsApp.models import (
    Project,
    ProjectExtension,
    NNA,
    Notification,
    OnlyProjectExtension,
    EntryDetails,
)
from django.core.paginator import Paginator
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import (
    ListView,
    UpdateView,
    DeleteView,
    CreateView,
    DetailView,
)
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count
from .forms import (
    ProjectCreateForm,
    ProjectUpdateForm,
    ProjectExtensionCreateForm,
    ProjectExtensionUpdateForm,
    OnlyProjectExtensionCreateForm,
    OnlyProjectExtensionUpdateForm,
)

# Premiosos
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins import PermitsPositionMixin

# Create your views here.


class ProjectLisView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "pages/proyectos/proyectos.html"
    paginate_by = 7

    def get_queryset(self):
        queryset = super().get_queryset().order_by("-id")
        search_query = self.request.GET.get("search")

        if search_query:
            if search_query.isdigit():
                queryset = queryset.filter(Q(code=search_query))
            else:
                queryset = queryset.filter(
                    Q(project_name=search_query)
                    | Q(institution_FK__institution_name=search_query)
                )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(context["object_list"], self.paginate_by)
        page = self.request.GET.get("page")
        context["object_list"] = paginator.get_page(page)
        context["placeholder"] = "Buscar por código, nombre, institución"
        return context


class ProjectCreateView(LoginRequiredMixin, PermitsPositionMixin, CreateView):
    model = Project
    form_class = ProjectCreateForm
    template_name = "pages/proyectos/crear_proyecto.html"

    def form_valid(self, form):
        project = form.save(commit=False)
        project.active = True
        project.save()
        messages.success(self.request, "Proyecto agregado correctamente")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("ProjectList")


class ProjectUpdateView(LoginRequiredMixin, PermitsPositionMixin, UpdateView):
    model = Project
    form_class = ProjectUpdateForm
    template_name = "pages/proyectos/editar_proyecto.html"

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Proyecto editado correctamente")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("ProjectList")


class ProjectDeleteView(LoginRequiredMixin, PermitsPositionMixin, DeleteView):
    model = Project
    success_url = reverse_lazy("ProjectList")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        messages.success(self.request, "Proyecto eliminado correctamente")
        self.object.delete()
        return redirect(self.get_success_url())


###############################
#####      CUPOS     ##########
###############################
from utils.tasks import desactivar_proyectos
from ListaEsperaApp.models import NNAEntrante


class ActiveProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "pages/proyectos/cupos_project_list.html"
    context_object_name = "projects"
    paginate_by = 7

    def get_queryset(self):
        desactivar_proyectos()
        projects = Project.objects.filter(active=True)
        search_query = self.request.GET.get("search")

        # Annotar cada proyecto con el número de NNA activos (con current_status=True)
        projects = projects.annotate(
            nna_activos=Count(
                "entrydetails", filter=Q(entrydetails__current_status=True)
            )
        )

        # Filtro de búsqueda
        if search_query:
            if search_query.isdigit():
                projects = projects.filter(Q(code=search_query))
            else:
                projects = projects.filter(
                    Q(project_name__icontains=search_query)
                    | Q(institution_FK__institution_name__icontains=search_query)
                    | Q(tipo_proyecto__icontains=search_query)
                )

        projects = projects.order_by("date_project")

        return projects

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(context["projects"], self.paginate_by)
        page = self.request.GET.get("page")
        project_page = paginator.get_page(page)
        context["projects"] = project_page

        for project in context["projects"]:
            # Calcular los cupos disponibles
            project.cupos_disponibles = project.ability - project.nna_activos

            # Duración total del proyecto
            total_base_duration = project.duration  # en meses
            approved_project_extensions = project.onlyprojectextension_set.filter(
                approved=True
            )
            total_project_extension_months = sum(
                extension.extension for extension in approved_project_extensions
            )
            total_project_duration_months = (
                total_base_duration + total_project_extension_months
            )

            # Fecha de inicio del proyecto
            start_date = project.date_project
            time_delta = relativedelta(timezone.now().date(), start_date)

            # Total de meses desde el inicio del proyecto
            months_since_start = (time_delta.years * 12) + time_delta.months
            remaining_project_months = (
                total_project_duration_months - months_since_start
            )

            # Agregar la información de meses restantes al proyecto
            project.remaining_months = remaining_project_months

            # Obtener el número de solicitantes que coincidan con el tipo de proyecto y la comuna
            solicitantes_count = NNAEntrante.objects.filter(
                tipo_proyecto=project.tipo_proyecto,
                nna_FK__location_FK__commune=project.location_FK.commune,
            ).count()

            project.solicitantes = solicitantes_count

        context["placeholder"] = (
            "Buscar por código, nombre, institución, tipo de proyecto"
        )
        return context


###################################
##### Extensión de Fecha NNA ######
###################################
from django.utils import timezone
from dateutil.relativedelta import relativedelta


class ProjectExtensionListView(LoginRequiredMixin, ListView):
    model = ProjectExtension
    template_name = "pages/extension/proyectos_extension.html"
    paginate_by = 7

    def get_queryset(self):
        # Consulta solo de extensiones aprobadas y filtrado por búsqueda
        search_query = self.request.GET.get("search")

        project_extensions = (
            ProjectExtension.objects.filter(approved=True)
            .select_related("nna_FK__person_FK", "project_FK")
            .values(
                "nna_FK",
                "nna_FK__cod_nna",
                "nna_FK__person_FK__rut",
                "nna_FK__person_FK__name",
                "project_FK__code",
                "project_FK",
            )
            .annotate(total_extension=Sum("extension"))
        )

        if search_query:
            if search_query.isdigit():
                project_extensions = project_extensions.filter(
                    nna_FK__cod_nna=search_query
                )
            else:
                project_extensions = project_extensions.filter(
                    nna_FK__person_FK__rut=search_query
                )

        # Procesamiento de extensión de proyecto por NNA
        nna_projects = {}
        for extension in project_extensions:
            nna = extension["nna_FK"]
            cod_nna = extension["nna_FK__cod_nna"]
            rut = extension["nna_FK__person_FK__rut"]
            name = extension["nna_FK__person_FK__name"]
            project = extension["project_FK"]
            project_code = extension["project_FK__code"]
            total_nna_extension_months = extension["total_extension"]

            # Obtenemos los detalles de entrada del NNA al proyecto
            entry_details = EntryDetails.objects.filter(
                nna_FK=nna, project_FK=project
            ).first()

            if entry_details:
                # Calculamos la duración del NNA en el proyecto
                entry_date = entry_details.date_of_entry
                if entry_details.date_of_exit:
                    exit_date = entry_details.date_of_exit
                    nna_duration = relativedelta(exit_date, entry_date)
                else:
                    nna_duration = relativedelta(timezone.now().date(), entry_date)
                time_in_project_months = (nna_duration.years * 12) + nna_duration.months
            else:
                time_in_project_months = 0

            # Calculamos la duración total del NNA en el proyecto
            total_duration = time_in_project_months + total_nna_extension_months

            print(total_duration)
            # Solo guardamos el proyecto con mayor duración para cada NNA
            if (
                nna not in nna_projects
                or nna_projects[nna]["total_duration"] < total_duration
            ):
                nna_projects[nna] = {
                    "nna_FK": {"id": nna, "cod_nna": cod_nna, "rut": rut, "name": name},
                    "project": project,
                    "project_code": project_code,
                    "total_duration": total_duration,
                    "extension_count": ProjectExtension.objects.filter(
                        nna_FK=nna, project_FK=project, approved=True
                    ).count(),
                }

        # Retornamos los proyectos con la mayor extensión para cada NNA
        return list(nna_projects.values())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(context["object_list"], self.paginate_by)
        page = self.request.GET.get("page")
        context["object_list"] = paginator.get_page(page)
        context["placeholder"] = "Buscar por código NNA o RUT"
        return context


class ProjectExtensionCreateView(LoginRequiredMixin, CreateView):
    model = ProjectExtension
    form_class = ProjectExtensionCreateForm
    template_name = "pages/extension/extension_create_proyecto.html"

    def form_valid(self, form):
        nna = get_object_or_404(NNA, pk=self.kwargs["nna_pk"])
        project = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        user = self.request.user

        form.instance.nna_FK = nna
        form.instance.project_FK = project
        form.instance.user_FK = user

        # Duración total del proyecto
        total_base_duration = project.duration  # en meses
        approved_project_extensions = project.onlyprojectextension_set.filter(
            approved=True
        )
        total_project_extension_months = sum(
            extension.extension for extension in approved_project_extensions
        )
        total_project_duration_months = (
            total_base_duration + total_project_extension_months
        )

        # Fecha de inicio del proyecto
        start_date = project.date_project
        time_delta = relativedelta(timezone.now().date(), start_date)

        # Total de meses desde el inicio del proyecto
        months_since_start = (time_delta.years * 12) + time_delta.months
        remaining_project_months = total_project_duration_months - months_since_start

        # Tiempo que el NNA ha estado en el proyecto
        entry_details = EntryDetails.objects.filter(
            nna_FK=nna, project_FK=project, current_status=True
        ).first()
        if not entry_details:
            messages.error(
                self.request,
                "El NNA no tiene un registro de entrada activo en este proyecto.",
            )
            return self.form_invalid(form)

        try:
            entry_date = entry_details.date_of_entry
            if entry_details.date_of_exit:
                exit_date = entry_details.date_of_exit
                nna_duration = relativedelta(exit_date, entry_date)
            else:
                nna_duration = relativedelta(timezone.now().date(), entry_date)
            time_in_project_months = (nna_duration.years * 12) + nna_duration.months
        except EntryDetails.DoesNotExist:
            time_in_project_months = 0

        # Sumar las extensiones aprobadas del NNA en este proyecto
        approved_nna_extensions = ProjectExtension.objects.filter(
            nna_FK=nna, project_FK=project, approved=True
        )
        total_nna_extension_months = sum(
            extension.extension for extension in approved_nna_extensions
        )
        total_nna_time_in_project = time_in_project_months + total_nna_extension_months

        # Calcular el tiempo total proyectado con la nueva extensión
        requested_extension = form.instance.extension
        projected_total_nna_time = total_nna_time_in_project + requested_extension

        # Verificar si el tiempo proyectado excede el tiempo restante del proyecto
        if projected_total_nna_time > total_project_duration_months:
            messages.error(
                self.request,
                f"No es posible extender la estadía de este NNA en el proyecto. "
                f"Solo le quedan {remaining_project_months} meses activos al proyecto.",
            )
            return self.form_invalid(form)

        # Lógica de aprobación automática para extensiones menores a 7 meses
        if requested_extension < 7:
            form.instance.approved = True
            messages.success(self.request, "La extensión fue aprobada automáticamente.")
        else:
            form.instance.approved = False
            messages.info(self.request, "La extensión queda en espera de aprobación.")

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "ProjectExtensionDetail", kwargs={"pk": self.kwargs["nna_pk"]}
        )


class ProjectExtensionDetailView(LoginRequiredMixin, DetailView):
    model = NNA
    template_name = "pages/extension/nna_project_details.html"
    context_object_name = "nna"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtenemos los proyectos en los que el NNA ha estado
        nna_projects = Project.objects.filter(
            entrydetails__nna_FK=self.object
        ).distinct()

        projects_with_durations = []
        for project in nna_projects:
            # Obtenemos todas las extensiones del proyecto para este NNA
            all_extensions = ProjectExtension.objects.filter(
                nna_FK=self.object, project_FK=project
            )

            # Filtramos solo las extensiones aprobadas
            approved_extensions = all_extensions.filter(approved=True)
            total_approved_extension_months = (
                approved_extensions.aggregate(Sum("extension"))["extension__sum"] or 0
            )

            # Calculamos la duración base del proyecto más las extensiones
            entry_details = EntryDetails.objects.filter(
                nna_FK=self.object, project_FK=project
            ).first()

            if entry_details:
                entry_date = entry_details.date_of_entry
                if entry_details.date_of_exit:
                    exit_date = entry_details.date_of_exit
                    nna_duration = relativedelta(exit_date, entry_date)
                else:
                    nna_duration = relativedelta(timezone.now().date(), entry_date)
                time_in_project_months = (nna_duration.years * 12) + nna_duration.months
            else:
                time_in_project_months = 0

            # Sumamos la duración base y las extensiones aprobadas
            total_duration = time_in_project_months + total_approved_extension_months

            # Añadimos los datos del proyecto con la duración calculada
            projects_with_durations.append(
                {
                    "project": project,
                    "base_duration": time_in_project_months,
                    "extension_count": all_extensions.count(),
                    "total_extension": total_approved_extension_months,
                    "total_duration": total_duration,
                    "extensions": all_extensions,
                    "validity": entry_details.current_status,
                }
            )
            print("*" * 30)
            print(f"entry_details.date_of_entry: {entry_details.date_of_entry}")
            print(f"entry_details.date_of_exit: {entry_details.date_of_exit}")
            print(f"nna_duration: {nna_duration}")
            print(f"time_in_project_months: {time_in_project_months}")
            print(
                f"total_approved_extension_months: { total_approved_extension_months}"
            )
            print(f"total_duration: {total_duration}")
            print(f"validity: {entry_details.current_status}")
            print("*" * 30)
        # Añadimos los proyectos con duraciones al contexto
        context["projects_with_durations"] = projects_with_durations
        return context


class ExtensionNNADetailView(LoginRequiredMixin, PermitsPositionMixin, DetailView):
    model = ProjectExtension
    template_name = "pages/extension/nna_extension_details.html"
    context_object_name = "nna_extension"


class ProjectExtensionUpdateView(LoginRequiredMixin, PermitsPositionMixin, UpdateView):
    model = ProjectExtension
    form_class = ProjectExtensionUpdateForm
    template_name = "pages/extension/editar_proyecto_extension.html"

    def form_valid(self, form):
        project_extension = form.save(commit=False)
        project_extension.approved_user_FK = self.request.user
        project_extension.save()
        messages.success(self.request, "Aprobado correctamente")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error en el formulario")
        for field, errors in form.errors.items():
            for error in errors:
                print(field, error)
                messages.error(self.request, f"{error}")
        return redirect("ProjectExtensionList")

    def get_success_url(self):
        return reverse_lazy("ProjectExtensionList")


###############################
##### Notificaciones ##########
###############################
from utils.tasks import generar_alertas_nna_proyectos


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = "pages/extension/notificaciones.html"
    paginate_by = 7

    def get_queryset(self):
        search_query = self.request.GET.get("search")
        generar_alertas_nna_proyectos()
        notifications = Notification.objects.filter(is_active=True).order_by(
            "-alert_type"
        )
        if search_query:
            if search_query.isdigit():
                notifications = notifications.filter(nna_FK__cod_nna=search_query)
            else:
                notifications = notifications.filter(
                    nna_FK__person_FK__rut=search_query
                )
        return notifications

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(context["object_list"], self.paginate_by)
        page = self.request.GET.get("page")
        context["object_list"] = paginator.get_page(page)
        context["placeholder"] = "Buscar por código NNA o RUT"
        return context


#############################################
##### Extensión de Fecha de Proyectos #######
#############################################


class OnlyProjectExtensionListView(LoginRequiredMixin, ListView):
    model = OnlyProjectExtension
    template_name = "pages/proyectos/extension/proyectos_extension.html"
    paginate_by = 7

    def get_queryset(self):
        # Obtén el parámetro de búsqueda de la solicitud GET
        search_query = self.request.GET.get("search")

        # Consulta inicial para obtener extensiones aprobadas y sumar la extensión de cada proyecto
        project_extensions = (
            OnlyProjectExtension.objects.filter(approved=True)
            .select_related("project_FK")
            .values(
                "project_FK__code",
                "project_FK__project_name",
                "project_FK__type_of_attention",
                "project_FK__duration",
                "project_FK",
            )
            .annotate(total_extension=Sum("extension"))
        )

        # Filtra por código de proyecto si se proporciona un valor de búsqueda
        if search_query:
            if search_query.isdigit():
                project_extensions = project_extensions.filter(
                    project_FK__code=search_query
                )
            else:
                project_extensions = project_extensions.filter(
                    project_FK__project_name__icontains=search_query
                )

        # Procesa y construye los datos de proyectos con extensiones acumuladas
        projects_data = []
        for extension in project_extensions:
            code = extension["project_FK__code"]
            project_name = extension["project_FK__project_name"]
            type_of_attention = extension["project_FK__type_of_attention"]
            duration = extension["project_FK__duration"]
            total_extension = extension["total_extension"]
            project = extension["project_FK"]

            # Calcula la duración total del proyecto incluyendo las extensiones
            total_duration = duration + total_extension

            # Agrega los datos del proyecto al listado final
            projects_data.append(
                {
                    "code": code,
                    "project_name": project_name,
                    "type_of_attention": type_of_attention,
                    "base_duration": duration,
                    "veces_extension": OnlyProjectExtension.objects.filter(
                        project_FK=project
                    ).count(),
                    "total_duration": total_duration,
                    "id": project,
                }
            )

        return projects_data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(context["object_list"], self.paginate_by)
        page = self.request.GET.get("page")
        context["object_list"] = paginator.get_page(page)
        context["placeholder"] = "Buscar por código o nombre de proyecto"
        return context


class OnlyProjectExtensionCreateView(LoginRequiredMixin, CreateView):
    model = OnlyProjectExtension
    form_class = OnlyProjectExtensionCreateForm
    template_name = "pages/proyectos/extension/extension_create_proyecto.html"

    def form_valid(self, form):
        # Obtenemos el proyecto y el usuario actual
        project = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        user = self.request.user

        # Verificar si el proyecto está activo
        if not project.active:
            messages.error(self.request, "No se puede extender un proyecto inactivo.")
            return redirect("OnlyProjectExtensionDetail", pk=self.kwargs["project_pk"])

        # Asignar el proyecto y usuario al formulario
        form.instance.project_FK = project
        form.instance.user_FK = user

        # Lógica de aprobación automática si la extensión es menor a 7 meses
        if form.instance.extension < 7:
            form.instance.approved = True
            messages.success(self.request, "La extensión fue aprobada automáticamente.")
        else:
            form.instance.approved = False
            messages.info(self.request, "La extensión queda en espera de aprobación.")

        return super().form_valid(form)

    def get_success_url(self):
        # Redirige a la página de detalle del proyecto después de crear la extensión
        return reverse_lazy(
            "OnlyProjectExtensionDetail", kwargs={"pk": self.kwargs["project_pk"]}
        )


class OnlyProjectExtensionDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = "pages/proyectos/extension/project_details.html"
    context_object_name = "project"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtenemos todas las extensiones aprobadas para el proyecto actual
        all_extensions = OnlyProjectExtension.objects.filter(project_FK=self.object)

        total_extension_months = (
            all_extensions.aggregate(Sum("extension"))["extension__sum"] or 0
        )
        total_duration = self.object.duration + total_extension_months

        context["project_details"] = {
            "project": self.object,
            "base_duration": self.object.duration,
            "extension_count": all_extensions.count(),
            "total_extension": total_extension_months,
            "total_duration": total_duration,
            "extensions": all_extensions,
        }

        return context


class ExtensionProjectDetailView(LoginRequiredMixin, PermitsPositionMixin, DetailView):
    model = OnlyProjectExtension
    template_name = "pages/proyectos/extension/project_extension_details.html"
    context_object_name = "project_extension"


class OnlyProjectExtensionUpdateView(
    LoginRequiredMixin, PermitsPositionMixin, UpdateView
):
    model = OnlyProjectExtension
    form_class = OnlyProjectExtensionUpdateForm
    template_name = "pages/proyectos/extension/editar_proyecto_extension.html"

    def form_valid(self, form):
        project_extension = form.save(commit=False)
        project_extension.approved_user_FK = self.request.user
        project_extension.save()
        messages.success(self.request, "La extensión se aprobó correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("OnlyProjectExtensionList")
