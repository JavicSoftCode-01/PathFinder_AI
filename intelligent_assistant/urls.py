from django.urls import path

from .views import TextReaderView

app_name = 'intelligent_assistant'

urlpatterns = [
  path('text_reader/', TextReaderView.as_view(), name='text_reader'),
]
