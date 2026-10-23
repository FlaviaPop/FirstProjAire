"""Story 1.9 AC 10, 11: unlock = delete the axes attempt (audited); the audit log is read-only."""

import re

import pytest
from axes.models import AccessAttempt
from django.test import Client

from infrastructure.persistence.accounts.admin import platform_admin_site
from infrastructure.persistence.audit.fingerprint import username_fingerprint
from infrastructure.persistence.audit.models import AuditLogModel
from infrastructure.persistence.audit.repositories import DjangoAuditPort
from tests.factories.accounts import StudentFactory
from tests.fakes import FixedClock
from tests.integration.web.admin.admin_helpers import ATTEMPTS, AUDIT, admin_rows

pytestmark = pytest.mark.django_db
LOGIN = "/ro/accounts/login/"
PASSWORD = "pilot-pass-123"


def _lock_out(username):
    browser = Client()
    statuses = [
        browser.post(LOGIN, {"username": username, "password": "wrong-pass-1"}).status_code
        for _ in range(5)
    ]
    return browser, statuses


def _attempt(username):
    return AccessAttempt.objects.create(
        username=username,
        ip_address="10.0.0.9",
        user_agent="",
        http_accept="",
        path_info=LOGIN,
        get_data="",
        post_data="",
        failures_since_start=5,
    )


# --- AC 10: access attempts -------------------------------------------------------------------
def test_admin_clears_a_lockout_and_the_student_signs_in_at_once(admin_client, admin_user):
    ana = StudentFactory(username="ana")
    browser, statuses = _lock_out("ana")
    assert statuses[-1] == 429
    assert browser.post(LOGIN, {"username": "ana", "password": PASSWORD}).status_code == 429
    attempt = AccessAttempt.objects.get(username="ana")

    response = admin_client.post(f"{ATTEMPTS}{attempt.pk}/delete/", {"post": "yes"})

    assert response.status_code == 302
    assert not AccessAttempt.objects.exists()
    assert admin_rows("auth.lockout_cleared") == [
        {
            "action": "auth.lockout_cleared",
            "actor_id": admin_user.pk,
            "actor_username": "admin1",
            "target_id": str(ana.pk),
            "metadata": {},
        }
    ]
    assert browser.post(LOGIN, {"username": "ana", "password": PASSWORD}).status_code == 302


def test_unknown_username_is_audited_as_a_fingerprint_never_the_typed_text(admin_client):
    attempt = _attempt("Ana2018!secret")

    admin_client.post(f"{ATTEMPTS}{attempt.pk}/delete/", {"post": "yes"})

    row = AuditLogModel.objects.get(action="auth.lockout_cleared")
    assert (row.target_type, row.target_id) == (
        "user",
        f"(unknown):{username_fingerprint('Ana2018!secret')}",
    )
    assert re.fullmatch(r"\(unknown\):[0-9a-f]{8}", row.target_id)
    stored = [row.actor_username, row.target_id, str(row.metadata)]
    assert not any("Ana2018" in value for value in stored)


def test_empty_username_attempt_is_audited_as_empty(admin_client):
    attempt = _attempt("")

    admin_client.post(f"{ATTEMPTS}{attempt.pk}/delete/", {"post": "yes"})

    assert AuditLogModel.objects.get(action="auth.lockout_cleared").target_id == "(empty)"


def test_bulk_unlock_audits_every_attempt(admin_client):
    ana = StudentFactory(username="ana")
    attempts = [_attempt("ana"), _attempt("ghost")]

    response = admin_client.post(
        ATTEMPTS,
        {"action": "delete_selected", "_selected_action": [a.pk for a in attempts], "post": "yes"},
    )

    assert response.status_code == 302
    assert not AccessAttempt.objects.exists()
    targets = sorted(r["target_id"] for r in admin_rows("auth.lockout_cleared"))
    assert targets == sorted([str(ana.pk), f"(unknown):{username_fingerprint('ghost')}"])


