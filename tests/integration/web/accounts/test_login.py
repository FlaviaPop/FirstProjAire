"""GET/POST /<lang>/accounts/login/ — the System responses table of Story 1.2."""

import pytest
from django.contrib.sessions.models import Session

from tests.factories.accounts import StudentFactory, TeacherFactory

pytestmark = pytest.mark.django_db
LOGIN = "/ro/accounts/login/"
LOGIN_EN = "/en/accounts/login/"
PASSWORD = "pilot-pass-123"
GENERIC_ERROR = "Incorrect username or password."


def _post(client, username, password=PASSWORD, url=LOGIN, **extra):
    return client.post(url, {"username": username, "password": password, **extra})


@pytest.mark.parametrize("url", [LOGIN, LOGIN_EN])
def test_login_page_is_public_in_both_languages(client, url):
    response = client.get(url)

    assert response.status_code == 200
    assert b'name="username"' in response.content
    assert b'name="password"' in response.content
    assert b"csrfmiddlewaretoken" in response.content


def test_login_page_renders_in_the_url_language(client):
    response = client.get(LOGIN_EN)

    assert b'<html lang="en">' in response.content
    assert b"Sign in" in response.content


@pytest.mark.parametrize("language", ["ro", "en"])
def test_valid_login_redirects_to_preferred_language_home(client, language):
    StudentFactory(username="ana", preferred_language=language)

    response = _post(client, "ana")

    assert response.status_code == 302
    assert response["Location"] == f"/{language}/"


def test_valid_login_authenticates_the_session(client):
    student = StudentFactory(username="ana")

    _post(client, "ana")

    assert client.session["_auth_user_id"] == str(student.pk)
    assert Session.objects.count() == 1


def test_login_rotates_session_key(client, settings):
    TeacherFactory(username="t1")
    session = client.session  # create an anonymous pre-login session
    session["probe"] = 1
    session.save()
    client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

    _post(client, "t1")

    assert client.cookies[settings.SESSION_COOKIE_NAME].value != session.session_key


def test_repeat_login_while_signed_in_rotates_the_key_again(client, settings):
    TeacherFactory(username="t1", preferred_language="en")
    _post(client, "t1")
    first_key = client.cookies[settings.SESSION_COOKIE_NAME].value

    response = _post(client, "t1")

    assert response["Location"] == "/en/"
    assert client.cookies[settings.SESSION_COOKIE_NAME].value != first_key
    assert Session.objects.count() == 1


@pytest.mark.parametrize(
    "next_url",
    ["https://evil.example/", "//evil.example/x", "javascript:alert(1)", "http://testserver.evil/"],
)
def test_unsafe_next_is_ignored(client, next_url):
    StudentFactory(username="ana")

    response = _post(client, "ana", next=next_url)

    assert response["Location"] == "/ro/"


def test_safe_next_is_honoured(client):
    StudentFactory(username="ana")

    assert _post(client, "ana", next="/ro/catalogue/")["Location"] == "/ro/catalogue/"


def test_safe_next_from_query_string_is_honoured(client):
    StudentFactory(username="ana", preferred_language="en")

    response = client.post(
        f"{LOGIN}?next=/ro/catalogue/", {"username": "ana", "password": PASSWORD}
    )

    assert response["Location"] == "/ro/catalogue/"


def test_next_is_carried_into_the_form(client):
    response = client.get(f"{LOGIN}?next=/ro/catalogue/")

    assert b'name="next" value="/ro/catalogue/"' in response.content


@pytest.mark.parametrize("case", ["wrong_password", "unknown_user", "inactive"])
def test_failures_share_one_generic_message(client, case):
    StudentFactory(username="ana", is_active=case != "inactive")
    username = "ghost" if case == "unknown_user" else "ana"
    password = "nope-nope-1" if case == "wrong_password" else PASSWORD

    # English URL: the assertion must not depend on compiled RO catalogues.
    response = _post(client, username, password, url=LOGIN_EN)

    assert response.status_code == 200
    assert response.content.decode().count(GENERIC_ERROR) == 1
    assert b'role="alert"' in response.content


def test_failure_messages_are_byte_identical_across_cases(client):
    StudentFactory(username="ana")
    StudentFactory(username="off", is_active=False)

    bodies = [
        _post(client, user, pwd, url=LOGIN_EN).context["form"].non_field_errors()
        for user, pwd in [("ana", "nope-nope-1"), ("ghost", PASSWORD), ("off", PASSWORD)]
    ]

    assert bodies[0] == bodies[1] == bodies[2] == [GENERIC_ERROR]


def test_failed_login_keeps_username_and_clears_password(client):
    StudentFactory(username="ana")

    content = _post(client, "ana", "nope-nope-1").content.decode()

    assert 'value="ana"' in content
    assert "nope-nope-1" not in content


def test_failed_login_creates_no_session(client):
    StudentFactory(username="ana")

    _post(client, "ana", "nope-nope-1")

    assert Session.objects.count() == 0


def test_login_updates_only_last_login(client):
    student = StudentFactory(username="ana", preferred_language="en")
    before = {f.name: getattr(student, f.name) for f in student._meta.concrete_fields}

    _post(client, "ana")

    student.refresh_from_db()
    after = {f.name: getattr(student, f.name) for f in student._meta.concrete_fields}
    changed = {name for name in before if before[name] != after[name]}
    assert changed == {"last_login"}


@pytest.mark.parametrize(("username", "password"), [("", PASSWORD), ("ana", ""), ("", "")])
def test_missing_fields_show_field_level_required_error(client, username, password):
    StudentFactory(username="ana")

    response = _post(client, username, password, url=LOGIN_EN)

    assert response.status_code == 200
    assert b"This field is required." in response.content
    assert GENERIC_ERROR.encode() not in response.content
    assert b'aria-invalid="true"' in response.content


def test_post_without_csrf_is_rejected():
    from django.test import Client

    strict = Client(enforce_csrf_checks=True)

    assert strict.post(LOGIN, {"username": "x", "password": "y"}).status_code == 403


def test_post_with_csrf_token_signs_in_under_strict_checks():
    from django.test import Client

    StudentFactory(username="ana")
    strict = Client(enforce_csrf_checks=True)
    token = strict.get(LOGIN).context["csrf_token"]

    response = strict.post(
        LOGIN, {"username": "ana", "password": PASSWORD, "csrfmiddlewaretoken": str(token)}
    )

    assert response.status_code == 302
    assert response["Location"] == "/ro/"
