from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from auth_api.models import CustomUser


class UserFeedback(models.Model):
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  responded_correctly = models.BooleanField(_("Responded Correctly"))
  comment = models.TextField(_("Comment"), blank=True, null=True)
  created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

  def __str__(self):
    return f"Feedback from {self.user.email} at {self.created_at}"


class TrainingExercise(models.Model):
  command_text = models.CharField(
    _("Texto del Comando a Decir"),
    max_length=255,
    help_text="El comando exacto que el usuario debe decir. Ej: 'Activar detección de obstáculos'"
  )
  explanation_text = models.TextField(
    _("Explicación del Comando"),
    blank=True,
    help_text="Una breve descripción de lo que hace el comando (para la sección 'Ver ejemplos')."
  )
  order = models.PositiveIntegerField(
    _("Orden"),
    default=0,
    help_text="El orden en que aparecerá el ejercicio (0 primero, 1 después, etc.)."
  )

  class Meta:
    verbose_name = _("Ejercicio de Entrenamiento")
    verbose_name_plural = _("Ejercicios de Entrenamiento")
    ordering = ['order']

  def __str__(self):
    return f"Ejercicio {self.order}: {self.command_text}"
