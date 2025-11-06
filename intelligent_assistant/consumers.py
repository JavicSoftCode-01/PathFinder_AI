import base64
import json
import threading
import time
from uuid import uuid4

import boto3
import cv2
import numpy as np
from botocore.exceptions import BotoCoreError, ClientError
from channels.generic.websocket import WebsocketConsumer
from django.conf import settings
from ultralytics import YOLO

try:
  yolo_model = YOLO('intelligent_assistant/IA_models/yolov8m-seg.pt')
  import google.generativeai as genai

  genai.configure(api_key=settings.GEMINI_API_KEY)
  gemini_model = genai.GenerativeModel('gemini-flash-lite-latest') 

  print("✅ Modelos de IA cargados correctamente:")
  print("   - YOLOv8m-seg (Detección de objetos)")
  print("   - Gemini 1.5 Flash (Análisis contextual)")

except Exception as e:
  print(f"❌ ERROR CRÍTICO: No se pudieron cargar los modelos de IA. {e}")
  yolo_model = None
  gemini_model = None


def upload_frame_to_s3(image_bytes: bytes, filename_prefix: str = "frames") -> str:
  bucket = settings.AWS_STORAGE_BUCKET_NAME
  region = getattr(settings, "AWS_S3_REGION_NAME", None)
  filename = f"{filename_prefix}/{uuid4().hex}_{int(time.time())}.jpg"

  s3_client = boto3.client(
    "s3",
    aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
    aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
    region_name=region
  )

  try:
    s3_client.put_object(
      Bucket=bucket,
      Key=filename,
      Body=image_bytes,
      ContentType='image/jpeg',
    )
  except (BotoCoreError, ClientError) as e:
    raise RuntimeError(f"Error subiendo a S3: {e}")

  domain = getattr(settings, "AWS_S3_CUSTOM_DOMAIN", f"{bucket}.s3.amazonaws.com")
  url = f"https://{domain}/{filename}"
  return url


