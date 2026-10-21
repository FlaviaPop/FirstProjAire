"""Permission keys and the role → permission map (ADR-007: RBAC as a code-defined map)."""

from enum import StrEnum
from types import MappingProxyType

from domain.accounts.roles import Role


class Permission(StrEnum):
    """The 16 permission keys, spelled exactly as in docs/requirements.md."""

    LESSONS_VIEW = "lessons:view"
    EXERCISES_COMPLETE = "exercises:complete"
    TESTS_SUBMIT = "tests:submit"
    SCORES_VIEW_OWN = "scores:view-own"
    CONTENT_CREATE = "content:create"
    CONTENT_EDIT = "content:edit"
    TESTS_CONFIGURE = "tests:configure"
    SCORES_VIEW_ALL = "scores:view-all"
    CONTENT_RESUBMIT = "content:resubmit"
    CHILD_PROGRESS_VIEW = "child-progress:view"
    CHILD_SCORES_VIEW = "child-scores:view"
    ACCOUNTS_MANAGE = "accounts:manage"
    PARENTS_LINK = "parents:link"
    CONTENT_REVIEW = "content:review"
    CONTENT_BLOCK = "content:block"
    CONTENT_UNBLOCK = "content:unblock"


P = Permission
# Canonical copy of the Roles & Permissions Matrix in docs/requirements.md — keep verbatim.
ROLE_PERMISSIONS: MappingProxyType[Role, frozenset[Permission]] = MappingProxyType(
    {
        Role.STUDENT: frozenset(
            {P.LESSONS_VIEW, P.EXERCISES_COMPLETE, P.TESTS_SUBMIT, P.SCORES_VIEW_OWN}
        ),
        Role.TEACHER: frozenset(
            {
                P.CONTENT_CREATE,
                P.CONTENT_EDIT,
                P.TESTS_CONFIGURE,
                P.SCORES_VIEW_ALL,
                P.CONTENT_RESUBMIT,
            }
        ),
        Role.PARENT: frozenset({P.CHILD_PROGRESS_VIEW, P.CHILD_SCORES_VIEW}),
        Role.ADMIN: frozenset(
            {
                P.ACCOUNTS_MANAGE,
                P.PARENTS_LINK,
                P.CONTENT_REVIEW,
                P.CONTENT_BLOCK,
                P.CONTENT_UNBLOCK,
                P.SCORES_VIEW_ALL,
            }
        ),
    }
)


def has_permission(role: Role, permission: Permission) -> bool:
    """Return True if `role` holds `permission` in the requirements matrix."""
    return permission in ROLE_PERMISSIONS[role]
