from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models

from infrastructure.persistence.accounts.managers import UserManager

# Values mirror domain.accounts.roles.Role (Story 1.3 asserts equality).
ROLE_CHOICES = [
    ("STUDENT", "Student"),
    ("TEACHER", "Teacher"),
    ("PARENT", "Parent/Guardian"),
    ("ADMIN", "Admin"),
]
LANGUAGE_CHOICES = [("ro", "Română"), ("en", "English")]


class UserModel(AbstractUser):
    first_name = None  # type: ignore[assignment]  # replaced by full_name (requirements)
    last_name = None  # type: ignore[assignment]
    full_name = models.CharField(max_length=150)
    date_of_birth = models.DateField()
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    preferred_language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default="ro")

    objects: ClassVar[UserManager] = UserManager()
    REQUIRED_FIELDS: ClassVar[list[str]] = ["full_name", "date_of_birth"]

    class Meta:
        db_table = "accounts_user"

    def __str__(self) -> str:
        return self.username

    def get_full_name(self) -> str:
        return self.full_name

    def get_short_name(self) -> str:
        return self.full_name
