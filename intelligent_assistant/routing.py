from django.urls import path

from . import consumers

websocket_urlpatterns = [
  path('ws/obstacle_detection/', consumers.ObstacleConsumer.as_asgi()),
]
