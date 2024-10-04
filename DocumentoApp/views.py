from django.views.generic import ListView, CreateView, DeleteView, UpdateView
from .forms import DocumentPdfCreateForm, DocumentPdfUpdateForm
from django.contrib import messages
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import DocumentPDF
from core.mixins import PermitsPositionMixin

# Create your views here.


class DocumentPdfCreateView(LoginRequiredMixin, CreateView):
    model = DocumentPDF
    form_class = DocumentPdfCreateForm
    template_name = "pages/documentos_pdf/carga_pdf.html"
    success_url = reverse_lazy("PdfList")

    def form_valid(self, form):
        user = self.request.user
        document_pdf = form.save(commit=False)
        document_pdf.user_FK = user
        document_pdf.state = False
        document_pdf.save()
        messages.success(self.request, "Archivo cargado con éxito")
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                print(field, error)
                messages.error(self.request, f"{error}")
        return redirect("PdfList")


class DocumentPdfListView(LoginRequiredMixin, ListView):
    model = DocumentPDF
    template_name = "pages/documentos_pdf/pdf_lista.html"

    def get_queryset(self):
        if (
            self.request.user.is_authenticated
            and self.request.user.profile.position_FK.id != 3
        ):
            return DocumentPDF.objects.all()
        return DocumentPDF.objects.filter(state=True)


class DocumentPdfDeleteView(LoginRequiredMixin, PermitsPositionMixin, DeleteView):
    model = DocumentPDF
    success_url = reverse_lazy("PdfList")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        messages.success(self.request, "PDF eliminado correctamente")
        self.object.delete()
        return redirect(self.get_success_url())


class DocumentPdfUpdateView(LoginRequiredMixin, PermitsPositionMixin, UpdateView):
    model = DocumentPDF
    form_class = DocumentPdfUpdateForm
    template_name = "pages/documentos_pdf/editar_pdf.html"

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Pdf editado correctamente")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error en el formulario")
        for field, errors in form.errors.items():
            for error in errors:
                print(field, error)
                messages.error(self.request, f"{error}")
        return redirect("PdfEdit")

    def get_success_url(self):
        return reverse_lazy("PdfList")
