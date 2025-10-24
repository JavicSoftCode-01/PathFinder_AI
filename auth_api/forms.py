from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import CustomUser
from .utils.validators import Validation


class CustomUserCreationForm(UserCreationForm):
  full_name = forms.CharField(
    max_length=255,
    label="Nombre completo",
    widget=forms.TextInput(attrs={'placeholder': 'Nombre completo'}),
  )
  email = forms.EmailField(
    label="Correo Electrónico/Usuario",
    widget=forms.EmailInput(attrs={'placeholder': 'Correo Electrónico/Usuario'}),
  )
  emailEmergency = forms.EmailField(
    label="Correo Electrónico de Emergencia",
    widget=forms.EmailInput(attrs={'placeholder': 'Correo Electrónico de Emergencia'}),
  )
  emailAlternative = forms.EmailField(
    label="Correo Electrónico Alternativo",
    required=False,
    widget=forms.EmailInput(attrs={'placeholder': 'Correo Electrónico Alternativo'}),
  )
  emergency_contact = forms.CharField(
    max_length=10,
    label="Contacto de emergencia",
    widget=forms.TextInput(attrs={
      'placeholder': 'Contacto de emergencia',
      'type': 'tel',
      'inputmode': 'numeric',
      'pattern': '[0-9]*'
    }),
  )
  age = forms.IntegerField(
    label="Edad",
    widget=forms.NumberInput(attrs={'placeholder': 'Edad'}),
  )
  alternative_contact = forms.CharField(
    max_length=10,
    required=False,
    label="Contacto alternativo",
    widget=forms.TextInput(attrs={
      'placeholder': 'Contacto alternativo',
      'type': 'tel',
      'inputmode': 'numeric',
      'pattern': '[0-9]*'
    }),
  )

  class Meta:
    model = CustomUser
    fields = (
      'full_name', 'email', 'emailEmergency', 'emailAlternative',
      'emergency_contact', 'alternative_contact', 'age',
      'password1', 'password2'
    )

  def clean_full_name(self):
    value = self.cleaned_data.get('full_name')
    try:
      return Validation.validate_full_name(value)
    except ValidationError as e:
      raise ValidationError(str(e.message))

  def clean_email(self):
    value = self.cleaned_data.get('email')
    try:
      validated_email = Validation.validate_email(value)
      if CustomUser.objects.filter(email=validated_email).exists():
        raise ValidationError("Este correo electrónico ya está registrado")
      return validated_email
    except ValidationError as e:
      raise ValidationError(str(e.message) if hasattr(e, 'message') else str(e))

  def clean_emailEmergency(self):
    value = self.cleaned_data.get('emailEmergency')
    if value:
      try:
        return Validation.validate_email(value)
      except ValidationError as e:
        raise ValidationError(str(e.message) if hasattr(e, 'message') else str(e))
    return value

  def clean_emailAlternative(self):
    value = self.cleaned_data.get('emailAlternative')
    if value:
      try:
        return Validation.validate_email(value)
      except ValidationError as e:
        raise ValidationError(str(e.message) if hasattr(e, 'message') else str(e))
    return value

  def clean_emergency_contact(self):
    value = self.cleaned_data.get('emergency_contact')
    try:
      return Validation.validate_phone_number(value)
    except ValidationError as e:
      raise ValidationError(str(e.message) if hasattr(e, 'message') else str(e))

  def clean_alternative_contact(self):
    value = self.cleaned_data.get('alternative_contact')
    if value:
      try:
        return Validation.validate_phone_number(value)
      except ValidationError as e:
        raise ValidationError(str(e.message) if hasattr(e, 'message') else str(e))
    return value

  def clean_age(self):
    value = self.cleaned_data.get('age')
    try:
      return Validation.validate_age(value)
    except ValidationError as e:
      raise ValidationError(str(e.message) if hasattr(e, 'message') else str(e))
