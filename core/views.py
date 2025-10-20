from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from .forms import UserFeedbackForm
from .models import TrainingExercise


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


class FeedbackView(LoginRequiredMixin, FormView):
  template_name = 'core/feedback.html'
  form_class = UserFeedbackForm
  success_url = reverse_lazy('auth_api:core:home')

  def form_valid(self, form):
    feedback = form.save(commit=False)
    feedback.user = self.request.user
    feedback.save()
    return super().form_valid(form)


class TrainingModeView(LoginRequiredMixin, TemplateView):
  template_name = 'core/training.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)

    exercises_queryset = TrainingExercise.objects.all().order_by('order')

    exercises_list = list(exercises_queryset.values('command_text', 'explanation_text'))

    context['exercises'] = exercises_list

    return context
