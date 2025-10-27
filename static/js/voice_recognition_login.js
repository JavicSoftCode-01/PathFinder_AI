// ============================================
// VALIDACIÓN EN TIEMPO REAL
// ============================================
const form = document.querySelector('form');
const inputs = form.querySelectorAll('input');

inputs.forEach(input => {
  input.addEventListener('blur', function () {
    validateField(this, true); // Activar feedback de voz
  });
});

// ============================================
// MOSTRAR/OCULTAR CONTRASEÑA
// ============================================
const togglePasswordBtn = document.querySelector('.toggle-password-btn');
const passwordInput = document.querySelector('#id_password');

if (togglePasswordBtn && passwordInput) {
  togglePasswordBtn.addEventListener('click', function () {
    // Alternar entre password y text
    if (passwordInput.type === 'password') {
      passwordInput.type = 'text';
      this.textContent = '🙈'; // Cambiar icono a "ocultar"
      this.title = 'Ocultar contraseña';
    } else {
      passwordInput.type = 'password';
      this.textContent = '👁️'; // Cambiar icono a "mostrar"
      this.title = 'Mostrar contraseña';
    }
  });
}

function validateField(field, speakFeedback = false) {
  const fieldName = field.name;
  const validationIcon = field.parentElement.querySelector('.validation-icon');

  if (!field.value) {
    validationIcon.style.display = 'none';
    field.classList.remove('valid', 'invalid');
    return;
  }

  let isValid = false;
  let feedbackMessage = '';

  if (fieldName === 'username') {
    // Validación de email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    isValid = emailRegex.test(field.value);

    if (isValid) {
      feedbackMessage = 'Correo electrónico válido';
    } else {
      feedbackMessage = 'Correo electrónico inválido. Verifique el formato. Debe incluir arroba y punto';
    }
  } else if (fieldName === 'password') {
    // Validación básica de contraseña (al menos 8 caracteres)
    isValid = field.value.length >= 8;

    if (isValid) {
      feedbackMessage = 'Contraseña válida';
    } else {
      feedbackMessage = 'Contraseña muy corta. Debe tener al menos 8 caracteres';
    }
  }

  validationIcon.style.display = 'flex';
  if (isValid) {
    field.classList.remove('invalid');
    field.classList.add('valid');
    validationIcon.innerHTML = '✓';
    validationIcon.classList.remove('invalid-icon');
  } else {
    field.classList.remove('valid');
    field.classList.add('invalid');
    validationIcon.innerHTML = '✗';
    validationIcon.classList.add('invalid-icon');
  }

  // Dar feedback de voz solo si se solicita
  if (speakFeedback) {
    speak(feedbackMessage);
  }
}

// Función para limpiar el texto del correo electrónico
function cleanEmailText(text) {
  // Convertir todo a minúsculas
  let cleaned = text.toLowerCase().trim();

  // Eliminar todos los espacios
  cleaned = cleaned.replace(/\s+/g, '');

  // Reemplazar palabras comunes pronunciadas
  const replacements = {
    'arroba': '@',
    'aroba': '@',
    'en': '@',
    'punto': '.',
    'puntoes': '.es',
    'puntocom': '.com',
    'puntoedu': '.edu',
    'puntogob': '.gob',
    'puntomx': '.mx',
    'puntoec': '.ec',
    'puntoco': '.co',
    'puntoorg': '.org',
    'puntonet': '.net'
  };

  // Aplicar reemplazos
  Object.keys(replacements).forEach(key => {
    const regex = new RegExp(key, 'gi');
    cleaned = cleaned.replace(regex, replacements[key]);
  });

  // Asegurar que solo haya un @
  const atCount = (cleaned.match(/@/g) || []).length;
  if (atCount > 1) {
    const parts = cleaned.split('@');
    cleaned = parts[0] + '@' + parts.slice(1).join('');
  }

  return cleaned;
}

// Función para convertir texto de números a dígitos
function cleanPasswordText(text) {
  let cleaned = text.toLowerCase().trim();

  // Mapeo de palabras a números
  const numberMap = {
    'cero': '0',
    'uno': '1',
    'dos': '2',
    'tres': '3',
    'cuatro': '4',
    'cinco': '5',
    'seis': '6',
    'siete': '7',
    'ocho': '8',
    'nueve': '9'
  };

  // Reemplazar palabras por números
  Object.keys(numberMap).forEach(word => {
    const regex = new RegExp(word, 'gi');
    cleaned = cleaned.replace(regex, numberMap[word]);
  });

  // Eliminar espacios
  cleaned = cleaned.replace(/\s+/g, '');

  return cleaned;
}

// Función para detectar si el correo está completo
function isEmailComplete(text) {
  const emailEndings = ['.com', '.es', '.edu', '.gob', '.mx', '.ec', '.co', '.org', '.net'];
  return emailEndings.some(ending => text.toLowerCase().endsWith(ending));
}

