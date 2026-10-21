"""django-axes brute-force protection: 5 failures per username+IP lock for 15 minutes."""

import datetime
import logging

import pytest
from axes.models import AccessAttempt
from axes.signals import user_locked_out
from django.contrib.sessions.models import Session
from django.utils import timezone

from tests.factories.accounts import StudentFactory

pytestmark = pytest.mark.django_db
LOGIN = "/ro/accounts/login/"
LOGIN_EN = "/en/accounts/login/"
PASSWORD = "pilot-pass-123"
WRONG = "wrong-pass-1"
LOCKOUT_SENTENCE = "Too many failed attempts. Try again in 15 minutes or ask the administrator."


def _post(client, username, password=PASSWORD, url=LOGIN, **extra):
    return client.post(url, {"username": username, "password": password}, **extra)


def _fail(client, times, username="ana", **extra):
    return [_post(client, username, WRONG, **extra).status_code for _ in range(times)]


def _age_attempts(minutes):
    AccessAttempt.objects.update(attempt_time=timezone.now() - datetime.timedelta(minutes=minutes))


def test_empty_fields_are_not_counted_as_attempts(client):
    _post(client, "", "")
    _post(client, "ana", "")
    _post(client, "", PASSWORD)

    assert AccessAttempt.objects.count() == 0


def test_each_failure_is_recorded_for_username_and_ip(client):
    StudentFactory(username="ana")

    _fail(client, 4)

    attempt = AccessAttempt.objects.get()
    assert attempt.username == "ana"
    assert attempt.ip_address == "127.0.0.1"
    assert attempt.failures_since_start == 4


def test_four_failures_still_allow_the_right_password(client):
    StudentFactory(username="ana")

    assert _fail(client, 4) == [200, 200, 200, 200]
    assert _post(client, "ana").status_code == 302


def test_fifth_failure_locks_even_correct_password(client):
    StudentFactory(username="ana")
    assert _fail(client, 4) == [200, 200, 200, 200]

    assert _post(client, "ana", WRONG).status_code == 429
    assert _post(client, "ana").status_code == 429
    assert Session.objects.count() == 0


def test_lockout_page_explains_the_cool_off(client):
    StudentFactory(username="ana")
    _fail(client, 4, url=LOGIN_EN)

    response = _post(client, "ana", WRONG, url=LOGIN_EN)

    content = response.content.decode()
    assert response.status_code == 429
    # The view renders the form first; AxesMiddleware then replaces the response.
    assert "accounts/locked_out.html" in [t.name for t in response.templates]
    assert 'name="password"' not in content
    assert "Too many attempts" in content
    assert LOCKOUT_SENTENCE in content
    assert "15" in content
    assert content.count("<h1") == 1
    assert '<html lang="en">' in content


def test_lockout_page_has_the_security_headers(client):
    StudentFactory(username="ana")
    _fail(client, 5)

    response = _post(client, "ana")

    assert response.status_code == 429
    assert response["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in response["Content-Security-Policy"]


def test_lockout_sends_the_user_locked_out_signal(client):
    StudentFactory(username="ana")
    received = []

    def _receiver(sender, **kwargs):
        received.append(kwargs["username"])

    user_locked_out.connect(_receiver)
    try:
        _fail(client, 5)
    finally:
        user_locked_out.disconnect(_receiver)

    assert received == ["ana"]


def test_lockout_is_still_active_before_fifteen_minutes(client):
    StudentFactory(username="ana")
    _fail(client, 5)
    _age_attempts(14)

    assert _post(client, "ana").status_code == 429


def test_correct_login_succeeds_after_the_cool_off(client):
    StudentFactory(username="ana")
    _fail(client, 5)
    _age_attempts(16)

    response = _post(client, "ana")

    assert response.status_code == 302
    assert AccessAttempt.objects.filter(username="ana").count() == 0


def test_attempts_during_cool_off_have_no_side_effect(client):
    StudentFactory(username="ana")
    _fail(client, 5)
    locked = AccessAttempt.objects.get()

    statuses = [_post(client, "ana", WRONG).status_code, _post(client, "ana").status_code]

    after = AccessAttempt.objects.get()
    assert statuses == [429, 429]
    assert (after.failures_since_start, after.attempt_time) == (5, locked.attempt_time)


def test_cool_off_counts_from_the_lockout_not_from_later_attempts(client):
    StudentFactory(username="ana")
    _fail(client, 5)
    _age_attempts(10)
    assert _post(client, "ana").status_code == 429

    _age_attempts(16)

    assert _post(client, "ana").status_code == 302


def test_success_resets_failure_counter(client):
    StudentFactory(username="ana")
    _fail(client, 4)
    _post(client, "ana")
    client.post("/ro/accounts/logout/")

    assert _fail(client, 4) == [200, 200, 200, 200]


def test_lockout_is_per_username_and_ip(client):
    StudentFactory(username="ana")
    StudentFactory(username="bob")
    _fail(client, 5, REMOTE_ADDR="10.0.0.1")

    other_ip = _post(client, "ana", REMOTE_ADDR="10.0.0.2")
    client.post("/ro/accounts/logout/")
    other_user = _post(client, "bob", REMOTE_ADDR="10.0.0.1")

    assert other_ip.status_code == 302
    assert other_user.status_code == 302


def test_axes_logs_never_contain_password_or_username(client, caplog):
    StudentFactory(username="ana")

    with caplog.at_level(logging.DEBUG):
        _fail(client, 5)
        _post(client, "ana")

    assert "AXES" in caplog.text
    assert WRONG not in caplog.text
    assert PASSWORD not in caplog.text
    assert "'ana'" not in caplog.text
