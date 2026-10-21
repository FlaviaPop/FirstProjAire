import pytest

from application.accounts.record_security_event import (
    RecordSecurityEvent,
    SecurityEvent,
    SecurityEventCommand,
)
from tests.fakes import FakeAuditPort, FakeUnitOfWork


@pytest.fixture
def setup():
    audit, uow = FakeAuditPort(), FakeUnitOfWork()
    return RecordSecurityEvent(audit, uow), audit, uow


def test_security_events_are_the_four_auth_actions():
    assert [e.value for e in SecurityEvent] == [
        "auth.login",
        "auth.logout",
        "auth.login_failed",
        "auth.lockout",
    ]


@pytest.mark.parametrize("event", list(SecurityEvent))
def test_each_event_records_one_entry_in_a_unit_of_work(setup, event):
    use_case, audit, uow = setup

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
    use_case, audit, _ = setup

    use_case.execute(SecurityEventCommand(event, ""))

    assert audit.records[0]["actor_username"] == "(empty)"
    assert audit.records[0]["actor_id"] is None


def test_long_username_is_truncated(setup):
    use_case, audit, _ = setup

    use_case.execute(SecurityEventCommand(SecurityEvent.LOGIN_FAILED, "x" * 500))

    assert len(audit.records[0]["actor_username"]) == 150


def test_audit_failure_rolls_back_the_unit_of_work_and_propagates():
    class FailingAudit(FakeAuditPort):
        def record(self, action, **kwargs):
            raise RuntimeError("write failed")

    uow = FakeUnitOfWork()

    with pytest.raises(RuntimeError):
        RecordSecurityEvent(FailingAudit(), uow).execute(
            SecurityEventCommand(SecurityEvent.LOGIN, "ana", 1)
        )

    assert (uow.entered, uow.committed, uow.rolled_back) == (1, 0, 1)
