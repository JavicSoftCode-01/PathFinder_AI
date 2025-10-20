from django.urls import path

from .views import HomeView, EmergencyView

app_name = 'core'

urlpatterns = [
  path('home/', HomeView.as_view(), name='home'),
path('emergency/', EmergencyView.as_view(), name='emergency')
]
