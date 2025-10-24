import base64
import json
import threading
import time

import cv2
import numpy as np
from channels.generic.websocket import WebsocketConsumer
from django.conf import settings
from ultralytics import YOLO

try:
  yolo_model = YOLO('yolov8n.pt')

  import google.generativeai as genai

  genai.configure(api_key=settings.GEMINI_API_KEY)
  gemini_model = genai.GenerativeModel('gemini-flash-latest')
  print("Modelos YOLOv8 y Gemini cargados exitosamente.")

except Exception as e:
  print(f"ERROR CRÍTICO: No se pudieron cargar los modelos de IA. {e}")
  yolo_model = None
  gemini_model = None


class ObstacleConsumer(WebsocketConsumer):

  def connect(self):
    self.accept()
    self.last_gemini_call_time = 0
    self.gemini_call_interval = 15
    self.is_gemini_processing = False
    self.last_instruction_sent = ""
    self.last_yolo_instruction = ""
    self.instruction_repeat_count = 0
    self.max_repeats_before_silence = 2

  def disconnect(self, close_code):
    pass

  def receive(self, text_data):
    if not yolo_model or not gemini_model:
      self.send_error_message("Los servicios de IA no están disponibles.")
      return

    data = json.loads(text_data)
    image_data = data['image']

    try:
      header, encoded = image_data.split(",", 1)
      image_bytes = base64.b64decode(encoded)
      np_arr = np.frombuffer(image_bytes, dtype=np.uint8)
      image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    except Exception as e:
      print(f"Error decodificando imagen: {e}")
      return

    results = yolo_model(image, verbose=False)
    frame_height, frame_width, _ = image.shape
    yolo_detections = self.process_yolo_results(results, frame_width)

    yolo_instruction = self.generate_yolo_instruction(yolo_detections)

    should_send_instruction = False

    if yolo_instruction != self.last_yolo_instruction:
      self.last_yolo_instruction = yolo_instruction
      self.instruction_repeat_count = 0
      should_send_instruction = True
    elif self.instruction_repeat_count < self.max_repeats_before_silence:
      self.instruction_repeat_count += 1
      should_send_instruction = True

    response_data = {
      'zones': yolo_detections["zones"],
      'silent': not should_send_instruction
    }

    if should_send_instruction:
      response_data['instruction'] = yolo_instruction

    self.send(text_data=json.dumps(response_data))

    current_time = time.time()
    if not self.is_gemini_processing and (current_time - self.last_gemini_call_time > self.gemini_call_interval):
      self.is_gemini_processing = True
      self.last_gemini_call_time = current_time
      threading.Thread(target=self.get_gemini_analysis, args=(image_bytes, yolo_detections)).start()

  def get_gemini_analysis(self, image_bytes, yolo_detections):
    print("Iniciando análisis profundo con Gemini...")
    try:
      image_parts = [{"mime_type": "image/jpeg", "data": image_bytes}]

      yolo_summary = ", ".join([obj['label'] for obj in yolo_detections['objects']])
      if not yolo_summary: yolo_summary = "ninguno"

      prompt = f"""
            Eres un asistente de navegación para una persona no vidente. Tu único objetivo es la seguridad y la claridad.
            Analiza la imagen desde una perspectiva de cámara frontal a la altura del pecho.
            Ya he detectado los siguientes objetos con un modelo rápido: {yolo_summary}.

            Tu tarea es proporcionar UNA SOLA instrucción de navegación verbal, corta, clara y accionable.
            - Describe el entorno general SÓLO si es relevante para la navegación (ej. "Estás en una acera estrecha").
            - Prioriza el obstáculo más inminente o el camino más seguro.
            - Sé directo. Empieza con la acción: "Gira a la derecha", "Detente", "Sigue de frente con cuidado".
            - Si ves una pared, muro, o estructura sólida que bloquea completamente el paso, indícalo claramente como "Pared al frente, no hay paso" o "Camino bloqueado por muro".
            - Si el camino está REALMENTE despejado y no hay obstáculos relevantes, di simplemente "Camino despejado, puede avanzar".
            - Distingue entre objetos que se pueden esquivar y barreras físicas infranqueables.

            Ejemplos de buenas respuestas:
            - "Camino despejado, avanza."
            - "Detente, una persona está cruzando frente a ti."
            - "Gira ligeramente a la izquierda para esquivar un poste."
            - "Pared al frente, no hay paso. Gira atrás."
            - "Muro bloqueando, busca otra ruta."
            - "Sigue por la derecha, hay una bicicleta estacionada a tu izquierda."
            - "Escalera descendiendo, precaución al frente."

            No uses markdown. No saludes. Da únicamente la instrucción.
            """

      response = gemini_model.generate_content([prompt, image_parts[0]], request_options={"timeout": 20})

      if response and response.text:
        gemini_instruction = response.text.strip()
        print(f"Instrucción de Gemini: '{gemini_instruction}'")

        self.last_yolo_instruction = gemini_instruction
        self.instruction_repeat_count = 0

        self.send(text_data=json.dumps({
          'instruction': gemini_instruction,
          'zones': yolo_detections["zones"],
          'from_gemini': True
        }))
      else:
        print("Gemini no devolvió texto.")

    except Exception as e:
      print(f"Error en la llamada a la API de Gemini: {e}")
    finally:
      self.is_gemini_processing = False

  def process_yolo_results(self, results, frame_width):
    zone_width = frame_width / 3
    detections = {
      "objects": [],
      "zones": {"left": False, "center": False, "right": False}
    }
    for r in results:
      for box in r.boxes:
        x1, y1, x2, y2 = box.xyxy[0]
        cls_id = int(box.cls[0])
        label = yolo_model.names[cls_id]
        cx = (x1 + x2) / 2
        zone = ""
        if cx < zone_width:
          detections["zones"]["left"] = True
          zone = "izquierda"
        elif cx > 2 * zone_width:
          detections["zones"]["right"] = True
          zone = "derecha"
        else:
          detections["zones"]["center"] = True
          zone = "centro"
        detections["objects"].append({"label": label, "zone": zone})
    return detections

  def generate_yolo_instruction(self, detections):
    if detections["zones"]["center"]:
      return "Obstáculo al frente."
    if not detections["zones"]["center"] and (detections["zones"]["left"] or detections["zones"]["right"]):
      return "Centro libre."
    return "Despejado."

  def send_error_message(self, message):
    self.send(text_data=json.dumps({
      'instruction': message,
      'zones': {"left": False, "center": False, "right": False},
      'error': True
    }))
