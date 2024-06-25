from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from UsuarioApp.models import Profile
from ReportsApp.models import NNA
from DocumentoApp.models import DocumentPDF

# Create your views here.


class HomeView(LoginRequiredMixin, ListView):
    model = User
    template_name = "pages/index.html"

    def get_queryset(self):
        last_connected_users = User.objects.filter(
            Q(last_login__isnull=False)
        ).order_by("-last_login")[:5]
        return last_connected_users

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Agrega los usuarios activos al contexto
        recent_activity_cutoff = timezone.now() - timezone.timedelta(minutes=2)
        active_users = Profile.objects.filter(
            last_activity__gte=recent_activity_cutoff
        ).values_list("user_FK_id", flat=True)
        context["active_users"] = active_users

        # Agrega el recuento de NNA y la fecha de registro más reciente al contexto
        nna_count = NNA.objects.count()
        latest_nna = NNA.objects.order_by("-registration_date").first()
        latest_registration_date = latest_nna.registration_date if latest_nna else None
        latest_registration_user = (
            latest_nna.user_FK.username if latest_nna and latest_nna.user_FK else None
        )

        context["nna_count"] = nna_count
        context["latest_registration_date"] = latest_registration_date
        context["latest_registration_user"] = latest_registration_user

        # Agrega el recuento de PDF y la fecha de registro más reciente al contexto
        pdf_count = DocumentPDF.objects.filter(state=True).count()
        latest_pdf = DocumentPDF.objects.order_by("-date").first()
        latest_registration_date_pdf = latest_pdf.date if latest_pdf else None
        latest_registration_user_pdf = (
            latest_pdf.user_FK.username if latest_pdf and latest_pdf.user_FK else None
        )

        context["pdf_count"] = pdf_count
        context["latest_registration_date_pdf"] = latest_registration_date_pdf
        context["latest_registration_user_pdf"] = latest_registration_user_pdf

        return context
