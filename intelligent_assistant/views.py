import base64
import json

import google.generativeai as genai
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from utils.safe_views import SafeExceptionMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView


@method_decorator(csrf_exempt, name='dispatch')
class TextReaderView(SafeExceptionMixin, LoginRequiredMixin, View):

  def get(self, request, *args, **kwargs):
    try:
      api_key = settings.GEMINI_API_KEY
      genai.configure(api_key=api_key)

      print("\n" + "=" * 60)
      print("MODELOS DISPONIBLES EN TU API:")
      print("=" * 60)

      models = genai.list_models()

      for model in models:
        if 'generateContent' in model.supported_generation_methods:
          print(f"\n✓ Nombre: {model.name}")
          print(f"  Display: {model.display_name}")
          print(f"  Métodos: {model.supported_generation_methods}")

      print("\n" + "=" * 60 + "\n")

    except Exception as e:
      print(f"ERROR listando modelos: {e}")

    return render(request, 'intelligent_assistant/text_reader.html')

  def post(self, request, *args, **kwargs):
    try:
      api_key = settings.GEMINI_API_KEY
      if not api_key:
        return JsonResponse({'error': 'La clave de API de Google no está configurada en settings.py.'}, status=500)

      genai.configure(api_key=api_key)

      data = json.loads(request.body)
      image_data = data.get('image_data')

      if not image_data or ';base64,' not in image_data:
        return JsonResponse({'error': 'No se proporcionaron datos de imagen válidos.'}, status=400)

      header, encoded = image_data.split(';base64,', 1)
      image_bytes = base64.b64decode(encoded)

      image_parts = [{"mime_type": "image/jpeg", "data": image_bytes}]

      prompt_text = (
        "Analiza esta imagen. Tu tarea es responder de la manera más concisa posible. "
        "Si la imagen contiene principalmente texto legible (como un cartel, un documento o una etiqueta), "
        "extrae y devuelve ÚNICAMENTE el texto que ves, sin añadir ninguna palabra introductoria. "
        "Si la imagen contiene símbolos, dibujos, objetos, personas o una escena, "
        "describe brevemente lo que ves en la imagen, como si se lo explicaras a una persona ciega. "
        "No incluyas formatos como markdown."
      )

      model = genai.GenerativeModel('gemini-2.5-flash')

      response = model.generate_content([prompt_text, image_parts[0]])

      if response and response.text:
        return JsonResponse({'text': response.text.strip()})
      else:
        return JsonResponse({'text': 'No se pudo obtener una respuesta de la IA.'})

    except Exception as e:
      print(f"Error en TextReaderView: {e}")
      return JsonResponse({'error': f'Ocurrió un error en el servidor: {str(e)}'}, status=500)


class ObstacleDetectionView(SafeExceptionMixin, LoginRequiredMixin, TemplateView):
  template_name = 'intelligent_assistant/obstacle_detection.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['page_title'] = "Detección de Obstáculos"
    return context
