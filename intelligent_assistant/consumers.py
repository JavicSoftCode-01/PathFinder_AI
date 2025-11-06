import base64
import json
import threading
import time
from collections import Counter

import cv2
import numpy as np
from channels.generic.websocket import WebsocketConsumer
from django.conf import settings
from ultralytics import YOLO

try:
  yolo_model = YOLO('intelligent_assistant/IA_models/yolov8m-seg.pt')

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
    self.gemini_call_interval = 7
    self.is_gemini_processing = False

    self.last_instruction_sent = ""
    self.last_yolo_instruction = ""
    self.instruction_repeat_count = 0
    self.max_repeats_before_silence = 2

    self.yolo_frame_buffer = []
    self.max_buffer_size = 7
    
    self.frame_images_buffer = []  

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
    yolo_detections = self.process_yolo_results(results, frame_width, frame_height)

    self.yolo_frame_buffer.append(yolo_detections)
    self.frame_images_buffer.append(image_bytes)

    if len(self.yolo_frame_buffer) > self.max_buffer_size:
      self.yolo_frame_buffer.pop(0)
      self.frame_images_buffer.pop(0)

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
    if (not self.is_gemini_processing and
        len(self.yolo_frame_buffer) >= self.max_buffer_size and
        len(self.frame_images_buffer) >= self.max_buffer_size and
        (current_time - self.last_gemini_call_time > self.gemini_call_interval)):

      self.is_gemini_processing = True
      self.last_gemini_call_time = current_time

      accumulated_summary = self.create_accumulated_summary()

      most_recent_frame = self.frame_images_buffer[-1]

      threading.Thread(
        target=self.get_gemini_analysis,
        args=(most_recent_frame, accumulated_summary)
      ).start()

  def create_accumulated_summary(self):
    all_objects = []
    zone_counters = {"left": 0, "center": 0, "right": 0}

    for detection in self.yolo_frame_buffer:
      for obj in detection['objects']:
        all_objects.append(f"{obj['label']} en {obj['zone']}")

      if detection['zones']['left']:
        zone_counters['left'] += 1
      if detection['zones']['center']:
        zone_counters['center'] += 1
      if detection['zones']['right']:
        zone_counters['right'] += 1

    object_frequency = Counter(all_objects)
    most_common = object_frequency.most_common(7)

    summary_parts = []

    if most_common:
      summary_parts.append("Objetos detectados en los últimos 7 frames:")
      for obj, count in most_common:
        if count >= 3:  
          summary_parts.append(f"  - {obj} (detectado {count} de 7 veces)")

    zone_info = []
    if zone_counters['center'] >= 4:
      zone_info.append("CENTRO bloqueado persistentemente")
    if zone_counters['left'] >= 4:
      zone_info.append("IZQUIERDA bloqueada")
    if zone_counters['right'] >= 4:
      zone_info.append("DERECHA bloqueada")

    if zone_info:
      summary_parts.append("\nZonas comprometidas en el periodo:")
      summary_parts.extend([f"  - {z}" for z in zone_info])

    if not summary_parts:
      return "No se detectaron objetos significativos en los últimos 7 frames"

    return "\n".join(summary_parts)

  def get_gemini_analysis(self, image_bytes, accumulated_summary):
    print(f"\n{'=' * 60}")
    print("🔍 ANÁLISIS GEMINI - FRAME ACTUAL DEL USUARIO")
    print(f"{'=' * 60}")
    print(f"Contexto histórico (últimos 7 frames):\n{accumulated_summary}")
    print(f"{'=' * 60}\n")

    try:
      image_parts = [{"mime_type": "image/jpeg", "data": image_bytes}]

      prompt = f"""Eres un asistente de navegación en tiempo real para personas no videntes. Tu misión es guiar basándote en lo que el usuario está viendo AHORA.

CONTEXTO HISTÓRICO (últimos 1-2 segundos):
{accumulated_summary}

⚠️ IMPORTANTE: El contexto histórico es solo referencia. Tu instrucción debe basarse en la imagen ACTUAL que el usuario está viendo en este momento.

ANÁLISIS VISUAL REQUERIDO:
Analiza la imagen ACTUAL desde una perspectiva frontal a altura del pecho.

INSTRUCCIONES DE NAVEGACIÓN:
1. **Prioriza la seguridad inmediata**: Analiza lo que hay AHORA frente al usuario.

2. **Distingue entre pasado y presente**:
   - ❌ NO menciones objetos del contexto histórico si no están en la imagen actual
   - ✅ Si un objeto del historial YA NO está presente, el usuario ya lo superó
   - ✅ Enfócate en obstáculos NUEVOS o ACTUALES en la imagen

3. **Estructura de respuesta**:
   - ACCIÓN primero: "Detente", "Gira a la derecha", "Gira a la izquierda", "Avanza"
   - Razón ACTUAL: describe solo lo que ves EN LA IMAGEN AHORA
   
4. **Casos específicos**:
   - Si la imagen muestra camino libre pero el historial tenía obstáculos → "Camino despejado, avanza"
   - Si la imagen muestra un obstáculo nuevo → Instrúyelo sobre el obstáculo ACTUAL
   - Si la imagen muestra una pared/barrera → "Pared al frente, gira [dirección]"

5. **Camino despejado**: Di "Camino despejado, avanza" si la imagen ACTUAL no muestra riesgos.

6. **Precisión espacial**:
   - Usa "izquierda/derecha/centro/adelante" según la imagen ACTUAL
   - Indica distancia aproximada si es crítico

EJEMPLOS CORRECTOS:
✅ Historial: "Mesa centro (7/7)" | Imagen actual: pared clara
   → "Camino despejado, avanza"

✅ Historial: "Despejado" | Imagen actual: persona cruzando
   → "Detente. Persona cruzando adelante"

✅ Historial: "Silla izquierda (5/7)" | Imagen actual: pasillo vacío
   → "Camino despejado, continúa"

✅ Historial: "Despejado" | Imagen actual: escalera
   → "Alto. Escalera descendiendo al frente"

❌ INCORRECTO:
   Historial: "Mesa centro (7/7)" | Imagen actual: pasillo vacío
   → "Desvíate de la mesa" ← ¡NO! El usuario ya pasó la mesa

FORMATO DE RESPUESTA:
- Máximo 2 oraciones
- Sin markdown, sin asteriscos
- Basado en la imagen ACTUAL
- Tono directo y accionable

Responde SOLO con la instrucción basada en lo que ves EN LA IMAGEN ACTUAL:"""

      response = gemini_model.generate_content(
        [prompt, image_parts[0]],
        request_options={"timeout": 20}
      )

      if response and response.text:
        gemini_instruction = response.text.strip()
        gemini_instruction = gemini_instruction.replace('**', '').replace('*', '')

        print(f"✅ INSTRUCCIÓN GEMINI (sobre imagen ACTUAL): '{gemini_instruction}'\n")

        self.last_yolo_instruction = gemini_instruction
        self.instruction_repeat_count = 0

        self.send(text_data=json.dumps({
          'instruction': gemini_instruction,
          'zones': self.yolo_frame_buffer[-1]["zones"],
          'from_gemini': True
        }))
      else:
        print("⚠️ Gemini no devolvió texto válido.")

    except Exception as e:
      print(f"❌ Error en Gemini API: {e}")
    finally:
      self.is_gemini_processing = False

      self.yolo_frame_buffer.clear()
      self.frame_images_buffer.clear()

  def process_yolo_results(self, results, frame_width, frame_height):
    zone_width = frame_width / 3
    detections = {
      "objects": [],
      "zones": {"left": False, "center": False, "right": False},
      "confidence_avg": 0.0,
      "total_detections": 0
    }

    confidences = []

    for r in results:
      for box in r.boxes:
        x1, y1, x2, y2 = box.xyxy[0]
        cls_id = int(box.cls[0])
        confidence = float(box.conf[0])
        label = yolo_model.names[cls_id]

        confidences.append(confidence)

        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2

        obj_area = (x2 - x1) * (y2 - y1)
        frame_area = frame_width * frame_height
        area_percentage = (obj_area / frame_area) * 100

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

        detections["objects"].append({
          "label": label,
          "zone": zone,
          "confidence": round(confidence, 2),
          "area_pct": round(area_percentage, 1),
          "position": "alto" if cy < frame_height / 3 else "medio" if cy < 2 * frame_height / 3 else "bajo"
        })

    detections["total_detections"] = len(confidences)
    if confidences:
      detections["confidence_avg"] = round(sum(confidences) / len(confidences), 2)

    return detections

  def generate_yolo_instruction(self, detections):
    if detections["zones"]["center"]:
      center_objects = [obj for obj in detections['objects'] if obj['zone'] == 'centro']
      if center_objects and any(obj['area_pct'] > 15 for obj in center_objects):
        return "Obstáculo grande al frente, precaución."
      return "Obstáculo al frente."

    if not detections["zones"]["center"] and (detections["zones"]["left"] or detections["zones"]["right"]):
      return "Centro libre, avanza."

    return "Despejado."

  def send_error_message(self, message):
    self.send(text_data=json.dumps({
      'instruction': message,
      'zones': {"left": False, "center": False, "right": False},
      'error': True
    }))