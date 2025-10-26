import traceback
import inspect
import os
from django.http import JsonResponse, HttpResponse, Http404
from django.contrib import messages
from django.shortcuts import render
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.response import TemplateResponse
from django.views import View
from django.conf import settings
from django.urls.exceptions import Resolver404, NoReverseMatch
from django.core.exceptions import PermissionDenied
from django.urls import resolve, reverse


class SafeExceptionMixin:

  def process_exception(self, request, exception):
    if isinstance(exception, (Http404, Resolver404)) or getattr(exception, 'status_code', None) == 404:
      context = {
        "code": 404,
        "title": "Página no encontrada",
        "message": "La ruta que intentas acceder no existe o ha sido eliminada. Por favor, verifica la URL o vuelve al inicio.",
        "is_4xx": True,
        "is_5xx": False,
      }
      return render(request, "errors.html", context=context, status=404)
    return None

  def _verify_url_exists(self, request):
    try:
      resolve(request.path_info)
      return True
    except Resolver404:
      context = {
        "code": 404,
        "title": "Ruta no encontrada",
        "message": "La página que intentas acceder no está configurada en el sistema. Por favor, verifica la URL.",
        "is_4xx": True,
        "is_5xx": False,
      }
      return render(request, "errors.html", context=context, status=404)
  
  def _check_view_file(self):
    try:
      file_path = inspect.getfile(self.__class__)
      
      if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        raise ValueError(f"El archivo de vista {file_path} está vacío o no existe")
      
      if isinstance(self, View):
        required_methods = ['get', 'post', 'put', 'delete', 'head', 'options', 'trace']
        has_any_method = any(hasattr(self, method) for method in required_methods)
        if not has_any_method:
          raise ValueError(f"La vista {self.__class__.__name__} no tiene ningún método HTTP definido")
          
      return True
    except Exception as e:
      return str(e)

  def _verify_related_files(self):
    try:
      module = inspect.getmodule(self.__class__)
      module_path = module.__file__
      dir_path = os.path.dirname(module_path)
      app_name = os.path.basename(dir_path)
      
      if app_name in ['core', 'auth_api']:
        critical_files = ['forms.py', 'models.py', 'urls.py']
        for file in critical_files:
          file_path = os.path.join(dir_path, file)
          if os.path.exists(file_path) and os.path.getsize(file_path) == 0:
            raise ValueError(f"El archivo {file} está vacío en la app {app_name}")
      
      elif app_name == 'intelligent_assistant':
        file_path = os.path.join(dir_path, 'urls.py')
        if os.path.exists(file_path) and os.path.getsize(file_path) == 0:
          raise ValueError("El archivo urls.py está vacío en la app intelligent_assistant")
          
      return True
    except Exception as e:
      return str(e)

  def dispatch(self, request, *args, **kwargs):
    try:
      url_check = self._verify_url_exists(request)
      if isinstance(url_check, TemplateResponse):
        return url_check

      view_check = self._check_view_file()
      if isinstance(view_check, str):
        context = {
          "code": 500,
          "title": "Error en archivo de vista",
          "message": f"Se detectó un problema en la vista: {view_check}",
          "is_4xx": False,
          "is_5xx": True,
        }
        return render(request, "errors.html", context=context, status=500)
      
      files_check = self._verify_related_files()
      if isinstance(files_check, str):
        context = {
          "code": 500,
          "title": "Error en archivos relacionados",
          "message": f"Se detectó un problema en archivos del sistema: {files_check}",
          "is_4xx": False,
          "is_5xx": True,
        }
        return render(request, "errors.html", context=context, status=500)

      response = super().dispatch(request, *args, **kwargs)

      try:
        if isinstance(response, TemplateResponse) and not response.is_rendered:
          response.render()
          
          if not response.content.strip():
            context = {
              "code": 404,
              "title": "Página vacía",
              "message": "La página que intentas ver está vacía. Por favor, verifica que el contenido exista.",
              "is_4xx": True,
              "is_5xx": False,
            }
            return render(request, "errors.html", context=context, status=404)
            
      except Exception:
        raise

      return response
    except Exception as e:
      tb = traceback.format_exc()
      print("\n" + "=" * 60)
      print(f"ERROR HANDLED in view {self.__class__.__name__}: {e}")
      print(f"Error Type: {type(e).__name__}")
      print(tb)
      print("=" * 60 + "\n")

      status_code = 500
      tech_details = str(e)

      if isinstance(e, Http404):
        status_code = 404
      elif isinstance(e, NoReverseMatch):
        status_code = 500
        error_msg = str(e)
        view_name = error_msg.split("'")[1] if "'" in error_msg else "desconocida"
        tech_details = f"Error en URL: No se pudo encontrar la ruta para '{view_name}'"
      elif isinstance(e, PermissionError):
        status_code = 403
      elif isinstance(e, (TemplateDoesNotExist, TemplateSyntaxError)):
        status_code = 500
        tech_details = f"Template Error: {str(e)}"
      elif isinstance(e, ImportError):
        status_code = 500
        tech_details = f"Import Error: {str(e)}"
      elif isinstance(e, SyntaxError):
        status_code = 500
        tech_details = f"Syntax Error: {str(e)}"
      elif isinstance(e, NameError):
        status_code = 500
        tech_details = f"Name Error: {str(e)}"
      elif isinstance(e, AttributeError):
        status_code = 500
        tech_details = f"Attribute Error: {str(e)}"
      elif isinstance(e, ValueError):
        status_code = 400
        tech_details = f"Value Error: {str(e)}"
      elif isinstance(e, TypeError):
        status_code = 500
        tech_details = f"Type Error: {str(e)}"
      
      print(f"\nTechnical Details for Developers:")
      print(f"Status Code: {status_code}")
      print(f"Error Type: {type(e).__name__}")
      print(f"Details: {tech_details}")
      print(f"File: {getattr(e, '__file__', 'N/A')}")
      print(f"Line: {getattr(e, 'lineno', 'N/A')}")
      if hasattr(e, 'filename'):
          print(f"File with error: {e.filename}")

      if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json":
        return JsonResponse({"error": "Ocurrió un error interno en el servidor."}, status=status_code)

      if status_code == 404:
        title = "Página no encontrada"
        message = "La página que buscas no existe o fue movida. Verifica la dirección o vuelve al inicio."
      elif status_code == 403:
        title = "Acceso denegado"
        message = "No tienes permiso para acceder a esta sección. Si crees que esto es un error, por favor contacta con soporte."
      elif status_code == 400:
        title = "Solicitud incorrecta"
        message = "Hubo un problema con la información enviada. Por favor verifica los datos e intenta nuevamente."
      elif isinstance(e, SyntaxError):
        title = "Error de sintaxis"
        message = "Estamos experimentando dificultades técnicas. Nuestro equipo ha sido notificado y estamos trabajando en ello."
      elif isinstance(e, ImportError):
        title = "Error de módulo"
        message = "Hay un problema con algunos componentes del sistema. El equipo técnico está trabajando para resolverlo."
      elif isinstance(e, (TemplateDoesNotExist, TemplateSyntaxError)):
        title = "Error de plantilla"
        message = "Hay un problema con la visualización de esta página. El equipo de desarrollo está trabajando en una solución."
      else:
        title = "Error interno"
        message = "Ocurrió un error inesperado. Nuestro equipo ha sido notificado y estamos trabajando para resolverlo."

      is_4xx = str(status_code).startswith('4')
      is_5xx = str(status_code).startswith('5')

      context = {
        "code": status_code,
        "title": title,
        "message": message,
        "is_4xx": is_4xx,
        "is_5xx": is_5xx,
      }

      try:
        return render(request, "errors.html", context=context, status=status_code)
      except Exception:
        print("Error rendering errors.html:")
        print(traceback.format_exc())
        return HttpResponse(f"Error {status_code}: {message}", status=status_code, content_type="text/plain")
