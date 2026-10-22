import datetime

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection

from tests.factories.accounts import UserFactory

pytestmark = pytest.mark.django_db


def test_auth_user_model_is_custom_accounts_model():
    assert settings.AUTH_USER_MODEL == "accounts.UserModel"
    assert get_user_model()._meta.db_table == "accounts_user"


def test_create_user_stores_profile_fields_and_hashes_password():
    user = get_user_model().objects.create_user(
        username="ana",
        password="pilot-pass-123",
        full_name="Ana Pop",
        date_of_birth=datetime.date(2018, 3, 2),
        role="STUDENT",
    )

    user.refresh_from_db()
    assert (user.full_name, user.role, user.preferred_language) == ("Ana Pop", "STUDENT", "ro")
    assert user.password != "pilot-pass-123"
    assert user.check_password("pilot-pass-123")
    assert user.get_full_name() == "Ana Pop"
    assert user.get_short_name() == "Ana Pop"
    assert str(user) == "ana"


def test_create_superuser_is_always_admin_role():
    admin = get_user_model().objects.create_superuser(
        username="root",
        password="x-strong-pass-9",
        full_name="Admin One",
        date_of_birth=datetime.date(1990, 1, 1),
        role="STUDENT",
    )

    assert (admin.role, admin.is_staff, admin.is_superuser) == ("ADMIN", True, True)


def test_createsuperuser_command_creates_admin_role():
    call_command(
        "createsuperuser",
        interactive=False,
        username="boot",
        full_name="Boot Admin",
        date_of_birth="1985-06-15",
        verbosity=0,
    )

    admin = get_user_model().objects.get(username="boot")
    assert (admin.role, admin.is_staff, admin.is_superuser) == ("ADMIN", True, True)


def test_role_and_language_choices_are_the_canonical_values():
    model = get_user_model()

    assert [value for value, _ in model._meta.get_field("role").choices] == [
        "STUDENT",
        "TEACHER",
        "PARENT",
        "ADMIN",
    ]
    assert [value for value, _ in model._meta.get_field("preferred_language").choices] == [
        "ro",
        "en",
    ]
    assert model._meta.get_field("full_name").max_length == 150


def test_first_and_last_name_columns_are_removed():
    columns = {
        c.name
        for c in connection.introspection.get_table_description(
            connection.cursor(), "accounts_user"
        )
    }

    assert {"full_name", "date_of_birth", "role", "preferred_language"} <= columns
    assert not {"first_name", "last_name"} & columns


def test_user_factory_builds_a_valid_student():
    user = UserFactory()

    user.full_clean()
    assert user.role == "STUDENT"
    assert user.check_password("pilot-pass-123")


def test_sqlite_runs_in_wal_mode_with_immediate_transactions():
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]

    assert journal_mode.lower() == "wal"
    assert connection.settings_dict["OPTIONS"]["transaction_mode"] == "IMMEDIATE"
    assert connection.settings_dict["OPTIONS"]["timeout"] == 20
    assert settings.DATABASES["default"]["ATOMIC_REQUESTS"] is False


# --- Story 1.9 AC 1: Django admin access follows the platform role -------------------------
@pytest.mark.parametrize(
    ("role", "is_admin"),
    [("STUDENT", False), ("TEACHER", False), ("PARENT", False), ("ADMIN", True)],
)
def test_staff_flags_are_derived_from_the_role_on_create(role, is_admin):
    user = UserFactory(role=role, is_staff=not is_admin, is_superuser=not is_admin)

    user.refresh_from_db()
    assert (user.is_staff, user.is_superuser) == (is_admin, is_admin)


@pytest.mark.parametrize("new_role", ["STUDENT", "TEACHER", "PARENT"])
def test_leaving_the_admin_role_revokes_the_staff_flags(new_role):
    user = UserFactory(role="ADMIN")

    user.role = new_role
    user.save()

    user.refresh_from_db()
    assert (user.is_staff, user.is_superuser) == (False, False)


def test_becoming_admin_grants_the_staff_flags():
    user = UserFactory(role="TEACHER")

    user.role = "ADMIN"
    user.save()

    user.refresh_from_db()
    assert (user.is_staff, user.is_superuser) == (True, True)


def test_partial_save_of_the_role_also_saves_the_staff_flags():
    user = UserFactory(role="ADMIN")

    user.role = "PARENT"
    user.save(update_fields=["role"])

    user.refresh_from_db()
    assert (user.role, user.is_staff, user.is_superuser) == ("PARENT", False, False)


def test_partial_save_of_other_fields_leaves_the_staff_flags_alone():
    user = UserFactory(role="ADMIN")

    user.full_name = "Renamed"
    user.save(update_fields=["full_name"])

    user.refresh_from_db()
    assert (user.full_name, user.is_staff) == ("Renamed", True)
