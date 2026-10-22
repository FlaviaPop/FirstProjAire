from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AuditConfig(AppConfig):
    name = "infrastructure.persistence.audit"
    label = "audit"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Audit log")  # Story 1.9: shown in the admin area

    def ready(self) -> None:
        from infrastructure.persistence.audit import receivers  # noqa: F401 — connects signals
