"""Argon2id storage and hash upgrade, run with the real (base) hashers, not the test MD5 one."""

import importlib

import pytest
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from tests.factories.accounts import StudentFactory

pytestmark = pytest.mark.django_db
PASSWORD = "pilot-pass-123"


@pytest.fixture
def real_hashers(settings):
    settings.PASSWORD_HASHERS = importlib.import_module("config.settings.base").PASSWORD_HASHERS


def test_new_passwords_are_stored_with_argon2id(real_hashers):
    student = StudentFactory(username="ana")

    student.refresh_from_db()
    assert student.password.startswith("argon2$argon2id$")


def test_pbkdf2_hash_is_upgraded_to_argon2id_on_login(real_hashers, client):
    student = StudentFactory(username="ana")
    student.password = make_password(PASSWORD, hasher="pbkdf2_sha256")
    student.save(update_fields=["password"])

    response = client.post("/ro/accounts/login/", {"username": "ana", "password": PASSWORD})

    student.refresh_from_db()
    assert response.status_code == 302
    assert student.password.startswith("argon2$argon2id$")


@pytest.mark.parametrize(
    ("password", "code"),
    [
        ("Ab3$xyz", "password_too_short"),
        ("password123", "password_too_common"),
        ("83920174", "password_entirely_numeric"),
    ],
)
def test_password_validators_reject_weak_passwords(password, code):
    with pytest.raises(ValidationError) as excinfo:
        validate_password(password)

    assert code in {error.code for error in excinfo.value.error_list}


def test_password_validators_accept_a_reasonable_password():
    assert validate_password("Lună-plină-42") is None
