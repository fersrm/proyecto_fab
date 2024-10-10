from ReportsApp.models import Project, ProjectExtension, NNA, Notification
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
from django.db.models import Q, Sum
from .forms import (
    ProjectCreateForm,
    ProjectUpdateForm,
    ProjectExtensionCreateForm,
    ProjectExtensionUpdateForm,
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
        form.save()
        messages.success(self.request, "Proyecto agregado correctamente")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error en el formulario")
        for field, errors in form.errors.items():
            for error in errors:
                print(field, error)
                messages.error(self.request, f"{error}")
        return redirect("ProjectCreate")

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

    def form_invalid(self, form):
        messages.error(self.request, "Error en el formulario")
        for field, errors in form.errors.items():
            for error in errors:
                print(field, error)
                messages.error(self.request, f"{error}")
        return redirect("ProjectEdit")

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


################################
##### Extensión de Fecha #######
################################


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
            total_extension = extension["total_extension"]

            # Obtenemos la duración del proyecto original
            project_duration = Project.objects.get(id=project).duration

            # Calculamos la duración total del proyecto con extensiones
            total_duration = project_duration + total_extension

            # Solo guardamos el proyecto con mayor duración para cada NNA
            if (
                nna not in nna_projects
                or nna_projects[nna]["total_duration"] < total_duration
            ):
                nna_projects[nna] = {
                    "nna_FK": {"id": nna, "cod_nna": cod_nna, "rut": rut, "name": name},
                    "project": project,
                    "total_duration": total_duration,
                    "extension_count": ProjectExtension.objects.filter(
                        nna_FK=nna, project_FK=project
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

        if form.instance.extension < 7:
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

        nna_projects = Project.objects.filter(
            entrydetails__nna_FK=self.object
        ).distinct()

        projects_with_durations = []
        for project in nna_projects:
            all_extensions = ProjectExtension.objects.filter(
                nna_FK=self.object, project_FK=project
            )

            approved_extensions = all_extensions.filter(approved=True)
            total_approved_extension_months = (
                approved_extensions.aggregate(Sum("extension"))["extension__sum"] or 0
            )

            total_duration = project.duration + total_approved_extension_months

            projects_with_durations.append(
                {
                    "project": project,
                    "base_duration": project.duration,
                    "extension_count": all_extensions.count(),
                    "total_extension": total_approved_extension_months,
                    "total_duration": total_duration,
                    "extensions": all_extensions,
                }
            )

        context["projects_with_durations"] = projects_with_durations
        return context


class ProjectExtensionUpdateView(LoginRequiredMixin, PermitsPositionMixin, UpdateView):
    model = ProjectExtension
    form_class = ProjectExtensionUpdateForm
    template_name = "pages/extension/editar_proyecto_extension.html"

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Aprobado correctamente")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error en el formulario")
        for field, errors in form.errors.items():
            for error in errors:
                print(field, error)
                messages.error(self.request, f"{error}")
        return redirect("ProjectExtensionEdit")

    def get_success_url(self):
        return reverse_lazy("ProjectExtensionList")


###############################
##### Notificaciones ##########
###############################


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = "pages/extension/notificaciones.html"
    paginate_by = 7

    def get_queryset(self):
        search_query = self.request.GET.get("search")

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
