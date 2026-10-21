import json
from datetime import UTC

import pytest
from axes.signals import user_locked_out
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db import DatabaseError

from infrastructure.persistence.audit.models import AuditLogModel
from infrastructure.persistence.audit.repositories import FORBIDDEN_METADATA_KEYS, DjangoAuditPort
from tests.factories.accounts import UserFactory
from tests.fakes import FixedClock

pytestmark = pytest.mark.django_db


def _rows():
    return list(
        AuditLogModel.objects.order_by("created_at", "id").values_list(
            "action", "actor_id", "actor_username", "ip_address"
        )
    )


def test_login_and_logout_signals_write_rows(rf):
    user = UserFactory(username="ana")
    request = rf.get("/", REMOTE_ADDR="127.0.0.1")

    user_logged_in.send(sender=type(user), request=request, user=user)
    user_logged_out.send(sender=type(user), request=request, user=user)

    assert _rows() == [
        ("auth.login", user.pk, "ana", "127.0.0.1"),
        ("auth.logout", user.pk, "ana", "127.0.0.1"),
    ]


def test_logout_without_user_writes_no_row(rf):
    user_logged_out.send(sender=None, request=rf.get("/"), user=None)

    assert AuditLogModel.objects.count() == 0


def test_failed_login_records_attempted_username_never_password(rf):
    user_login_failed.send(
        sender=None,
        credentials={"username": "ghost", "password": "********"},
        request=rf.post("/", REMOTE_ADDR="10.1.2.3"),
    )

    row = AuditLogModel.objects.get()
    assert (row.action, row.actor_id, row.actor_username) == ("auth.login_failed", None, "ghost")
    assert row.ip_address == "10.1.2.3"
    assert row.metadata == {}


def test_failed_login_without_request_or_username_is_still_recorded():
    user_login_failed.send(sender=None, credentials={})

    row = AuditLogModel.objects.get()
    assert (row.action, row.actor_username, row.ip_address) == (
        "auth.login_failed",
        "(empty)",
        None,
    )


def test_lockout_signal_records_lockout(rf):
    user_locked_out.send(
        sender="axes",
        request=rf.post("/", REMOTE_ADDR="127.0.0.1"),
        username="ana",
        ip_address="127.0.0.1",
    )

    row = AuditLogModel.objects.get()
    assert (row.action, row.actor_id, row.actor_username, row.ip_address) == (
        "auth.lockout",
        None,
        "ana",
        "127.0.0.1",
    )


def test_each_signal_is_connected_exactly_once(rf):
    user = UserFactory()

    user_logged_in.send(sender=type(user), request=rf.get("/"), user=user)

    assert AuditLogModel.objects.count() == 1


def test_rows_are_append_only():
    DjangoAuditPort(FixedClock()).record("auth.login", actor_username="ana")
    row = AuditLogModel.objects.get()

    row.actor_username = "mallory"
    with pytest.raises(PermissionError, match="append-only"):
        row.save()
    with pytest.raises(PermissionError, match="append-only"):
        row.delete()
    with pytest.raises(PermissionError, match="append-only"):
        AuditLogModel.objects.all().delete()
    with pytest.raises(PermissionError, match="append-only"):
        AuditLogModel.objects.filter(pk=row.pk).update(actor_username="mallory")
    assert AuditLogModel.objects.get().actor_username == "ana"


def test_deleting_user_keeps_rows_with_username():
    user = UserFactory(username="ana")
    DjangoAuditPort(FixedClock()).record("auth.login", actor_id=user.pk, actor_username="ana")

    user.delete()

    row = AuditLogModel.objects.get()
    assert (row.actor_id, row.actor_username) == (None, "ana")


@pytest.mark.parametrize("key", sorted(FORBIDDEN_METADATA_KEYS))
def test_forbidden_metadata_is_rejected(key):
    with pytest.raises(ValueError, match=key):
        DjangoAuditPort(FixedClock()).record("x", metadata={key: "secret"})

    assert AuditLogModel.objects.count() == 0


def test_target_and_metadata_are_stored():
    DjangoAuditPort(FixedClock()).record(
        "test.submitted", actor_id=None, target=("test", "7"), metadata={"score": 87}
    )

    row = AuditLogModel.objects.get()
    assert (row.target_type, row.target_id, row.metadata) == ("test", "7", {"score": 87})


def test_audit_failure_does_not_break_login_signal(rf, monkeypatch, capfd):
    def boom(*args, **kwargs):
        raise DatabaseError("database is locked")

    monkeypatch.setattr(DjangoAuditPort, "record", boom)
    user = UserFactory()

    user_logged_in.send(sender=type(user), request=rf.get("/"), user=user)  # must not raise

    lines = [json.loads(line) for line in capfd.readouterr().out.splitlines() if line.strip()]
    failure = next(line for line in lines if line["event"] == "audit.write_failed")
    assert failure["level"] == "ERROR"
    assert failure["audit_action"] == "auth.login"
    assert "database is locked" not in json.dumps(failure)


def test_non_database_errors_propagate(rf, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("bug")

    monkeypatch.setattr(DjangoAuditPort, "record", boom)
    user = UserFactory()

    with pytest.raises(RuntimeError):
        user_logged_in.send(sender=type(user), request=rf.get("/"), user=user)


def test_created_at_comes_from_injected_clock():
    clock = FixedClock()
    DjangoAuditPort(clock).record("auth.login", actor_username="ana")

    created_at = AuditLogModel.objects.get().created_at
    assert created_at == clock.at
    assert created_at.tzinfo is not None
    assert created_at.utcoffset() == UTC.utcoffset(None)


def test_str_names_action_actor_and_time():
    DjangoAuditPort(FixedClock()).record("auth.login", actor_username="ana")

    assert str(AuditLogModel.objects.get()) == "auth.login by ana at 2026-11-02 09:00"
