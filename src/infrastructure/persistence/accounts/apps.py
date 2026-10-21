from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "infrastructure.persistence.accounts"
    label = "accounts"
    default_auto_field = "django.db.models.BigAutoField"
