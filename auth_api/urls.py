from django.urls import path, include

from .views import RegisterView, CustomLoginView, CustomLogoutView

app_name = "auth_api"
urlpatterns = [
  path("", CustomLoginView.as_view(), name="login"),
  path("register/", RegisterView.as_view(), name="register"),
  path("logout/", CustomLogoutView.as_view(), name="logout"),
  path('core/', include("core.urls")),
  path('intelligent-assistant/', include("intelligent_assistant.urls")),
]
