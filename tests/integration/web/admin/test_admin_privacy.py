"""Story 1.9 regression: no date of birth or password value ever reaches the audit log or logs.

One pass through every audited admin action, then a sweep of every audit row and log line.
"""

import pytest

from infrastructure.logging.sensitive import is_sensitive_key
from infrastructure.persistence.accounts.models import ParentChildLinkModel, UserModel
from infrastructure.persistence.audit.models import AuditLogModel
from tests.factories.accounts import ParentFactory
from tests.integration.web.admin.admin_helpers import LINKS, USERS, change_data

pytestmark = pytest.mark.django_db
DOB, NEW_DOB = "2018-03-02", "2017-12-24"
FIRST_PASSWORD, RESET_PASSWORD = "Ana-Start-2026!", "Ana-Reset-2026!"


def _run_every_audited_action(admin_client):
    admin_client.post(
        f"{USERS}add/",
        {
            "username": "ana",
            "full_name": "Ana Pop",
            "date_of_birth": DOB,
            "role": "STUDENT",
            "preferred_language": "ro",
            "password1": FIRST_PASSWORD,
            "password2": FIRST_PASSWORD,
        },
    )
    ana = UserModel.objects.get(username="ana")
    admin_client.post(f"{USERS}{ana.pk}/change/", change_data(ana, date_of_birth=NEW_DOB))
    admin_client.post(
        f"{USERS}{ana.pk}/password/", {"password1": RESET_PASSWORD, "password2": RESET_PASSWORD}
    )
    admin_client.post(f"{LINKS}add/", {"parent": ParentFactory().pk, "student": ana.pk})
    link = ParentChildLinkModel.objects.get()
    admin_client.post(f"{LINKS}{link.pk}/delete/", {"post": "yes"})
    admin_client.post(f"{USERS}{ana.pk}/delete/", {"post": "yes"})


def test_no_dob_or_password_in_any_audit_row_or_log_line(admin_client, capfd):
    _run_every_audited_action(admin_client)

    rows = list(AuditLogModel.objects.values())
    actions = {row["action"] for row in rows}
    stored = repr(rows)
    logs = capfd.readouterr().out
    assert {
        "accounts.created",
        "accounts.updated",
        "accounts.password_changed",
        "accounts.parent_linked",
        "accounts.parent_unlinked",
        "accounts.deleted",
    } <= actions
    for secret in (DOB, NEW_DOB, "2017", FIRST_PASSWORD, RESET_PASSWORD, "Ana Pop"):
        assert secret not in stored
        assert secret not in logs
    assert not [key for row in rows for key in row["metadata"] if is_sensitive_key(key)]
