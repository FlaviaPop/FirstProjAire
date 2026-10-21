from django.apps import AppConfig


class AuditConfig(AppConfig):
    name = "infrastructure.persistence.audit"
    label = "audit"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        from infrastructure.persistence.audit import receivers  # noqa: F401 — connects signals
