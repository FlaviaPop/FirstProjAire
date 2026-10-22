from typing import Any, ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from infrastructure.persistence.accounts.managers import UserManager

# Values mirror domain.accounts.roles.Role (Story 1.3 asserts equality).
ROLE_CHOICES = [
    ("STUDENT", _("Student")),
    ("TEACHER", _("Teacher")),
    ("PARENT", _("Parent/Guardian")),
    ("ADMIN", _("Admin")),
]
LANGUAGE_CHOICES = [("ro", "Română"), ("en", "English")]  # endonyms: never translated
ADMIN_ROLE = "ADMIN"
STAFF_FLAGS = ("is_staff", "is_superuser")


class UserModel(AbstractUser):
    first_name = None  # type: ignore[assignment]  # replaced by full_name (requirements)
    last_name = None  # type: ignore[assignment]
    full_name = models.CharField(_("full name"), max_length=150)
    date_of_birth = models.DateField(_("date of birth"))
    role = models.CharField(_("role"), max_length=10, choices=ROLE_CHOICES)
    preferred_language = models.CharField(
        _("preferred language"), max_length=2, choices=LANGUAGE_CHOICES, default="ro"
    )

    objects: ClassVar[UserManager] = UserManager()
    REQUIRED_FIELDS: ClassVar[list[str]] = ["full_name", "date_of_birth"]

    class Meta:
        db_table = "accounts_user"
        verbose_name = _("account")
        verbose_name_plural = _("accounts")

    def __str__(self) -> str:
        return self.username

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Django admin access follows the platform role (architecture: admin limited to the
        # Admin role), so a demoted Admin loses it on the next request.
        self.is_staff = self.is_superuser = self.role == ADMIN_ROLE
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and "role" in update_fields:
            kwargs["update_fields"] = {*update_fields, *STAFF_FLAGS}
        super().save(*args, **kwargs)

    def get_full_name(self) -> str:
        return self.full_name

    def get_short_name(self) -> str:
        return self.full_name


class ParentChildLinkModel(models.Model):
    """PARENT_CHILD_LINK: a parent sees only the progress of children linked here."""

    # Deleting either account deletes its links (retention: kept until the account is deleted).
    parent = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="child_links",
        verbose_name=_("Parent/Guardian"),
    )
    student = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name="parent_links",
        verbose_name=_("Student"),
    )
    created_by = models.ForeignKey(
        UserModel,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("created by"),
    )
    created_at = models.DateTimeField(_("created at"))

    class Meta:
        db_table = "accounts_parent_child_link"
        verbose_name = _("parent-child link")
        verbose_name_plural = _("parent-child links")
        # In addition to the LinkParent use-case checks (patterns §6.2): the last line of defence
        # against a concurrent duplicate and against linking an account to itself.
        constraints = (
            models.UniqueConstraint(fields=["parent", "student"], name="uniq_parent_student"),
            models.CheckConstraint(
                condition=~models.Q(parent=models.F("student")), name="parent_not_student"
            ),
        )

    def __str__(self) -> str:
        return f"{self.parent} → {self.student}"
