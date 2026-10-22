import pytest

from application.accounts.record_security_event import (
    RecordSecurityEvent,
    SecurityEvent,
    SecurityEventCommand,
)
from tests.fakes import FakeAuditPort, FakeUnitOfWork


class FakeDirectory:
    """Usernames that belong to real accounts; records every lookup."""

    def __init__(self, known=("ana",)):
        self.known, self.lookups = set(known), []

    def exists(self, username):
        self.lookups.append(username)
        return username in self.known


def fake_fingerprint(value):
    return f"fp{len(value):02d}"


@pytest.fixture
def setup():
    audit, uow, directory = FakeAuditPort(), FakeUnitOfWork(), FakeDirectory()
    return RecordSecurityEvent(audit, uow, directory, fake_fingerprint), audit, uow, directory


def test_security_events_are_the_four_auth_actions():
    assert [e.value for e in SecurityEvent] == [
        "auth.login",
        "auth.logout",
        "auth.login_failed",
        "auth.lockout",
    ]


@pytest.mark.parametrize("event", list(SecurityEvent))
def test_each_event_records_one_entry_in_a_unit_of_work(setup, event):
    use_case, audit, uow, _ = setup

    use_case.execute(SecurityEventCommand(event, "ana", 7, "10.0.0.1"))

    assert audit.records == [
        {
            "action": event.value,
            "actor_id": 7,
            "actor_username": "ana",
            "target": None,
            "metadata": {},
            "ip_address": "10.0.0.1",
        }
    ]
    assert (uow.entered, uow.committed, uow.rolled_back) == (1, 1, 0)


@pytest.mark.parametrize("event", [SecurityEvent.LOGIN_FAILED, SecurityEvent.LOCKOUT])
def test_empty_username_is_recorded_explicitly(setup, event):
    use_case, audit, _, _ = setup

    use_case.execute(SecurityEventCommand(event, ""))

    assert audit.records[0]["actor_username"] == "(empty)"
    assert audit.records[0]["actor_id"] is None


def test_long_username_is_truncated(setup):
    use_case, audit, _, _ = setup

    use_case.execute(SecurityEventCommand(SecurityEvent.LOGIN, "x" * 500, user_id=3))

    assert len(audit.records[0]["actor_username"]) == 150


def test_audit_failure_rolls_back_the_unit_of_work_and_propagates():
    class FailingAudit(FakeAuditPort):
        def record(self, action, **kwargs):
            raise RuntimeError("write failed")

    uow = FakeUnitOfWork()
    use_case = RecordSecurityEvent(FailingAudit(), uow, FakeDirectory(), fake_fingerprint)

    with pytest.raises(RuntimeError):
        use_case.execute(SecurityEventCommand(SecurityEvent.LOGIN, "ana", 1))

    assert (uow.entered, uow.committed, uow.rolled_back) == (1, 0, 1)


# --- Review v1 ISS-003: an unknown typed username may be a mistyped password ----------------


@pytest.mark.parametrize("event", [SecurityEvent.LOGIN_FAILED, SecurityEvent.LOCKOUT])
def test_unknown_username_is_never_stored_only_its_fingerprint(setup, event):
    use_case, audit, _, _ = setup

    use_case.execute(SecurityEventCommand(event, "Ana2018!secret"))

    stored = audit.records[0]["actor_username"]
    assert stored == "(unknown):fp14"
    assert "Ana2018" not in stored


@pytest.mark.parametrize("event", [SecurityEvent.LOGIN_FAILED, SecurityEvent.LOCKOUT])
def test_username_of_a_real_account_is_kept(setup, event):
    use_case, audit, _, directory = setup

    use_case.execute(SecurityEventCommand(event, "ana"))

    assert audit.records[0]["actor_username"] == "ana"
    assert directory.lookups == ["ana"]


@pytest.mark.parametrize("event", [SecurityEvent.LOGIN, SecurityEvent.LOGOUT])
def test_signed_in_events_never_look_up_or_mask(setup, event):
    use_case, audit, _, directory = setup

    use_case.execute(SecurityEventCommand(event, "ana", user_id=7))

    assert audit.records[0]["actor_username"] == "ana"
    assert directory.lookups == []


def test_same_unknown_text_gets_the_same_fingerprint(setup):
    use_case, audit, _, _ = setup

    for _ in range(2):
        use_case.execute(SecurityEventCommand(SecurityEvent.LOGIN_FAILED, "ghost"))

    assert audit.records[0]["actor_username"] == audit.records[1]["actor_username"]
