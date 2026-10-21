"""Security configuration of Story 1.2, asserted against the real (base/prod) settings."""

import datetime
import importlib
import runpy
from pathlib import Path

import pytest
from django.conf import settings as django_settings

pytestmark = pytest.mark.django_db
EXPECTED_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "font-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'self'"
)
HASHERS = "django.contrib.auth.hashers"
VALIDATION = "django.contrib.auth.password_validation"


@pytest.fixture
def base():
    return importlib.import_module("config.settings.base")


def test_argon2_is_the_primary_hasher_in_real_settings(base):
    assert base.PASSWORD_HASHERS[0].endswith("Argon2PasswordHasher")


def test_password_hashers_keep_fallbacks_for_upgrade(base):
    assert [
        f"{HASHERS}.Argon2PasswordHasher",
        f"{HASHERS}.PBKDF2PasswordHasher",
        f"{HASHERS}.PBKDF2SHA1PasswordHasher",
        f"{HASHERS}.ScryptPasswordHasher",
    ] == base.PASSWORD_HASHERS


def test_password_validators_are_min_length_8_common_and_numeric(base):
    assert [
        {"NAME": f"{VALIDATION}.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
        {"NAME": f"{VALIDATION}.CommonPasswordValidator"},
        {"NAME": f"{VALIDATION}.NumericPasswordValidator"},
    ] == base.AUTH_PASSWORD_VALIDATORS


def test_axes_policy_constants(base):
    assert base.AXES_FAILURE_LIMIT == 5
    assert datetime.timedelta(minutes=15) == base.AXES_COOLOFF_TIME
    assert base.AXES_LOCKOUT_PARAMETERS == [["username", "ip_address"]]
    assert base.AXES_RESET_ON_SUCCESS is True
    assert base.AXES_LOCKOUT_TEMPLATE == "accounts/locked_out.html"
    assert base.AXES_HTTP_RESPONSE_CODE == 429
    assert base.AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT is False
    assert base.AXES_IPWARE_PROXY_COUNT == 0


def test_axes_proxy_count_comes_from_the_environment(base, monkeypatch):
    monkeypatch.setenv("AXES_PROXY_COUNT", "2")

    namespace = runpy.run_path(base.__file__)  # a fresh evaluation, not the cached module

    assert namespace["AXES_IPWARE_PROXY_COUNT"] == 2


def test_axes_backend_runs_before_the_model_backend(base):
    assert base.AUTHENTICATION_BACKENDS == [
        "axes.backends.AxesStandaloneBackend",
        "django.contrib.auth.backends.ModelBackend",
    ]
    assert "axes" in base.INSTALLED_APPS
    assert "csp" in base.INSTALLED_APPS


def test_axes_middleware_is_last_and_csp_follows_security(base):
    middleware = base.MIDDLEWARE

    assert middleware[-1] == "axes.middleware.AxesMiddleware"
    security = middleware.index("django.middleware.security.SecurityMiddleware")
    assert middleware[security + 1] == "csp.middleware.CSPMiddleware"
    assert security < middleware.index("django.contrib.sessions.middleware.SessionMiddleware")


def test_session_policy(base):
    assert base.SESSION_ENGINE == "django.contrib.sessions.backends.db"
    assert base.SESSION_COOKIE_AGE == 8 * 3600
    assert base.SESSION_COOKIE_HTTPONLY is True
    assert base.SESSION_COOKIE_SAMESITE == "Lax"
    assert base.CSRF_COOKIE_HTTPONLY is True
    assert base.LOGIN_URL == "accounts:login"


def test_prod_keeps_secure_cookies(base, monkeypatch):
    monkeypatch.setenv("DJANGO_SECRET_KEY", "x" * 50)
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "example.org")

    prod = runpy.run_path(str(Path(base.__file__).with_name("prod.py")))

    assert prod["SESSION_COOKIE_SECURE"] is True
    assert prod["CSRF_COOKIE_SECURE"] is True
    assert prod["PASSWORD_HASHERS"][0].endswith("Argon2PasswordHasher")


def test_active_settings_inherit_the_policy():
    assert django_settings.SESSION_COOKIE_AGE == 28800
    assert django_settings.MIDDLEWARE[-1] == "axes.middleware.AxesMiddleware"


@pytest.mark.parametrize("url", ["/ro/accounts/login/", "/en/accounts/login/"])
def test_security_headers_on_login_page(client, url):
    response = client.get(url)

    assert response["X-Frame-Options"] == "DENY"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["Referrer-Policy"] == "same-origin"
    assert sorted(response["Content-Security-Policy"].split("; ")) == sorted(
        EXPECTED_CSP.split("; ")
    )


def test_security_headers_on_redirects(client):
    from tests.factories.accounts import StudentFactory

    StudentFactory(username="ana")

    response = client.post("/ro/accounts/login/", {"username": "ana", "password": "pilot-pass-123"})

    assert response.status_code == 302
    assert response["X-Frame-Options"] == "DENY"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["Referrer-Policy"] == "same-origin"
    assert sorted(response["Content-Security-Policy"].split("; ")) == sorted(
        EXPECTED_CSP.split("; ")
    )


def test_session_cookie_flags(client):
    from tests.factories.accounts import StudentFactory

    StudentFactory(username="ana")
    client.post("/ro/accounts/login/", {"username": "ana", "password": "pilot-pass-123"})
    cookie = client.cookies["sessionid"]

    assert cookie["httponly"] is True
    assert cookie["samesite"] == "Lax"
    assert int(cookie["max-age"]) == 8 * 3600


def test_expired_session_is_anonymous(student_client):
    from django.contrib.sessions.models import Session
    from django.utils import timezone

    Session.objects.update(expire_date=timezone.now() - datetime.timedelta(seconds=1))

    response = student_client.get("/ro/accounts/login/")

    assert response.wsgi_request.user.is_anonymous


def test_login_session_expires_eight_hours_after_sign_in(client):
    from django.contrib.sessions.models import Session
    from django.utils import timezone

    from tests.factories.accounts import StudentFactory

    StudentFactory(username="ana")
    client.post("/ro/accounts/login/", {"username": "ana", "password": "pilot-pass-123"})

    lifetime = Session.objects.get().expire_date - timezone.now()
    assert datetime.timedelta(hours=8) - datetime.timedelta(minutes=1) < lifetime
    assert lifetime <= datetime.timedelta(hours=8)


def test_session_is_still_valid_before_expiry(student_client):
    from django.contrib.sessions.models import Session
    from django.utils import timezone

    Session.objects.update(expire_date=timezone.now() + datetime.timedelta(minutes=1))

    response = student_client.get("/ro/accounts/login/")

    assert response.wsgi_request.user.is_authenticated


def test_login_and_logout_are_public_routes():
    from infrastructure.web.common.decorators import PUBLIC_URL_NAMES

    assert {"accounts:login", "accounts:logout"} <= PUBLIC_URL_NAMES
