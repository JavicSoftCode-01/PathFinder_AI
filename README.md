# PathFinder AI 🌟

PathFinder AI es una aplicación web innovadora diseñada para asistir a personas con discapacidad visual, integrando tecnologías de inteligencia artificial y reconocimiento de voz para mejorar su experiencia de navegación y accesibilidad.

## 🚀 Características Principales

- **Sistema de Autenticación Seguro**
  - Registro y login con reconocimiento de voz
  - Validación de usuarios
  - Gestión de sesiones seguras

- **Asistente Inteligente**
  - Detección de obstáculos en tiempo real
  - Lector de texto integrado
  - Sistema de retroalimentación por voz

- **Módulo de Entrenamiento**
  - Ejercicios de entrenamiento personalizados
  - Sistema de emergencia
  - Seguimiento de progreso

- **Interfaz Accesible**
  - Diseño responsivo
  - Compatibilidad con lectores de pantalla
  - Navegación por voz

## 🛠️ Tecnologías Utilizadas

- **Backend**
  - Python 3.13
  - Django
  - Django Channels (WebSocket)
  - SQLite3
  - PostgresSQL

- **Frontend**
  - HTML5
  - CSS3
  - JavaScript
  - Bootstrap

- **Inteligencia Artificial**
  - YOLOv8-m (Detección de objetos y segmentación)
  - Gemeni

## 📋 Prerrequisitos

```bash
- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Git
```

## 🔧 Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/JavicSoftCode-01/PathFinder_AI.git
cd PathFinder_AI
```

2. **Crear y activar entorno virtual**
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar la base de datos**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Crear superusuario (opcional)**
```bash
python manage.py createsuperuser
```

6. **Iniciar el servidor de desarrollo**
```bash
python manage.py runserver
```

La aplicación estará disponible en `http://localhost:8000`

## 🗂️ Estructura del Proyecto

```
PathFinder_AI/
├── auth_api/                 # Módulo de autenticación
├── core/                     # Funcionalidad principal
├── intelligent_assistant/    # Módulo de IA y asistencia
├── static/                  # Archivos estáticos (CSS, JS, imágenes)
├── templates/               # Plantillas HTML
├── utils/                   # Utilidades y métodos auxiliares
└── PathFinder_AI/          # Configuración principal del proyecto
```

## 📱 Módulos Principales

### Auth API
- Gestión de autenticación y autorización
- Formularios personalizados
- Validadores de seguridad

### Core
- Gestión de ejercicios de entrenamiento
- Sistema de retroalimentación
- Manejo de emergencias

### Intelligent Assistant
- Implementación de YOLOv8 para detección de objetos
- Sistema de lectura de texto
- WebSockets para comunicación en tiempo real

## 🔐 Variables de Entorno

Crear un archivo `.env` en la raíz del proyecto:

```env
SECRET_KEY=tu_clave_secreta
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE.md](LICENSE.md) para más detalles

## 👥 Contribución

1. Fork el proyecto
2. Crea tu rama de características (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📞 Contacto

rsalazarz@unemi.edu.ec
mbermeog2@unemi.edu.ec

## 🙏 Agradecimientos

- Django Framework
- YOLOv8 Team
- Bootstrap Team
- Todos los contribuidores que han ayudado a hacer este proyecto posible

---
