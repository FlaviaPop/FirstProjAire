"""Story 1.9 AC 9: account changes are audited with field NAMES only, never values."""

import pytest

from application.accounts.manage_account import ACCOUNT_ACTIONS, AuditAccountChange
from tests.fakes import FakeAuditPort, FakeUnitOfWork


@pytest.fixture
def setup():
    audit, uow = FakeAuditPort(), FakeUnitOfWork()
    return AuditAccountChange(audit, uow), audit, uow


def test_allowed_actions_are_the_account_actions_plus_lockout_cleared():
    assert (
        frozenset(
            {
                "accounts.created",
                "accounts.updated",
                "accounts.deleted",
                "accounts.password_changed",
                "accounts.role_changed",
                "auth.lockout_cleared",
            }
        )
        == ACCOUNT_ACTIONS
    )


def test_update_records_sorted_field_names_for_the_target_user(setup):
    use_case, audit, uow = setup

    use_case.execute("accounts.updated", 1, 42, "ana", ["full_name", "date_of_birth"])

    assert audit.records == [
        {
            "action": "accounts.updated",
            "actor_id": 1,
            "actor_username": "",
            "target": ("user", "42"),
            "metadata": {"fields": ["date_of_birth", "full_name"]},
            "ip_address": None,
        }
    ]
    assert (uow.entered, uow.committed) == (1, 1)


def test_password_form_fields_are_never_recorded(setup):
    use_case, audit, _ = setup

    use_case.execute("accounts.created", 1, 42, "ana", ["username", "password1", "password2"])

    assert audit.records[0]["metadata"] == {"fields": ["username"]}


def test_duplicate_field_names_are_recorded_once(setup):
    use_case, audit, _ = setup

    use_case.execute("accounts.updated", 1, 42, "ana", ("role", "role"))

    assert audit.records[0]["metadata"] == {"fields": ["role"]}


@pytest.mark.parametrize("action", ["accounts.deleted", "accounts.password_changed"])
def test_actions_without_changed_fields_record_an_empty_list(setup, action):
    use_case, audit, _ = setup

    use_case.execute(action, 1, 42, "ana")

    assert audit.records[0]["metadata"] == {"fields": []}


def test_lockout_cleared_has_no_fields_metadata(setup):
    use_case, audit, _ = setup

    use_case.execute("auth.lockout_cleared", 1, 42, "ana")

    assert audit.records[0]["action"] == "auth.lockout_cleared"
    assert audit.records[0]["target"] == ("user", "42")
    assert audit.records[0]["metadata"] == {}


def test_target_without_an_account_id_uses_the_label_truncated_to_64(setup):
    use_case, audit, _ = setup

    use_case.execute("auth.lockout_cleared", 1, None, "(unknown):" + "a" * 100)

    target_type, target_id = audit.records[0]["target"]
    assert target_type == "user"
    assert target_id == ("(unknown):" + "a" * 100)[:64]


def test_unknown_action_is_rejected_before_anything_is_written(setup):
    use_case, audit, uow = setup

    with pytest.raises(ValueError, match=r"accounts\.hacked"):
        use_case.execute("accounts.hacked", 1, 42, "ana")

    assert audit.records == []
    assert uow.entered == 0


def test_audit_failure_propagates_so_the_change_rolls_back(setup):
    _, _, uow = setup

    class BrokenAudit:
        def record(self, *args, **kwargs):
            raise RuntimeError("disk full")

    with pytest.raises(RuntimeError):
        AuditAccountChange(BrokenAudit(), uow).execute("accounts.deleted", 1, 42, "ana")

    assert uow.rolled_back == 1
