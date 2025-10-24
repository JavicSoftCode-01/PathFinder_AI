from django.urls import path

from .views import HomeView, EmergencyView, SendAlertView, FeedbackView, TrainingModeView

app_name = 'core'

urlpatterns = [
  path('home/', HomeView.as_view(), name='home'),
  path('emergency/', EmergencyView.as_view(), name='emergency'),
  path('send-emergency-alert/', SendAlertView.as_view(), name='send_emergency_alert'),
  path('feedback/', FeedbackView.as_view(), name='feedback'),
  path('training/', TrainingModeView.as_view(), name='training'),
]