class ObstacleConsumer(WebsocketConsumer):
  def connect(self):
    self.accept()
    self.frame_batch_buffer = []
    self.is_gemini_processing = False
    print("Cliente WebSocket conectado.")

  def disconnect(self, close_code):
    print("Cliente WebSocket desconectado.")

  def receive(self, text_data):
    if not yolo_model or not gemini_model:
      self.send_error_message("Los servicios de IA no están disponibles.")
      return

    data = json.loads(text_data)
    image_data = data.get('image')
    if not image_data:
      return

    try:
      header, encoded = image_data.split(",", 1)
      image_bytes = base64.b64decode(encoded)
      np_arr = np.frombuffer(image_bytes, dtype=np.uint8)
      image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    except Exception as e:
      print(f"❌ Error decodificando la imagen: {e}")
      return

    self.frame_batch_buffer.append(image_bytes)

    if len(self.frame_batch_buffer) >= 3 and not self.is_gemini_processing:
      self.is_gemini_processing = True

      context_frames_bytes = self.frame_batch_buffer[:2]
      verification_frame_bytes = self.frame_batch_buffer[2]

      self.frame_batch_buffer.clear()

      threading.Thread(
        target=self.process_frames_for_gemini,
        args=(context_frames_bytes, verification_frame_bytes)
      ).start()

  def process_frames_for_gemini(self, context_frames_bytes, verification_frame_bytes):
    yolo_context_data = []
    for frame_bytes in context_frames_bytes:
        np_arr = np.frombuffer(frame_bytes, dtype=np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        results = yolo_model(image, verbose=False)
        frame_height, frame_width, _ = image.shape
        yolo_detections = self.process_yolo_results(results, frame_width, frame_height)
        yolo_context_data.append(yolo_detections)

    yolo_context_text = self.format_yolo_context(yolo_context_data)
    
    self.get_gemini_analysis(verification_frame_bytes, yolo_context_text)


  def format_yolo_context(self, yolo_data_list):
    context_parts = []
    for i, detections in enumerate(yolo_data_list, 1):
      if not detections['objects']:
        context_parts.append(f"Contexto Frame {i}: No se detectaron objetos.")
      else:
        objects_by_zone = {'izquierda': [], 'centro': [], 'derecha': []}
        for obj in detections['objects']:
          if obj['zone'] in objects_by_zone:
            objects_by_zone[obj['zone']].append(obj['label'])
        
        desc = f"Contexto Frame {i}: "
        zone_descs = []
        for zone, labels in objects_by_zone.items():
          if labels:
            zone_descs.append(f"en la {zone} hay {', '.join(set(labels))}")
        
        if not zone_descs:
            desc += "sin objetos claros en las zonas."
        else:
            desc += "; ".join(zone_descs) + "."
        context_parts.append(desc)
    
    return "\n".join(context_parts)

  def get_gemini_analysis(self, image_bytes, yolo_context):
    print(f"\n{'=' * 60}\n🔮 Disparando análisis con Gemini...\nContexto YOLO:\n{yolo_context}\n{'=' * 60}")

    try:
      s3_url = None
      try:
        s3_url = upload_frame_to_s3(image_bytes)
        print(f"📤 Frame de verificación en S3: {s3_url}")
      except Exception as e:
        print(f"⚠️ No se pudo subir frame a S3: {e}")

      image_part = {"mime_type": "image/jpeg", "data": image_bytes}
      prompt = f"""
            Eres un asistente de guía para una persona con discapacidad visual. Tu única función es dar una instrucción de navegación corta, clara y directa.

            **Información Recibida:**
            1.  **Contexto de YOLO:** Objetos detectados en 2 frames anteriores. Úsalo para entender la escena que conduce a este momento.
            2.  **Fotograma Actual:** La imagen que el usuario ve ahora mismo. Tu instrucción DEBE basarse en esta imagen, usando el contexto solo como referencia.

            **Contexto YOLO (Frames Anteriores):**
            {yolo_context}

            **REGLAS OBLIGATORIAS:**
            1.  **Formato Estricto:** Tu respuesta DEBE ser `Instrucción, [contexto breve]`. Sin excepciones.
            2.  **Brevedad:** La respuesta completa no debe superar las 10 palabras.
            3.  **Directo al Punto:** No saludes, no expliques, no uses frases como "Basado en el análisis". Responde ÚNICAMENTE con la instrucción.
            4.  **Prioriza la Seguridad:** La instrucción debe advertir sobre el peligro más inmediato y relevante en el **Fotograma Actual**.

            **Ejemplos de Respuestas CORRECTAS:**
            *   Gire a la derecha, pared al frente.
            *   Gire a la izquierda, silla en centro.
            *   Cuidado con el altillo.
            *   Cuidado con las escaleras, suba con cuidado.
            *   Cuidado con la persona del centro.
            *   Cuidado puerta cerrada al frente, la manija está del lado izquierdo.
            *   Avance con cuidado, desnivel en el suelo.
            *   Alerta, posible hueco a la derecha.

            **Situaciones de URGENCIA (Máxima Prioridad):**
            - **Obstáculo Total (pared, puerta, objeto grande):** Si el **Fotograma Actual** muestra un bloqueo total, indica una vía de escape. Ejemplo: "Gire a la derecha, pared al frente".
            - **Peligros Graves (escaleras, huecos, desniveles, ascensores):** Tu instrucción debe centrarse en ese peligro específico. Ejemplo: "Cuidado con las escaleras, suba con cuidado".

            Analiza el **Fotograma Actual** para confirmar el peligro real y da la instrucción más segura para este preciso momento.

            **INSTRUCCIÓN:**
            """

      response = gemini_model.generate_content(
        [prompt, image_part],
        request_options={"timeout": 15} 
      )

      if response and response.text:
        gemini_instruction = response.text.strip().replace('*', '').replace('\n', ' ')
        print(f"✅ Instrucción de Gemini: '{gemini_instruction}'")

        payload = {
          'instruction': gemini_instruction,
          'from_gemini': True, 
        }
        if s3_url:
          payload['frame_s3_url'] = s3_url

        self.send(text_data=json.dumps(payload))
      else:
        print("⚠️ Gemini no devolvió una respuesta válida.")
        self.send_error_message("Análisis no disponible.")

    except Exception as e:
      print(f"❌ Error en la llamada a Gemini: {e}")
      self.send_error_message("Error en el análisis. Reintentando.")
    finally:
      self.is_gemini_processing = False

  def process_yolo_results(self, results, frame_width, frame_height):
    zone_width = frame_width / 3
    detections = {"objects": []}
    for r in results:
      for box in r.boxes:
        x1, _, x2, _ = box.xyxy[0]
        cls_id = int(box.cls[0])
        label = yolo_model.names[cls_id]
        cx = (x1 + x2) / 2
        zone = "centro"
        if cx < zone_width:
          zone = "izquierda"
        elif cx > 2 * zone_width:
          zone = "derecha"
        detections["objects"].append({"label": label, "zone": zone})
    return detections

  def send_error_message(self, message):
    self.send(text_data=json.dumps({'instruction': message, 'error': True, 'from_gemini': True}))