import traceback

from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import CreateView

from auth_api.forms import CustomUserCreationForm
from auth_api.models import CustomUser
from auth_api.utils.validators import Validation
from utils.safe_views import SafeExceptionMixin


@method_decorator(never_cache, name='dispatch')
class RegisterView(SafeExceptionMixin, CreateView):
  model = CustomUser
  form_class = CustomUserCreationForm
  template_name = "auth/register.html"
  success_url = reverse_lazy("auth_api:login")

  def form_valid(self, form):
    messages.success(self.request, "Cuenta creada exitosamente. Ahora puedes iniciar sesión.")
    return super().form_valid(form)

  def form_invalid(self, form):
    if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
      field_name = list(self.request.POST.keys())[1]
      if field_name in form.errors:
        return JsonResponse({field_name: "invalid", "error": form.errors[field_name][0]})
      return JsonResponse({field_name: "valid"})

    for field, errors in form.errors.items():
      if field == '__all__':
        messages.error(self.request, errors[0])
      else:
        field_label = form.fields[field].label or field
        messages.error(self.request, f"{field_label}: {errors[0]}")

    return super().form_invalid(form)

  def post(self, request, *args, **kwargs):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
      field_name = None
      for key in request.POST.keys():
        if key != 'csrfmiddlewaretoken':
          field_name = key
          break

      if not field_name:
        return JsonResponse({"error": "No se especificó un campo"}, status=400)

      field_value = request.POST.get(field_name, '').strip()

      print(f"\n{'=' * 50}")
      print(f"Campo: {field_name}")
      print(f"Valor recibido: '{field_value}'")
      print(f"Longitud: {len(field_value)}")
      print(f"{'=' * 50}\n")

      optional_fields = {'alternative_contact', 'emailAlternative'}

      if not field_value and field_name not in optional_fields:
        return JsonResponse({field_name: "invalid", "error": "Este campo es requerido"})

      if field_name in optional_fields and not field_value:
        return JsonResponse({field_name: "valid"})

      try:
        if field_name == 'full_name':
          print(f"Validando full_name...")
          result = Validation.validate_full_name(field_value)
          print(f"Resultado validación: {result}")

        elif field_name == 'email':
          print(f"Validando email...")
          validated_email = Validation.validate_email(field_value)
          if CustomUser.objects.filter(email=validated_email).exists():
            return JsonResponse({field_name: "invalid", "error": "Este correo ya está registrado"})

        elif field_name == 'emailEmergency':
          print(f"Validando emailEmergency...")
          Validation.validate_email(field_value)

        elif field_name == 'emailAlternative':
          print(f"Validando emailAlternative...")
          Validation.validate_email(field_value)

        elif field_name == 'emergency_contact':
          print(f"Validando emergency_contact...")
          Validation.validate_phone_number(field_value)

        elif field_name == 'alternative_contact':
          if field_value:
            print(f"Validando alternative_contact...")
            Validation.validate_phone_number(field_value)

        elif field_name == 'age':
          print(f"Validando age...")
          if not field_value.isdigit():
            return JsonResponse({field_name: "invalid", "error": "Ingrese un número válido"})
          Validation.validate_age(int(field_value))

        elif field_name == 'password1':
          print(f"Validando password1...")
          if len(field_value) < 8:
            return JsonResponse({field_name: "invalid", "error": "La contraseña debe tener al menos 8 caracteres"})

          if field_value.isdigit():
            return JsonResponse({field_name: "invalid", "error": "La contraseña no puede ser completamente numérica"})

          email_field = request.POST.get('email', '')
          if not email_field:
            email_input = None
          else:
            email_input = email_field

          if email_input:
            email_base = email_input.split('@')[0].lower()
            password_lower = field_value.lower()
            if email_base in password_lower or password_lower in email_base:
              return JsonResponse(
                {field_name: "invalid", "error": "La contraseña es muy similar al correo electrónico"})

        elif field_name == 'password2':
          print(f"Validando password2...")
          password1 = request.POST.get('password1', '')
          print(f"Password1 recibido: '{password1}'")
          print(f"Password2 recibido: '{field_value}'")
          print(f"¿Son iguales?: {field_value == password1}")

          if not password1:
            return JsonResponse({field_name: "invalid", "error": "Primero ingrese la contraseña"})
          if field_value != password1:
            return JsonResponse({field_name: "invalid", "error": "Las contraseñas no coinciden"})

        print(f"✓ Validación exitosa para {field_name}")
        return JsonResponse({field_name: "valid"})

      except ValidationError as e:
        if hasattr(e, 'messages') and e.messages:
          error_message = e.messages[0]
        elif hasattr(e, 'message'):
          error_message = e.message
        else:
          error_message = str(e)

        if isinstance(error_message, list):
          error_message = error_message[0]

        print(f"✗ ValidationError: {error_message}")
        print(f"✗ Tipo de error: {type(e)}")
        print(f"✗ Dir del error: {dir(e)}")
        return JsonResponse({field_name: "invalid", "error": error_message})

      except Exception as e:
        print(f"✗ Exception: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({field_name: "invalid", "error": str(e)})

    return super().post(request, *args, **kwargs)

  def dispatch(self, request, *args, **kwargs):
    if request.user.is_authenticated:
      return redirect(self.get_success_url())
    return super().dispatch(request, *args, **kwargs)

  def get_success_url(self):
    return reverse_lazy("auth_api:core:home")


@method_decorator(never_cache, name='dispatch')
class CustomLoginView(SafeExceptionMixin, LoginView):
  template_name = "auth/login.html"

  def dispatch(self, request, *args, **kwargs):
    if request.user.is_authenticated:
      return redirect(self.get_success_url())
    return super().dispatch(request, *args, **kwargs)

  def get_success_url(self):
    return reverse_lazy("auth_api:core:home")

  def form_invalid(self, form):
    form.errors.clear()
    form._errors = {}

    messages.error(self.request, "Credenciales inválidas")
    return self.render_to_response(self.get_context_data(form=form))


class CustomLogoutView(SafeExceptionMixin, LogoutView):
  next_page = reverse_lazy("auth_api:login")

  def dispatch(self, request, *args, **kwargs):
    messages.info(request, "Sesión cerrada correctamente.")
    return super().dispatch(request, *args, **kwargs)
