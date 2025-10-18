import re

from django.core.exceptions import ValidationError


def strip_whitespace(value, remove_all=False):
  if not isinstance(value, str):
    value = str(value)
  if remove_all:
    return re.sub(r'\s+', '', value)
  return value.strip()


def raise_validation_error(message):
  full_message = f"Corrija la información del campo: {message}"
  raise ValidationError(full_message)
