from django.urls import path

from infrastructure.web.home import views

app_name = "home"

urlpatterns = [
    path("", views.index, name="index"),  # Story 1.7: /<lang>/
]
