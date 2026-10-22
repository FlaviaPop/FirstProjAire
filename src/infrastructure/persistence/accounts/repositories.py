"""Adapters for account ports (Story 1.9 adds parent-child links here)."""

from datetime import datetime

from django.db import IntegrityError

from application.accounts.link_parent import LinkExists
from infrastructure.persistence.accounts.models import ParentChildLinkModel, UserModel


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


class DjangoParentLinks:
    """Implements `application.accounts.link_parent.ParentLinkPort` (Story 1.9)."""

    def role_of(self, user_id: int) -> str | None:
        return UserModel.objects.filter(pk=user_id).values_list("role", flat=True).first()

    def exists(self, parent_id: int, student_id: int) -> bool:
        return ParentChildLinkModel.objects.filter(
            parent_id=parent_id, student_id=student_id
        ).exists()

    def add(self, parent_id: int, student_id: int, created_by: int, at: datetime) -> int:
        try:
            link = ParentChildLinkModel.objects.create(
                parent_id=parent_id, student_id=student_id, created_by_id=created_by, created_at=at
            )
        except IntegrityError as exc:  # a concurrent duplicate hit UNIQUE(parent, student)
            raise LinkExists() from exc
        return link.pk

    def remove(self, link_id: int) -> tuple[int, int] | None:
        pair = (
            ParentChildLinkModel.objects.filter(pk=link_id)
            .values_list("parent_id", "student_id")
            .first()
        )
        if pair is not None:
            ParentChildLinkModel.objects.filter(pk=link_id).delete()
        return pair
