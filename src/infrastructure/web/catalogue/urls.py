from django.urls import path

from infrastructure.web.catalogue import views

app_name = "catalogue"

urlpatterns = [
    path("catalogue/", views.index, name="index"),  # Story 2.2: /<lang>/catalogue/
    # `int` converter: a non-numeric id matches no route (404) and never reaches the view.
    path("subjects/<int:subject_id>/", views.subject, name="subject"),
]
