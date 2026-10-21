"""Story 1.1 wiring in the real settings and root URLConf (not a test URLConf)."""

import re
from pathlib import Path

import pytest
from django.conf import settings
from django.urls import get_resolver

from infrastructure.web.common import errors

pytestmark = pytest.mark.django_db

LOCALE_DIR = Path(__file__).resolve().parents[4] / "src/infrastructure/i18n/locale"
STORY_MSGIDS = [
    "Request could not be processed",
    "Access denied",
    "Page not found",
    "Already done",
    "Please check your input",
    "Something went wrong",
    "Your request could not be processed. Please try again.",
    "You do not have access to this page.",
    "We could not find this page.",
    "This has already been done and cannot be repeated.",
    "Please fix the following:",
    "Something went wrong on our side. Please try again later.",
    "Back to home",
    "Reference",
]


def test_request_id_middleware_is_first_and_domain_error_middleware_is_last_of_story_1_1():
    middleware = settings.MIDDLEWARE

    assert middleware[0] == "infrastructure.web.common.middleware.RequestIdMiddleware"
    assert middleware.index("infrastructure.web.common.middleware.DomainErrorMiddleware") > max(
        middleware.index(name) for name in middleware if name.startswith("django.")
    )


@pytest.mark.parametrize(
    ("status", "handler"),
    [
        (400, errors.handle_400),
        (403, errors.handle_403),
        (404, errors.handle_404),
        (500, errors.handle_500),
    ],
)
def test_root_urlconf_uses_the_shared_error_handlers(status, handler):
    assert get_resolver().resolve_error_handler(status) is handler


@pytest.mark.parametrize("url", ["/does-not-exist", "/ro/does-not-exist", "/en/does-not-exist"])
def test_unknown_url_renders_the_404_page(client, url):
    response = client.get(url)

    assert response.status_code == 404
    assert 'class="error-card"' in response.content.decode()
    assert len(response["X-Request-ID"]) == 32


def test_unknown_url_htmx_request_gets_the_partial(client):
    response = client.get("/ro/does-not-exist", headers={"HX-Request": "true"})

    assert response.status_code == 404
    assert b"<html" not in response.content
    assert b'role="alert"' in response.content


def test_disallowed_host_renders_the_400_page(client):
    response = client.get("/healthz", HTTP_HOST="evil.example")

    assert response.status_code == 400
    assert 'class="error-card"' in response.content.decode()
    assert "X-Request-ID" in response


def test_successful_response_keeps_status_and_body_and_gains_only_the_header(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}
    assert len(response["X-Request-ID"]) == 32


def _catalogue(language: str) -> dict[str, str]:
    text = (LOCALE_DIR / language / "LC_MESSAGES/django.po").read_text(encoding="utf-8")
    return dict(re.findall(r'^msgid "(.+)"\nmsgstr "(.*)"$', text, flags=re.MULTILINE))


@pytest.mark.parametrize("language", ["ro", "en"])
def test_every_story_message_has_a_translation_in_both_catalogues(language):
    catalogue = _catalogue(language)

    missing = [msgid for msgid in STORY_MSGIDS if not catalogue.get(msgid)]
    assert missing == []


def test_romanian_translations_differ_from_the_english_source():
    catalogue = _catalogue("ro")

    assert all(catalogue[msgid] != msgid for msgid in STORY_MSGIDS)


def test_every_generic_message_is_in_the_catalogue():
    assert {str(message) for message in errors.GENERIC_BY_STATUS.values()} <= set(STORY_MSGIDS)
