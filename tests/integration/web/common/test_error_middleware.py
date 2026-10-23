import re

import pytest
from django.contrib.sessions.models import Session
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.urls import path
from django.utils import translation

from config.urls import urlpatterns as root_urlpatterns
from domain.common.errors import ConflictError, DomainError, NotFound, PolicyViolation, Violation
from infrastructure.web.common.errors import ERROR_MESSAGES


def _raise(exc):
    def view(request):
        raise exc

    return view


class AlreadySubmitted(ConflictError):  # noqa: N818 — mirrors the architecture's error name
    code = "test_already_submitted"


urlpatterns = [
    path("nf", _raise(NotFound())),
    path("pv", _raise(PolicyViolation([Violation("a_rule"), Violation("b_rule")]))),
    path("pv-params", _raise(PolicyViolation([Violation("points_total_not_100", {"total": 95})]))),
    path("pv-missing", _raise(PolicyViolation([Violation("needs_limit"), Violation("b_rule")]))),
    path("cf", _raise(ConflictError())),
    path("as", _raise(AlreadySubmitted())),
    path("de", _raise(DomainError())),
    path("pd", _raise(PermissionDenied())),
    path("so", _raise(SuspiciousOperation("bad"))),
    path("boom", _raise(RuntimeError("secret internal detail"))),
    # Story 1.7: the layout links sign-in, language switch and home, so the real routes follow.
    *root_urlpatterns,
]
handler400 = "infrastructure.web.common.errors.handle_400"
handler403 = "infrastructure.web.common.errors.handle_403"
handler404 = "infrastructure.web.common.errors.handle_404"
handler500 = "infrastructure.web.common.errors.handle_500"

pytestmark = [pytest.mark.django_db, pytest.mark.urls(__name__)]

TITLES = {
    "/de": "Request could not be processed",
    "/pd": "Access denied",
    "/nf": "Page not found",
    "/cf": "Already done",
    "/pv": "Please check your input",
    "/boom": "Something went wrong",
}
ICONS = {
    "/de": "warning-circle",
    "/pd": "lock-simple",
    "/nf": "compass",
    "/cf": "warning-circle",
    "/pv": "warning-circle",
    "/boom": "plugs",
}


@pytest.fixture
def english():
    # Works before Story 1.4 (override) and after it (LocaleMiddleware reads Accept-Language).
    with translation.override("en"):
        yield {"Accept-Language": "en"}


@pytest.fixture
def client(client):
    client.raise_request_exception = False
    return client


@pytest.mark.parametrize(
    ("url", "status"),
    [("/nf", 404), ("/pv", 422), ("/cf", 409), ("/de", 400), ("/pd", 403), ("/unknown", 404)],
)
def test_errors_map_to_status_and_full_page(client, url, status):
    response = client.get(url)

    assert response.status_code == status
    assert b"<html" in response.content
    assert b"<h1" in response.content


@pytest.mark.parametrize("url", list(TITLES))
def test_full_page_has_one_title_icon_and_back_to_home_link(client, english, url):
    content = client.get(url, headers=english).content.decode()

    assert content.count("<h1") == 1
    assert f">{TITLES[url]}</h1>" in content
    assert f"#{ICONS[url]}" in content
    assert 'aria-hidden="true"' in content
    assert '<a href="/">Back to home</a>' in content


@pytest.mark.parametrize(
    ("url", "message"),
    [
        ("/de", "Your request could not be processed. Please try again."),
        ("/pd", "You do not have access to this page."),
        ("/nf", "We could not find this page."),
        ("/cf", "This has already been done and cannot be repeated."),
        ("/pv", "Please fix the following:"),
        ("/boom", "Something went wrong on our side. Please try again later."),
    ],
)
def test_full_page_shows_the_generic_message_for_its_status(client, english, url, message):
    assert message in client.get(url, headers=english).content.decode()


@pytest.mark.parametrize("language", ["ro", "en"])
def test_html_lang_follows_the_active_language(client, language):
    with translation.override(language):
        content = client.get("/nf", headers={"Accept-Language": language}).content.decode()

    assert f'<html lang="{language}">' in content


def test_policy_violation_lists_every_violation(client, monkeypatch):
    monkeypatch.setitem(ERROR_MESSAGES, "a_rule", "Rule A broken")
    monkeypatch.setitem(ERROR_MESSAGES, "b_rule", "Rule B broken")

    content = client.get("/pv").content.decode()

    assert content.index("Rule A broken") < content.index("Rule B broken")
    assert content.count("<li>") == 2


def test_violation_message_is_formatted_with_its_params(client, monkeypatch):
    monkeypatch.setitem(
        ERROR_MESSAGES, "points_total_not_100", "Total points is {total}; it must be 100"
    )

    content = client.get("/pv-params").content.decode()

    assert "<li>Total points is 95; it must be 100</li>" in content


def test_unregistered_violation_code_is_shown_as_its_code(client):
    content = client.get("/pv").content.decode()

    assert "<li>a_rule</li>" in content
    assert "<li>b_rule</li>" in content


