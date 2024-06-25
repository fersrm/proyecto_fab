from django.views.generic import View, ListView, CreateView, DeleteView
from .forms import DocumentPdfCreateForm
from django.contrib import messages
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from .models import DocumentPDF
from core.mixins import PermitsPositionMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

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


@method_decorator(csrf_exempt, name="dispatch")
class DocumentPdfUpdateView(LoginRequiredMixin, PermitsPositionMixin, View):
    def post(self, request, *args, **kwargs):
        item_id = request.POST.get("item_id")
        try:
            item = DocumentPDF.objects.get(id=item_id)
            item.state = not item.state
            item.save()
            messages.success(request, "Estado actualizado correctamente")
            return JsonResponse({"success": True})
        except DocumentPDF.DoesNotExist:
            return JsonResponse({"success": False, "error": "Documento no encontrado"})
