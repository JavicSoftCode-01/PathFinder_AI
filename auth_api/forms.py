from django import forms
from django.contrib.auth.forms import UserCreationForm

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
  emergency_contact = forms.CharField(
    max_length=10,
    label="Contacto de emergencia",
    widget=forms.NumberInput(attrs={'placeholder': 'Contacto de emergencia'}),
  )
  age = forms.IntegerField(
    label="Edad",
    widget=forms.NumberInput(attrs={'placeholder': 'Edad'}),
  )
  alternative_contact = forms.CharField(
    max_length=10,
    required=False,
    label="Contacto alternativo",
    widget=forms.NumberInput(attrs={'placeholder': 'Contacto alternativo'}),
  )

  class Meta:
    model = CustomUser
    fields = ('full_name', 'email', 'emergency_contact', 'age', 'alternative_contact', 'password1', 'password2')

  def clean_full_name(self):
    value = self.cleaned_data.get('full_name')
    return Validation.validate_full_name(value)

  def clean_email(self):
    value = self.cleaned_data.get('email')
    return Validation.validate_email(value)

  def clean_emergency_contact(self):
    value = self.cleaned_data.get('emergency_contact')
    return Validation.validate_phone_number(value)

  def clean_alternative_contact(self):
    value = self.cleaned_data.get('alternative_contact')
    if value:
      return Validation.validate_phone_number(value)
    return value

  def clean_age(self):
    value = self.cleaned_data.get('age')
    return Validation.validate_age(value)
