from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from utils.auxiliary_methods import raise_validation_error, strip_whitespace


class Validation:

  @staticmethod
  def validate_full_name(value):
    if not value:
      raise_validation_error("el nombre completo es requerido.")
    cleaned = strip_whitespace(value, remove_all=False)
    if len(cleaned) < 3:
      raise_validation_error("el nombre completo debe tener al menos 3 caracteres.")
    if not all(c.isalpha() or c.isspace() for c in cleaned):
      raise_validation_error(
        "el nombre completo solo puede contener letras (incluyendo Ñ, tildes y acentos) y espacios.")
    return cleaned

  @staticmethod
  def validate_email(value):
    if not value:
      raise_validation_error("el correo electrónico es requerido.")
    cleaned = strip_whitespace(value, remove_all=True)
    try:
      validate_email(cleaned)
    except ValidationError:
      raise_validation_error("el correo electrónico no es válido.")
    return cleaned

  @staticmethod
  def validate_phone_number(value):
    if not value:
      raise_validation_error("el contacto es requerido.")
    value_str = str(value)
    cleaned = strip_whitespace(value_str, remove_all=True)
    if not cleaned.isdigit():
      raise_validation_error("el contacto debe ser numérico.")
    if len(cleaned) != 10:
      raise_validation_error("el contacto debe tener exactamente 10 dígitos.")
    if not cleaned.startswith('09'):
      raise_validation_error("el contacto debe iniciar con '09' para números ecuatorianos.")
    return cleaned

  @staticmethod
  def validate_age(value):
    if value is None or value == '':
      raise_validation_error("la edad es requerida.")
    if isinstance(value, int):
      age_int = value
    else:
      cleaned = strip_whitespace(str(value), remove_all=True)
      if not cleaned.isdigit():
        raise_validation_error("la edad debe ser numérica.")
      age_int = int(cleaned)

    if not (10 <= age_int <= 100):
      raise_validation_error("la edad debe estar entre 10 y 100 años.")
    return age_int
