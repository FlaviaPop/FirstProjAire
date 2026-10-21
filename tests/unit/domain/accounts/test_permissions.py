import pytest

from domain.accounts.permissions import ROLE_PERMISSIONS, Permission, has_permission
from domain.accounts.roles import Role, parse_role

# Literal copy of docs/requirements.md → Roles & Permissions Matrix. Do NOT import from src.
EXPECTED = {
    "STUDENT": {"lessons:view", "exercises:complete", "tests:submit", "scores:view-own"},
    "TEACHER": {
        "content:create",
        "content:edit",
        "tests:configure",
        "scores:view-all",
        "content:resubmit",
    },
    "PARENT": {"child-progress:view", "child-scores:view"},
    "ADMIN": {
        "accounts:manage",
        "parents:link",
        "content:review",
        "content:block",
        "content:unblock",
        "scores:view-all",
    },
}


def test_permission_matrix_matches_requirements():
    actual = {role.value: {p.value for p in perms} for role, perms in ROLE_PERMISSIONS.items()}

    assert actual == EXPECTED


def test_permission_keys_are_exactly_the_sixteen_from_requirements():
    assert {p.value for p in Permission} == set().union(*EXPECTED.values())
    assert len(Permission) == 16


def test_matrix_is_read_only():
    with pytest.raises(TypeError):
        ROLE_PERMISSIONS[Role.STUDENT] = frozenset()  # type: ignore[index]


def test_matrix_values_are_frozensets():
    assert all(isinstance(perms, frozenset) for perms in ROLE_PERMISSIONS.values())


@pytest.mark.parametrize(
    ("role", "permission", "expected"),
    [
        (Role.STUDENT, Permission.TESTS_SUBMIT, True),
        (Role.STUDENT, Permission.CONTENT_EDIT, False),
        (Role.PARENT, Permission.SCORES_VIEW_ALL, False),
        (Role.ADMIN, Permission.LESSONS_VIEW, False),
        (Role.TEACHER, Permission.SCORES_VIEW_ALL, True),
    ],
)
def test_has_permission(role, permission, expected):
    assert has_permission(role, permission) is expected


@pytest.mark.parametrize("value", ["", "student", "SUPERHERO"])
def test_parse_role_rejects_unknown_values(value):
    assert parse_role(value) is None


@pytest.mark.parametrize("value", ["STUDENT", "TEACHER", "PARENT", "ADMIN"])
def test_parse_role_accepts_canonical_values(value):
    assert parse_role(value) is Role(value)
