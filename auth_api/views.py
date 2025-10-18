from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView

from auth_api.forms import CustomUserCreationForm
from auth_api.models import CustomUser


class RegisterView(CreateView):
  model = CustomUser
  form_class = CustomUserCreationForm
  template_name = "auth/register.html"
  success_url = reverse_lazy("login")

  def form_valid(self, form):
    messages.success(self.request, "Cuenta creada exitosamente. Ahora puedes iniciar sesión.")
    return super().form_valid(form)

  def form_invalid(self, form):
    if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
      field_name = list(self.request.POST.keys())[0]
      if field_name in form.errors:
        return JsonResponse({field_name: "invalid"})
      return JsonResponse({field_name: "valid"})
    return super().form_invalid(form)

  def post(self, request, *args, **kwargs):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
      form = self.form_class(request.POST)
      form.is_valid()
      field_name = list(request.POST.keys())[0]
      if field_name in form.errors:
        return JsonResponse({field_name: "invalid"})
      return JsonResponse({field_name: "valid"})
    return super().post(request, *args, **kwargs)


class CustomLoginView(LoginView):
  template_name = "auth/login.html"

  def get_success_url(self):
    return reverse_lazy("auth_api:core:home")


class CustomLogoutView(LogoutView):
  next_page = reverse_lazy("auth_api:login")

  def dispatch(self, request, *args, **kwargs):
    messages.info(request, "Sesión cerrada correctamente.")
    return super().dispatch(request, *args, **kwargs)