def test_access_attempt_list_columns(admin_client):
    _attempt("ana")

    response = admin_client.get(ATTEMPTS)

    # "account" is the username column, masked for non-accounts (review v1 ISS-002).
    assert list(response.context["cl"].list_display) == [
        "action_checkbox",
        "account",
        "ip_address",
        "failures_since_start",
        "attempt_time",
    ]


def test_attempts_cannot_be_added_or_edited_and_form_data_is_never_shown(admin_client):
    attempt = _attempt("ana")
    AccessAttempt.objects.filter(pk=attempt.pk).update(post_data="password=********")

    detail = admin_client.get(f"{ATTEMPTS}{attempt.pk}/change/")

    assert admin_client.get(f"{ATTEMPTS}add/").status_code == 403
    assert admin_client.post(f"{ATTEMPTS}{attempt.pk}/change/", {}).status_code == 403
    assert detail.status_code == 200
    assert "password=" not in detail.content.decode()


# --- AC 11: read-only audit log ---------------------------------------------------------------
def _audit_row():
    DjangoAuditPort(FixedClock()).record("auth.login", actor_username="ana")
    return AuditLogModel.objects.get(action="auth.login", actor_username="ana")


def test_audit_log_is_read_only_in_admin(admin_client):
    row = _audit_row()

    listing = admin_client.get(AUDIT)

    assert listing.status_code == 200
    assert admin_client.get(f"{AUDIT}add/").status_code == 403
    assert admin_client.post(f"{AUDIT}add/", {"action": "forged"}).status_code == 403
    assert admin_client.post(f"{AUDIT}{row.pk}/change/", {"action": "x"}).status_code == 403
    assert admin_client.get(f"{AUDIT}{row.pk}/delete/").status_code == 403
    assert admin_client.post(f"{AUDIT}{row.pk}/delete/", {"post": "yes"}).status_code == 403
    assert AuditLogModel.objects.get(pk=row.pk).action == "auth.login"


def test_audit_log_has_no_add_change_or_delete_buttons(admin_client):
    row = _audit_row()

    listing = admin_client.get(AUDIT).content.decode()
    detail = admin_client.get(f"{AUDIT}{row.pk}/change/")

    assert f"{AUDIT}add/" not in listing
    assert "delete_selected" not in listing
    assert detail.status_code == 200
    assert 'name="_save"' not in detail.content.decode()
    assert "/delete/" not in detail.content.decode()


def test_bulk_delete_of_audit_rows_is_not_possible(admin_client):
    row = _audit_row()

    admin_client.post(
        AUDIT, {"action": "delete_selected", "_selected_action": [row.pk], "post": "yes"}
    )

    assert AuditLogModel.objects.filter(pk=row.pk).exists()


def test_audit_log_columns_filter_search_and_date_hierarchy(admin_client):
    _audit_row()

    changelist = admin_client.get(AUDIT).context["cl"]

    assert list(changelist.list_display) == [
        "created_at",
        "action",
        "actor_username",
        "target_type",
        "target_id",
        "ip_address",
    ]
    assert [f.title for f in changelist.filter_specs] == ["action"]
    assert changelist.search_fields == ("actor_username",)
    assert changelist.date_hierarchy == "created_at"


def test_audit_log_search_and_filter_work(admin_client):
    _audit_row()
    DjangoAuditPort(FixedClock()).record("auth.logout", actor_username="bob")

    by_name = admin_client.get(AUDIT, {"q": "bob"}).context["cl"].result_list
    by_action = admin_client.get(AUDIT, {"action": "auth.login"}).context["cl"].result_list

    assert [r.actor_username for r in by_name] == ["bob"]
    assert {r.action for r in by_action} == {"auth.login"}


def test_every_model_on_the_site_is_one_of_the_four_story_screens():
    labels = sorted(model._meta.label for model in platform_admin_site._registry)

    assert labels == [
        "accounts.ParentChildLinkModel",
        "accounts.UserModel",
        "audit.AuditLogModel",
        "axes.AccessAttempt",
    ]
