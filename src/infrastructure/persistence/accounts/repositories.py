"""Adapters for account ports (Story 1.9 adds account management here)."""

from infrastructure.persistence.accounts.models import UserModel


class DjangoUsernameDirectory:
    """Implements `application.accounts.record_security_event.UsernameDirectory`."""

    def exists(self, username: str) -> bool:
        return UserModel.objects.filter(username=username).exists()


class DjangoUserPreferences:
    """Implements `application.accounts.update_preferred_language.UserPreferencePort`."""

    def get_language(self, user_id: int) -> str:
        return UserModel.objects.values_list("preferred_language", flat=True).get(pk=user_id)

    def set_language(self, user_id: int, language: str) -> None:
        # Single-column UPDATE scoped to this user only; no other field is touched.
        UserModel.objects.filter(pk=user_id).update(preferred_language=language)
