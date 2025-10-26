from django.shortcuts import render
from django.urls import resolve, Resolver404, NoReverseMatch
from django.conf import settings
from django.urls.exceptions import NoReverseMatch

class CustomErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def process_view(self, request, view_func, view_args, view_kwargs):
        try:
            return None
        except NoReverseMatch as e:
            return self.handle_no_reverse_match(request, e)
        except Exception:
            return None

    def handle_no_reverse_match(self, request, exception):
        error_msg = str(exception)
        view_name = error_msg.split("'")[1] if "'" in error_msg else "desconocida"
        
        context = {
            "code": 500,
            "title": "Error en la configuración de URLs",
            "message": f"La ruta '{view_name}' no está configurada correctamente. Por favor, contacta al administrador.",
            "is_4xx": False,
            "is_5xx": True,
            "technical_details": str(exception) if settings.DEBUG else None
        }
        return render(request, "errors.html", context=context, status=500)

    def __call__(self, request):
        try:
            resolve(request.path_info)
            try:
                response = self.get_response(request)
                return response
            except NoReverseMatch as e:
                return self.handle_no_reverse_match(request, e)
        except Resolver404:
            context = {
                "code": 404,
                "title": "Ruta no encontrada",
                "message": "La página que intentas acceder ya no existe o ha sido movida. Por favor, verifica la URL.",
                "is_4xx": True,
                "is_5xx": False,
            }
            return render(request, "errors.html", context=context, status=404)
        except Exception as e:
            if not settings.DEBUG:
                context = {
                    "code": 500,
                    "title": "Error del servidor",
                    "message": "Ha ocurrido un error inesperado. Por favor, intenta nuevamente más tarde.",
                    "is_4xx": False,
                    "is_5xx": True,
                }
                return render(request, "errors.html", context=context, status=500)
            raise  