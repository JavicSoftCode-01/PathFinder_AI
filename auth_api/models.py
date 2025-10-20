from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .utils.validators import Validation


class CustomUser(AbstractUser):
  age = models.PositiveIntegerField(_("Edad"), validators=[Validation.validate_age])
  full_name = models.CharField(_("Nombre completo"), max_length=255, validators=[Validation.validate_full_name])
  email = models.EmailField(_("Correo Electrónico"), unique=True, validators=[Validation.validate_email])

  emailEmergency = models.EmailField(
    _("Correo Electrónico de Emergencia"),
    max_length=254,
    validators=[Validation.validate_email]
  )
  emailAlternative = models.EmailField(
    _("Correo Electrónico Alternativo"),
    max_length=254,
    blank=True,
    null=True,
    validators=[Validation.validate_email]
  )

  emergency_contact = models.CharField(
    _("Contacto de emergencia"),
    max_length=255,
    validators=[Validation.validate_phone_number]
  )
  alternative_contact = models.CharField(
    _("Contacto alternativo"),
    blank=True,
    null=True,
    max_length=255,
    validators=[Validation.validate_phone_number]
  )

  USERNAME_FIELD = 'email'
  REQUIRED_FIELDS = ['full_name', 'age', 'emergency_contact']

  first_name = None
  last_name = None

  def __str__(self):
    return self.email

  def save(self, *args, **kwargs):
    if not self.username and self.email:
      self.username = self.extract_username_from_email()
    super().save(*args, **kwargs)

  def extract_username_from_email(self):
    return self.email.split('@')[0]
