"""AC 14: role factories and the shared logged-in client fixtures."""

import datetime

import pytest

from tests.factories.accounts import AdminFactory, ParentFactory, StudentFactory, TeacherFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("factory", "role", "born"),
    [
        (StudentFactory, "STUDENT", datetime.date(2018, 5, 1)),
        (TeacherFactory, "TEACHER", datetime.date(1985, 9, 15)),
        (ParentFactory, "PARENT", datetime.date(1987, 2, 20)),
        (AdminFactory, "ADMIN", datetime.date(1980, 1, 10)),
    ],
)
def test_each_role_factory_builds_a_valid_user(factory, role, born):
    user = factory()

    user.full_clean()
    assert (user.role, user.date_of_birth) == (role, born)
    assert user.check_password("pilot-pass-123")


def test_only_the_admin_factory_grants_staff_rights():
    assert (AdminFactory().is_staff, AdminFactory().is_superuser) == (True, True)
    assert StudentFactory().is_staff is False


def test_role_fixtures_have_fixed_usernames(student, other_student, teacher, parent, admin_user):
    users = [student, other_student, teacher, parent, admin_user]

    assert [u.username for u in users] == ["student1", "student2", "teacher1", "parent1", "admin1"]
    assert [u.role for u in users] == ["STUDENT", "STUDENT", "TEACHER", "PARENT", "ADMIN"]


@pytest.mark.parametrize(
    ("client_fixture", "username"),
    [
        ("student_client", "student1"),
        ("teacher_client", "teacher1"),
        ("parent_client", "parent1"),
        ("admin_client", "admin1"),
    ],
)
def test_logged_in_clients_are_authenticated_as_their_role(request, client_fixture, username):
    client = request.getfixturevalue(client_fixture)

    response = client.get("/ro/accounts/login/")

    assert response.wsgi_request.user.username == username
