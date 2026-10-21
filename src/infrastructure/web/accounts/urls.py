from django.urls import path

from infrastructure.web.accounts.views import PlatformLoginView, PlatformLogoutView

app_name = "accounts"
urlpatterns = [
    path("accounts/login/", PlatformLoginView.as_view(), name="login"),
    path("accounts/logout/", PlatformLogoutView.as_view(), name="logout"),
]
