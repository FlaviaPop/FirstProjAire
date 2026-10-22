"""BUG-003: CSRF failures render the localized 403 page (Story 1.1), not Django's default."""

import logging

import pytest
from django.conf import settings
from django.test import Client

pytestmark = pytest.mark.django_db
LOGIN = "/ro/accounts/login/"  # HTMX test


def test_csrf_failure_view_is_configured():
    assert settings.CSRF_FAILURE_VIEW == "infrastructure.web.common.errors.csrf_failure"


@pytest.mark.parametrize(
    ("url", "title"),
    [("/ro/accounts/login/", "Acces interzis"), ("/en/accounts/login/", "Access denied")],
)
def test_post_without_token_renders_the_localized_403_page(caplog, url, title, compiled_catalogues):
    strict = Client(enforce_csrf_checks=True)

    with caplog.at_level(logging.WARNING, logger="infrastructure.web.common.errors"):
        response = strict.post(url, {"username": "ana", "password": "x"})

    content = response.content.decode()
    assert response.status_code == 403
    assert "errors/403.html" in [t.name for t in response.templates]
    assert title in content
    assert "CSRF verification failed" not in content  # Django's default page
    record = next(r for r in caplog.records if r.getMessage() == "csrf.failure")
    assert record.levelname == "WARNING"
    assert record.reason  # Django's reason is logged for operators ...
    assert record.reason not in content  # ... but never shown to the user


def test_htmx_post_without_token_gets_the_partial():
    strict = Client(enforce_csrf_checks=True)

    response = strict.post(LOGIN, {"username": "ana", "password": "x"}, HTTP_HX_REQUEST="true")

    assert response.status_code == 403
    assert "errors/_partial.html" in [t.name for t in response.templates]
