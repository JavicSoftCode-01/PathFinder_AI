import json
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from utils.safe_views import SafeExceptionMixin
from django.core.mail import send_mail
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from .forms import UserFeedbackForm
from .models import TrainingExercise


class HomeView(SafeExceptionMixin, LoginRequiredMixin, TemplateView):
  template_name = 'core/home.html'

  def get(self, request, *args, **kwargs):
    if not request.session.get('welcome_shown', False):
      messages.success(request, f"Bienvenido {request.user.full_name}")
      request.session['welcome_shown'] = True
    return super().get(request, *args, **kwargs)

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    first_name = self.request.user.full_name.split()[0] if self.request.user.full_name else 'Usuario'
    context['user_name'] = first_name
    return context


class EmergencyView(SafeExceptionMixin, LoginRequiredMixin, TemplateView):
  template_name = 'core/emergency.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    user = self.request.user
    context['full_name'] = user.full_name
    context['emailEmergency'] = user.emailEmergency
    context['emailAlternative'] = user.emailAlternative
    context['emergency_contact'] = user.emergency_contact
    context['alternative_contact'] = user.alternative_contact if user.alternative_contact else ''
    now = datetime.now()
    context['current_date'] = now.strftime('%d/%m/%Y')
    context['current_time'] = now.strftime('%H:%M')
    return context


@method_decorator(csrf_exempt, name='dispatch')
class SendAlertView(SafeExceptionMixin, LoginRequiredMixin, View):

  def post(self, request, *args, **kwargs):
    try:
      data = json.loads(request.body)
      lat = data.get('latitude')
      lng = data.get('longitude')
      user = request.user

      if not lat or not lng:
        return JsonResponse({'status': 'error', 'message': 'Ubicación no proporcionada.'}, status=400)

      maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"

      subject = f"¡ALERTA DE EMERGENCIA - {user.full_name} necesita ayuda!"
      body = f"""
            ¡ATENCIÓN! Se ha recibido una alerta de emergencia.

            Esta es una solicitud de ayuda urgente de:

            - Nombre: {user.full_name}
            - Ubicación en tiempo real: {maps_link}

            --- Información de Contacto ---
            - Contacto de Emergencia: {user.emergency_contact}
            - Email de Emergencia: {user.emailEmergency}
            - Contacto Alternativo: {user.alternative_contact or 'No registrado'}
            - Email Alternativo: {user.emailAlternative or 'No registrado'}

            La alerta fue enviada en la fecha y hora: {datetime.now().strftime('%d/%m/%Y - %H:%M:%S')}

            Por favor, contacte a la persona o a las autoridades de inmediato.
            """

      recipient_list = [user.emailEmergency]
      if user.emailAlternative:
        recipient_list.append(user.emailAlternative)

      send_mail(
        subject,
        body,
        settings.EMAIL_HOST_USER,
        recipient_list,
        fail_silently=False,
      )

      return JsonResponse({'status': 'success', 'message': 'Alerta enviada correctamente.'})

    except Exception as e:
      print(f"Error al enviar alerta: {e}")
      return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


class FeedbackView(SafeExceptionMixin, LoginRequiredMixin, FormView):
  template_name = 'core/feedback.html'
  form_class = UserFeedbackForm
  success_url = reverse_lazy('auth_api:core:home')

  def form_valid(self, form):
    feedback = form.save(commit=False)
    feedback.user = self.request.user
    feedback.save()
    return super().form_valid(form)


class TrainingModeView(SafeExceptionMixin, LoginRequiredMixin, TemplateView):
  template_name = 'core/training.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)

    exercises_queryset = TrainingExercise.objects.all().order_by('order')

    exercises_list = list(exercises_queryset.values('command_text', 'explanation_text'))

    context['exercises'] = exercises_list

    return context