// Función de síntesis de voz (TTS)
function speak(text, callback) {
  if (!('speechSynthesis' in window)) {
    console.error('Tu navegador no soporta síntesis de voz');
    if (callback) callback();
    return;
  }

  // Cancelar cualquier síntesis en curso
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'es-ES';
  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  utterance.volume = 1.0;

  utterance.onend = () => {
    if (callback) callback();
  };

  utterance.onerror = (event) => {
    console.error('Error en síntesis de voz:', event);
    if (callback) callback();
  };

  window.speechSynthesis.speak(utterance);
}

// Funcionalidad de entrada por voz mejorada
const micButtons = document.querySelectorAll('.icon-btn');

micButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    if (!('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
      alert('Tu navegador no soporta reconocimiento de voz.');
      return;
    }

    const input = btn.closest('.input-wrapper').querySelector('input');
    const fieldName = input.name;

    // Mensaje personalizado según el campo
    let voicePrompt = '';
    if (fieldName === 'username') {
      voicePrompt = 'Diga su correo electrónico, ahora';
    } else if (fieldName === 'password') {
      voicePrompt = 'Diga su contraseña, ahora';
    }

    // Cambiar icono a indicar que está escuchando
    const originalEmoji = btn.textContent;
    btn.textContent = '🔴';
    btn.disabled = true;

    // Hablar primero, luego escuchar
    speak(voicePrompt, () => {
      const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new Recognition();

      recognition.lang = 'es-ES';
      recognition.continuous = false; // NO continuo - una sola captura
      recognition.interimResults = false; // Sin resultados intermedios
      recognition.maxAlternatives = 1;

      let recognitionTimeout;
      let hasRecognized = false;

      // Timeout de seguridad para correos (15 segundos)
      if (fieldName === 'username') {
        recognitionTimeout = setTimeout(() => {
          if (!hasRecognized) {
            recognition.stop();
            speak('Tiempo agotado. Intente nuevamente.');
          }
        }, 15000);
      }

      recognition.onresult = (event) => {
        hasRecognized = true;
        clearTimeout(recognitionTimeout);

        const transcript = event.results[0][0].transcript;
        console.log('Transcripción original:', transcript);

        // Procesar según el tipo de campo
        if (fieldName === 'username') {
          const cleanedEmail = cleanEmailText(transcript);
          input.value = cleanedEmail;
          console.log('Email limpio:', cleanedEmail);

          // Validar y dar feedback
          setTimeout(() => {
            validateField(input, true); // Feedback de voz activado
            if (isEmailComplete(cleanedEmail)) {
              speak('Correo registrado correctamente');
            } else {
              speak('Correo incompleto. Por favor verifique');
            }
          }, 100);
        } else if (fieldName === 'password') {
          const cleanedPassword = cleanPasswordText(transcript);
          input.value = cleanedPassword;
          console.log('Contraseña limpia:', cleanedPassword);

          setTimeout(() => {
            validateField(input, true); // Feedback de voz activado
            speak('Contraseña registrada');
          }, 100);
        }
      };

      recognition.onerror = (event) => {
        hasRecognized = true;
        clearTimeout(recognitionTimeout);
        console.error('Error en reconocimiento:', event.error);
        btn.textContent = originalEmoji;
        btn.disabled = false;

        let errorMessage = 'Error en el reconocimiento de voz';

        if (event.error === 'network') {
          errorMessage = 'Problema de conexión a internet';
        } else if (event.error === 'not-allowed') {
          errorMessage = 'Permiso de micrófono denegado. Por favor, permite el acceso al micrófono';
        } else if (event.error === 'no-speech') {
          errorMessage = 'No se detectó ninguna voz. Intenta de nuevo';
        } else if (event.error === 'aborted') {
          errorMessage = 'Reconocimiento cancelado';
        }

        speak(errorMessage);
      };

      recognition.onend = () => {
        clearTimeout(recognitionTimeout);
        btn.textContent = originalEmoji;
        btn.disabled = false;
      };

      recognition.start();
    });
  });
});

// Información sobre HTTPS
if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
  console.warn('⚠️ El reconocimiento de voz solo funciona en HTTPS o localhost por seguridad del navegador.');
}

// ============================================
// LECTURA AUTOMÁTICA DE MENSAJES AL CARGAR
// ============================================
window.addEventListener('load', function () {
  // Esperar a que todo esté cargado
  setTimeout(() => {
    // Buscar mensajes de Django
    const messagesContainer = document.querySelector('.messages');

    if (messagesContainer) {
      const alerts = messagesContainer.querySelectorAll('.alert');

      if (alerts.length > 0) {
        console.log('Mensajes encontrados:', alerts.length);

        alerts.forEach((alert, index) => {
          const messageText = alert.textContent.trim();
          console.log('Mensaje a leer:', messageText);

          // Leer cada mensaje con una pausa entre ellos
          setTimeout(() => {
            speak(messageText);
          }, index * 2500); // 2.5 segundos entre cada mensaje
        });
      } else {
        console.log('No hay mensajes para leer');
      }
    } else {
      console.log('No se encontró contenedor de mensajes');
    }
  }, 1000); // Esperar 1 segundo después de que cargue todo
});