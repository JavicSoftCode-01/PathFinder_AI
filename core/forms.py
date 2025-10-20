from django import forms

from .models import UserFeedback


class UserFeedbackForm(forms.ModelForm):
  class Meta:
    model = UserFeedback
    fields = ['responded_correctly', 'comment']
    widgets = {
      'comment': forms.Textarea(attrs={'placeholder': 'Enviar comentarios'}),
    }
