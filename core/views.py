from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class HomeView(LoginRequiredMixin, TemplateView):
  template_name = 'core/home.html'

  def get(self, request, *args, **kwargs):
    if not request.session.get('welcome_shown', False):
      messages.success(request, f"Bienvenido {request.user.full_name} 👋")
      request.session['welcome_shown'] = True
    return super().get(request, *args, **kwargs)

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    first_name = self.request.user.full_name.split()[0] if self.request.user.full_name else 'Usuario'
    context['user_name'] = first_name
    return context


class EmergencyView(LoginRequiredMixin, TemplateView):
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
