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
