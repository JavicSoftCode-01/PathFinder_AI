from django.urls import path, include

from .views import RegisterView, CustomLoginView, CustomLogoutView

app_name = "auth_api"
urlpatterns = [
  path('core/', include("core.urls")),
  path("register/", RegisterView.as_view(), name="register"),
  path("", CustomLoginView.as_view(), name="login"),
  path("logout/", CustomLogoutView.as_view(), name="logout"),
]
