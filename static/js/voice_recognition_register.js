// ============================================
// VALIDACIÓN EN TIEMPO REAL
// ============================================
const form = document.getElementById('registerForm');
const inputs = form.querySelectorAll('input[type="text"], input[type="email"], input[type="number"], input[type="password"], input[type="tel"]');

inputs.forEach(input => {
  input.addEventListener('blur', function () {
    validateField(this, true); // Con feedback de voz
  });

  // También validar en 'input' para campos numéricos
  if (input.type === 'number' || input.type === 'tel') {
    input.addEventListener('input', function () {
      // Validar solo si tiene contenido
      if (this.value.trim()) {
        validateField(this, false); // Sin feedback de voz en tiempo real
      }
    });
  }
});

// ============================================
// MOSTRAR/OCULTAR CONTRASEÑAS
// ============================================
const togglePasswordBtns = document.querySelectorAll('.toggle-password-btn');

togglePasswordBtns.forEach(btn => {
  btn.addEventListener('click', function () {
    const targetField = this.getAttribute('data-target');
    const passwordInput = document.querySelector(`input[name="${targetField}"]`);

    if (!passwordInput) return;

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
});

function validateField(field, speakFeedback = false) {
  const fieldName = field.name;
  const validationIcon = document.querySelector(`[data-field="${fieldName}"]`);

  // Campos opcionales cliente-side: alternative_contact y emailAlternative
  const optionalFields = ['alternative_contact', 'emailAlternative'];

  // Si el campo está vacío y no es opcional, limpiar validación
  if (!field.value && !optionalFields.includes(fieldName)) {
    if (validationIcon) validationIcon.style.display = 'none';
    field.classList.remove('valid', 'invalid');
    return;
  }

  // Si es uno de los opcionales y está vacío -> válido (no mostrar icono)
  if (optionalFields.includes(fieldName) && !field.value.trim()) {
    if (validationIcon) validationIcon.style.display = 'none';
    field.classList.remove('valid', 'invalid');
    return;
  }

  const formData = new FormData();
  formData.append(fieldName, field.value);
  formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

  // Si es password1, incluir email para validar similitud
  if (fieldName === 'password1') {
    const emailField = document.querySelector('input[name="email"]');
    if (emailField && emailField.value) {
      formData.append('email', emailField.value);
    }
  }

  // Si es password2, incluir password1 para comparación
  if (fieldName === 'password2') {
    const password1Field = document.querySelector('input[name="password1"]');
    if (password1Field) {
      formData.append('password1', password1Field.value);
    }
  }

  fetch(window.location.href, {
    method: 'POST',
    body: formData,
    headers: {
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
    .then(response => response.json())
    .then(data => {
      if (validationIcon) validationIcon.style.display = 'flex';

      if (data[fieldName] === 'valid') {
        field.classList.remove('invalid');
        field.classList.add('valid');
        if (validationIcon) {
          validationIcon.innerHTML = '✓';
          validationIcon.className = 'validation-icon';
        }

        if (speakFeedback) {
          speak(getFieldLabel(fieldName) + ' válido');
        }
      } else {
        field.classList.remove('valid');
        field.classList.add('invalid');
        if (validationIcon) {
          validationIcon.innerHTML = '✗';
          validationIcon.className = 'validation-icon invalid-icon';
        }

        if (speakFeedback && data.error) {
          speak(data.error);
        } else if (speakFeedback) {
          speak(getFieldLabel(fieldName) + ' inválido. Verifique el formato');
        }
      }
    })
    .catch(error => {
      console.error('Error:', error);
      if (speakFeedback) {
        speak('Error al validar el campo');
      }
    });
}

// Obtener el nombre legible del campo
function getFieldLabel(fieldName) {
  const labels = {
    'full_name': 'Nombre completo',
    'email': 'Correo electrónico',
    'emailEmergency': 'Correo electrónico de emergencia',
    'emailAlternative': 'Correo electrónico alternativo',
    'password1': 'Contraseña',
    'password2': 'Confirmación de contraseña',
    'emergency_contact': 'Contacto de emergencia',
    'age': 'Edad',
    'alternative_contact': 'Contacto alternativo'
  };
  return labels[fieldName] || fieldName;
}

// ============================================
// SÍNTESIS DE VOZ (TTS)
// ============================================
function speak(text, callback) {
  if (!('speechSynthesis' in window)) {
    console.error('Tu navegador no soporta síntesis de voz');
    if (callback) callback();
    return;
  }

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

// ============================================
// LIMPIEZA DE TEXTO SEGÚN TIPO DE CAMPO
// ============================================
function cleanEmailText(text) {
  let cleaned = text.toLowerCase().trim();
  cleaned = cleaned.replace(/\s+/g, '');

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

  Object.keys(replacements).forEach(key => {
    const regex = new RegExp(key, 'gi');
    cleaned = cleaned.replace(regex, replacements[key]);
  });

  const atCount = (cleaned.match(/@/g) || []).length;
  if (atCount > 1) {
    const parts = cleaned.split('@');
    cleaned = parts[0] + '@' + parts.slice(1).join('');
  }

  return cleaned;
}

function cleanPhoneText(text) {
  let cleaned = text.toLowerCase().trim();

  const numberMap = {
    'cero': '0', 'uno': '1', 'dos': '2', 'tres': '3', 'cuatro': '4',
    'cinco': '5', 'seis': '6', 'siete': '7', 'ocho': '8', 'nueve': '9'
  };

  Object.keys(numberMap).forEach(word => {
    const regex = new RegExp(word, 'gi');
    cleaned = cleaned.replace(regex, numberMap[word]);
  });

  cleaned = cleaned.replace(/\s+/g, '');
  cleaned = cleaned.replace(/\D/g, ''); // Solo números

  return cleaned;
}

function cleanNumberText(text) {
  let cleaned = text.toLowerCase().trim();

  const numberMap = {
    'cero': '0', 'uno': '1', 'dos': '2', 'tres': '3', 'cuatro': '4',
    'cinco': '5', 'seis': '6', 'siete': '7', 'ocho': '8', 'nueve': '9',
    'diez': '10', 'once': '11', 'doce': '12', 'trece': '13', 'catorce': '14',
    'quince': '15', 'dieciséis': '16', 'diecisiete': '17', 'dieciocho': '18',
    'diecinueve': '19', 'veinte': '20', 'veintiuno': '21', 'veintidós': '22'
  };

  Object.keys(numberMap).forEach(word => {
    const regex = new RegExp(word, 'gi');
    cleaned = cleaned.replace(regex, numberMap[word]);
  });

  cleaned = cleaned.replace(/\s+/g, '');
  cleaned = cleaned.replace(/\D/g, '');

  return cleaned;
}

function cleanNameText(text) {
  // Capitalizar cada palabra
  return text.trim()
    .split(/\s+/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

function cleanPasswordText(text) {
  return text.toLowerCase().trim().replace(/\s+/g, '');
}

// ============================================
// RECONOCIMIENTO DE VOZ POR CAMPO
// ============================================
const micButtons = document.querySelectorAll('.icon-btn');

micButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    if (!('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
      speak('Tu navegador no soporta reconocimiento de voz');
      return;
    }

    const input = btn.closest('.input-wrapper').querySelector('input');
    const fieldName = input.name;

    const voicePrompt = getVoicePrompt(fieldName);
    const originalEmoji = btn.textContent;
    btn.textContent = '🔴';
    btn.disabled = true;

    speak(voicePrompt, () => {
      const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new Recognition();

      recognition.lang = 'es-ES';
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      let recognitionTimeout = setTimeout(() => {
        recognition.stop();
        speak('Tiempo agotado. Intente nuevamente');
      }, 15000);

      recognition.onresult = (event) => {
        clearTimeout(recognitionTimeout);
        const transcript = event.results[0][0].transcript;
        console.log('Transcripción original:', transcript);

        let cleanedValue = cleanTextByField(fieldName, transcript);
        input.value = cleanedValue;
        console.log('Valor limpio:', cleanedValue);

        setTimeout(() => {
          validateField(input, true);
        }, 100);
      };

      recognition.onerror = (event) => {
        clearTimeout(recognitionTimeout);
        console.error('Error en reconocimiento:', event.error);
        btn.textContent = originalEmoji;
        btn.disabled = false;

        let errorMessage = 'Error en el reconocimiento de voz';
        if (event.error === 'network') {
          errorMessage = 'Problema de conexión a internet';
        } else if (event.error === 'not-allowed') {
          errorMessage = 'Permiso de micrófono denegado';
        } else if (event.error === 'no-speech') {
          errorMessage = 'No se detectó ninguna voz. Intenta de nuevo';
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

// Obtener prompt de voz según el campo
function getVoicePrompt(fieldName) {
  const prompts = {
    'full_name': 'Diga su nombre completo, ahora',
    'email': 'Diga su correo electrónico, ahora',
    'emailEmergency': 'Diga su correo electrónico de emergencia, ahora',
    'emailAlternative': 'Diga su correo electrónico alternativo, ahora',
    'password1': 'Diga su contraseña, ahora',
    'password2': 'Confirme su contraseña, ahora',
    'emergency_contact': 'Diga el número de contacto de emergencia, ahora',
    'age': 'Diga su edad, ahora',
    'alternative_contact': 'Diga el contacto alternativo, ahora'
  };
  return prompts[fieldName] || 'Diga el valor, ahora';
}

// Limpiar texto según tipo de campo
function cleanTextByField(fieldName, text) {
  switch (fieldName) {
    case 'email':
    case 'emailEmergency':
    case 'emailAlternative':
      return cleanEmailText(text);
    case 'emergency_contact':
    case 'alternative_contact':
      return cleanPhoneText(text);
    case 'age':
      return cleanNumberText(text);
    case 'full_name':
      return cleanNameText(text);
    case 'password1':
    case 'password2':
      return cleanPasswordText(text);
    default:
      return text.trim();
  }
}

// ============================================
// LECTURA AUTOMÁTICA DE MENSAJES AL CARGAR
// ============================================
window.addEventListener('load', function () {
  setTimeout(() => {
    const messagesContainer = document.querySelector('.messages');

    if (messagesContainer) {
      const alerts = messagesContainer.querySelectorAll('.alert');

      if (alerts.length > 0) {
        console.log('Mensajes encontrados:', alerts.length);

        alerts.forEach((alert, index) => {
          const messageText = alert.textContent.trim();
          console.log('Mensaje a leer:', messageText);

          setTimeout(() => {
            speak(messageText);
          }, index * 2500);
        });
      }
    }
  }, 1000);
});

// Información sobre HTTPS
if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
  console.warn('⚠️ El reconocimiento de voz solo funciona en HTTPS o localhost');
}
