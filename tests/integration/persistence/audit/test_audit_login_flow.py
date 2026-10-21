"""Audit rows produced by the real Story 1.2 login/logout/lockout views (not just signals)."""

import pytest

from infrastructure.persistence.audit.models import AuditLogModel
from tests.factories.accounts import StudentFactory

pytestmark = pytest.mark.django_db
LOGIN = "/ro/accounts/login/"
LOGOUT = "/ro/accounts/logout/"
PASSWORD = "pilot-pass-123"
WRONG = "wrong-pass-1"


def _post_login(client, username, password=PASSWORD):
    return client.post(LOGIN, {"username": username, "password": password})


def _actions(username):
    return list(
        AuditLogModel.objects.filter(actor_username=username)
        .order_by("created_at", "id")
        .values_list("action", flat=True)
    )


def test_login_then_logout_writes_exactly_two_rows(client):
    ana = StudentFactory(username="ana")

    assert _post_login(client, "ana").status_code == 302
    assert client.post(LOGOUT).status_code == 302

    rows = list(
        AuditLogModel.objects.order_by("created_at", "id").values(
            "action", "actor_id", "actor_username", "ip_address", "metadata"
        )
    )
    assert rows == [
        {
            "action": "auth.login",
            "actor_id": ana.pk,
            "actor_username": "ana",
            "ip_address": "127.0.0.1",
            "metadata": {},
        },
        {
            "action": "auth.logout",
            "actor_id": ana.pk,
            "actor_username": "ana",
            "ip_address": "127.0.0.1",
            "metadata": {},
        },
    ]


def test_second_login_is_a_second_row(client):
    StudentFactory(username="ana")

    _post_login(client, "ana")
    _post_login(client, "ana")

    assert _actions("ana") == ["auth.login", "auth.login"]


def test_wrong_password_and_unknown_user_record_failures(client):
    StudentFactory(username="ana")

    assert _post_login(client, "ana", WRONG).status_code == 200
    assert _post_login(client, "ghost", WRONG).status_code == 200

    assert _actions("ana") == ["auth.login_failed"]
    assert _actions("ghost") == ["auth.login_failed"]
    assert not AuditLogModel.objects.filter(actor_id__isnull=False).exists()


def test_fifth_failure_records_five_failures_and_one_lockout(client):
    StudentFactory(username="ana")

    statuses = [_post_login(client, "ana", WRONG).status_code for _ in range(5)]

    assert statuses == [200, 200, 200, 200, 429]
    # axes' own user_login_failed receiver fires user_locked_out before ours runs, so the
    # lockout row precedes the 5th failure row; the story requires the counts, not the order.
    assert sorted(_actions("ana")) == ["auth.lockout"] + ["auth.login_failed"] * 5


def test_attempts_during_cool_off_are_recorded_as_lockouts(client):
    StudentFactory(username="ana")
    for _ in range(5):
        _post_login(client, "ana", WRONG)

    assert _post_login(client, "ana").status_code == 429  # correct password, still locked

    assert _actions("ana").count("auth.lockout") == 2
    assert "auth.login" not in _actions("ana")


def test_login_response_is_unchanged_by_auditing(client):
    StudentFactory(username="ana")

    response = _post_login(client, "ana")

    assert response.status_code == 302
    assert "sessionid" in response.cookies
