from ReportsApp.models import Project
from django.core.paginator import Paginator
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import ListView, UpdateView, DeleteView, CreateView
from django.urls import reverse_lazy
from django.db.models import Q
from .forms import ProjectCreateForm, ProjectUpdateForm

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
