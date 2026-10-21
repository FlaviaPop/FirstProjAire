from django.apps import AppConfig


class CatalogueConfig(AppConfig):
    name = "infrastructure.persistence.catalogue"
    label = "catalogue"
    default_auto_field = "django.db.models.BigAutoField"
