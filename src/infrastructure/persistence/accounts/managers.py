from typing import TYPE_CHECKING, Any

from django.contrib.auth.models import UserManager as DjangoUserManager

if TYPE_CHECKING:
    from infrastructure.persistence.accounts.models import UserModel


class UserManager(DjangoUserManager["UserModel"]):
    def create_superuser(
        self,
        username: str,
        email: str | None = None,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "UserModel":
        # The first operator account is always an Admin in the platform's RBAC.
        extra_fields["role"] = "ADMIN"
        return super().create_superuser(username, email, password, **extra_fields)
