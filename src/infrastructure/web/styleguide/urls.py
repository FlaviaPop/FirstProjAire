from django.urls import path

from infrastructure.web.styleguide import views

app_name = "styleguide"

# Included by config/urls.py only when settings.DEBUG is True.
urlpatterns = [
    path("", views.index, name="index"),
]
