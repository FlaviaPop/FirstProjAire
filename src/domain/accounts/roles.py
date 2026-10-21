"""The four canonical roles from docs/requirements.md (Roles & Permissions Matrix)."""

from enum import StrEnum


class Role(StrEnum):
    """A user's single role. Values equal the persisted `UserModel.role` choices."""

    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    PARENT = "PARENT"
    ADMIN = "ADMIN"


def parse_role(value: str) -> Role | None:
    """Return the Role for a persisted value, or None for anything unknown (never raises).

    Args:
        value: The raw role string, e.g. from `request.user.role`.

    Returns:
        The matching Role, or None so callers deny access instead of crashing.
    """
    try:
        return Role(value)
    except ValueError:
        return None
