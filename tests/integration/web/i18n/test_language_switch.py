import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

from infrastructure.web.common.decorators import PUBLIC_URL_NAMES
from tests.factories.accounts import StudentFactory, UserFactory

pytestmark = pytest.mark.django_db
URL = "/i18n/setlang/"


def _writes(queries):
    return [q["sql"] for q in queries if q["sql"].lstrip().upper().startswith("UPDATE")]


# --- settings and routing ------------------------------------------------------------------


def test_locale_middleware_sits_right_after_sessions():
    middleware = settings.MIDDLEWARE
    session = middleware.index("django.contrib.sessions.middleware.SessionMiddleware")

    assert middleware[session + 1] == "django.middleware.locale.LocaleMiddleware"


def test_language_settings_and_cookie_policy():
    assert settings.LANGUAGE_CODE == "ro"
    assert settings.LANGUAGES == [("ro", "Română"), ("en", "English")]
    assert settings.LANGUAGE_COOKIE_NAME == "django_language"
    assert settings.LANGUAGE_COOKIE_AGE == 31_536_000
    assert settings.LANGUAGE_COOKIE_SAMESITE == "Lax"
    assert settings.LANGUAGE_COOKIE_SECURE == settings.SESSION_COOKIE_SECURE


def test_set_language_is_public_and_outside_language_prefix():
    assert "set_language" in PUBLIC_URL_NAMES
    assert Client().get("/ro/i18n/setlang/").status_code == 404


# AC 2 is specified on "/", whose target `/<lang>/` (home:index) is created by Story 1.7.
# LocaleMiddleware only redirects to prefixed paths that resolve, so the same language choice
# (cookie > Accept-Language > "ro") is proven on an unprefixed path that exists today.
UNPREFIXED = "/accounts/login/"


def test_unprefixed_path_redirects_to_romanian_by_default(client):
    response = client.get(UNPREFIXED)

    assert (response.status_code, response["Location"]) == (302, "/ro/accounts/login/")


def test_unprefixed_path_honours_accept_language(client):
    response = client.get(UNPREFIXED, headers={"Accept-Language": "en-GB,en;q=0.9"})

    assert response["Location"] == "/en/accounts/login/"


def test_unprefixed_path_prefers_the_language_cookie(client):
    client.cookies["django_language"] = "en"

    response = client.get(UNPREFIXED, headers={"Accept-Language": "ro"})

    assert response["Location"] == "/en/accounts/login/"


@pytest.mark.parametrize(("prefix", "lang"), [("ro", "ro"), ("en", "en")])
def test_prefixed_pages_render_in_their_language(client, prefix, lang):
    response = client.get(f"/{prefix}/accounts/login/")

    assert response.status_code == 200
    assert f'<html lang="{lang}"' in response.content.decode()


# --- switching -----------------------------------------------------------------------------


def test_anonymous_switch_sets_cookie_and_translates_next(client):
    response = client.post(URL, {"language": "en", "next": "/ro/accounts/login/"})

    assert (response.status_code, response["Location"]) == (302, "/en/accounts/login/")
    assert response.cookies["django_language"].value == "en"


def test_switch_back_to_romanian(client):
    response = client.post(URL, {"language": "ro", "next": "/en/accounts/login/"})

    assert response["Location"] == "/ro/accounts/login/"
    assert response.cookies["django_language"].value == "ro"


def test_signed_in_switch_persists_only_for_current_user(client):
    me, other = UserFactory(preferred_language="ro"), UserFactory(preferred_language="ro")
    client.force_login(me)

    client.post(
        URL, {"language": "en", "next": "/ro/", "user_id": other.pk, "username": other.username}
    )

    users = get_user_model().objects
    assert users.get(pk=me.pk).preferred_language == "en"
    assert users.get(pk=other.pk).preferred_language == "ro"


def test_switching_to_the_current_preference_writes_nothing(client):
    me = UserFactory(preferred_language="en")
    client.force_login(me)

    with CaptureQueriesContext(connection) as queries:
        response = client.post(URL, {"language": "en", "next": "/en/"})

    assert response["Location"] == "/en/"
    assert response.cookies["django_language"].value == "en"
    assert [sql for sql in _writes(queries) if "accounts_user" in sql] == []


@pytest.mark.parametrize("code", ["de", "", "RO", "en-us"])
def test_invalid_language_changes_nothing(client, code):
    me = UserFactory(preferred_language="ro")
    client.force_login(me)

    with CaptureQueriesContext(connection) as queries:
        response = client.post(URL, {"language": code, "next": "/ro/accounts/login/"})

    assert (response.status_code, response["Location"]) == (302, "/ro/accounts/login/")
    assert "django_language" not in response.cookies
    assert [sql for sql in _writes(queries) if "accounts_user" in sql] == []
    assert get_user_model().objects.get(pk=me.pk).preferred_language == "ro"


def test_invalid_language_with_unsafe_next_goes_to_current_language_root(client):
    response = client.post(URL, {"language": "de", "next": "https://evil.example/"})

    assert response["Location"] == "/ro/"


@pytest.mark.parametrize("next_url", ["https://evil.example/", "//evil.example/", ""])
def test_unsafe_or_missing_next_falls_back_to_language_root(client, next_url):
    response = client.post(URL, {"language": "en", "next": next_url})

    assert response["Location"] == "/en/"


def test_get_is_not_allowed(client):
    assert client.get(URL).status_code == 405


def test_post_without_csrf_is_rejected_with_the_access_denied_page():
    strict = Client(enforce_csrf_checks=True)

    response = strict.post(URL, {"language": "en", "next": "/ro/"})

    assert response.status_code == 403
    assert "django_language" not in response.cookies


def test_saved_preference_drives_the_next_sign_in(client):
    StudentFactory(username="ana", preferred_language="ro")
    login = {"username": "ana", "password": "pilot-pass-123"}
    client.post("/ro/accounts/login/", login)

    client.post(URL, {"language": "en", "next": "/ro/"})
    client.post("/en/accounts/logout/")
    response = client.post("/ro/accounts/login/", login)

    assert response["Location"] == "/en/"
