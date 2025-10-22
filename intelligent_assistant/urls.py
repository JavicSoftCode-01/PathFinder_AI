from django.urls import path

from .views import TextReaderView, ObstacleDetectionView

app_name = 'intelligent_assistant'

urlpatterns = [
  path('text_reader/', TextReaderView.as_view(), name='text_reader'),
  path('obstacle_detection/', ObstacleDetectionView.as_view(), name='obstacle_detection'),
]