def test_registered_error_code_message_replaces_the_generic_text(client, english, monkeypatch):
    monkeypatch.setitem(ERROR_MESSAGES, "test_already_submitted", "You already submitted this test")

    response = client.get("/as", headers=english)

    assert response.status_code == 409
    assert "You already submitted this test" in response.content.decode()
    assert "This has already been done" not in response.content.decode()


def test_unknown_error_code_falls_back_to_the_generic_message(client, english):
    response = client.get("/as", headers=english)

    assert response.status_code == 409
    assert "This has already been done and cannot be repeated." in response.content.decode()


def test_htmx_request_gets_partial_with_same_status(client):
    response = client.get("/cf", headers={"HX-Request": "true"})

    assert response.status_code == 409
    assert b"<html" not in response.content
    assert b'role="alert"' in response.content


@pytest.mark.parametrize(
    ("url", "status"),
    [("/nf", 404), ("/pv", 422), ("/cf", 409), ("/de", 400), ("/pd", 403), ("/boom", 500)],
)
def test_every_error_has_an_htmx_partial_with_the_same_status(client, english, url, status):
    response = client.get(url, headers={"HX-Request": "true", **english})

    content = response.content.decode()
    assert response.status_code == status
    assert "<html" not in content
    assert 'class="error-partial" role="alert"' in content


def test_htmx_partial_lists_every_violation(client):
    content = client.get("/pv", headers={"HX-Request": "true"}).content.decode()

    assert content.index("a_rule") < content.index("b_rule")
    assert content.count("<li>") == 2


def test_unexpected_error_shows_reference_without_details(client, settings):
    settings.TRUST_INCOMING_REQUEST_ID = True  # the proxy's id (Story 1.1 review v1 ISS-004)
    response = client.get("/boom", headers={"X-Request-ID": "qa-ref-0001"})

    assert response.status_code == 500
    assert b"qa-ref-0001" in response.content
    assert b"secret internal detail" not in response.content
    assert b"Traceback" not in response.content


def test_reference_on_500_page_equals_the_response_request_id(client, english):
    response = client.get("/boom", headers=english)

    assert f"Reference: {response['X-Request-ID']}" in response.content.decode()


@pytest.mark.parametrize("url", ["/nf", "/pv", "/cf", "/de", "/pd"])
def test_reference_is_shown_only_on_the_500_page(client, url):
    response = client.get(url)

    assert response["X-Request-ID"] not in response.content.decode()
    assert "error-card__ref" not in response.content.decode()


def test_suspicious_operation_renders_the_400_page(client, english):
    response = client.get("/so", headers=english)

    assert response.status_code == 400
    assert "Request could not be processed" in response.content.decode()


def _without_tokens(response):
    """The body with this response's request id and CSRF token values removed."""
    body = response.content.decode().replace(response["X-Request-ID"], "")
    body = re.sub(r'(name="csrfmiddlewaretoken" value=")[^"]+', r"\1", body)
    return re.sub(r'("X-CSRFToken": ")[^"]+', r"\1", body)


def test_repeated_failure_gets_same_status_and_new_request_id(client):
    first, second = client.get("/nf"), client.get("/nf")

    assert first.status_code == second.status_code == 404
    # Story 1.7: the layout carries a per-response CSRF token; everything else is identical.
    assert _without_tokens(first) == _without_tokens(second)
    assert first["X-Request-ID"] != second["X-Request-ID"]


@pytest.mark.parametrize("url", ["/nf", "/pv", "/cf", "/de", "/pd", "/boom", "/unknown"])
def test_error_handling_creates_no_session_or_cookie(client, url):
    response = client.get(url)

    # Owner decision 2026-10-23 (Story 1.7): error pages carry the full layout, whose forms need
    # the anti-forgery token, so `csrftoken` is the one cookie allowed. Never a session.
    assert set(response.cookies) <= {"csrftoken"}
    assert Session.objects.count() == 0


def test_error_pages_carry_no_inline_style_or_script(client):
    for url in TITLES:
        content = client.get(url).content.decode()

        assert "<style" not in content
        # Story 1.7 loads htmx.min.js and ui.js from /static/; inline scripts stay forbidden.
        assert not re.search(r"<script(?![^>]*\bsrc=)", content)
        assert "style=" not in content


def test_violation_missing_a_message_param_still_renders_422(client, english, monkeypatch, caplog):
    # Review v1 ISS-002: a coding slip in a later story must not turn validation into a 500.
    monkeypatch.setitem(ERROR_MESSAGES, "needs_limit", "At most {limit} items allowed.")
    monkeypatch.setitem(ERROR_MESSAGES, "b_rule", "Rule B broken")

    response = client.get("/pv-missing", headers=english)

    content = response.content.decode()
    assert response.status_code == 422
    assert "At most {limit} items allowed." in content
    assert "Rule B broken" in content  # the other violations are still listed
    warning = next(r for r in caplog.records if r.getMessage() == "error_message.missing_param")
    assert (warning.levelname, warning.code, warning.param) == ("WARNING", "needs_limit", "limit")
