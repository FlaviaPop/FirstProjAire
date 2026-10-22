"""Story 1.9 AC 4, 9 + owner decision 4: password resets and account deletion, audited."""

import pytest

from infrastructure.persistence.accounts.admin import delete_selected
from infrastructure.persistence.accounts.models import UserModel
from infrastructure.persistence.audit.models import AuditLogModel
from tests.factories.accounts import (
    AdminFactory,
    ParentChildLinkFactory,
    ParentFactory,
    StudentFactory,
)
from tests.integration.web.admin.admin_helpers import STRONG_PASSWORD, USERS, admin_rows

pytestmark = pytest.mark.django_db
LAST_ADMIN = "There must be at least one active administrator."


# --- Password reset ---------------------------------------------------------------------------
def test_password_reset_is_validated_and_audited_without_the_value(admin_client, student):
    url = f"{USERS}{student.pk}/password/"
    weak = admin_client.post(url, {"password1": "12345678", "password2": "12345678"})
    assert weak.status_code == 200
    assert admin_rows() == []

    response = admin_client.post(
        url, {"password1": STRONG_PASSWORD, "password2": STRONG_PASSWORD, "usable_password": "true"}
    )

    student.refresh_from_db()
    assert response.status_code == 302
    assert student.check_password(STRONG_PASSWORD)
    assert [(r["action"], r["target_id"], r["metadata"]) for r in admin_rows()] == [
        ("accounts.password_changed", str(student.pk), {"fields": []})
    ]


def test_admin_changing_their_own_password_is_audited(admin_client, admin_user):
    response = admin_client.post(
        "/en/admin/password_change/",
        {
            "old_password": "pilot-pass-123",
            "new_password1": STRONG_PASSWORD,
            "new_password2": STRONG_PASSWORD,
        },
    )

    assert response.status_code == 302
    assert [(r["action"], r["target_id"]) for r in admin_rows()] == [
        ("accounts.password_changed", str(admin_user.pk))
    ]


def test_failed_own_password_change_writes_nothing(admin_client):
    admin_client.post("/en/admin/password_change/", {"old_password": "wrong"})

    assert admin_rows() == []


# --- Delete -----------------------------------------------------------------------------------
def test_deleting_user_cascades_links_but_keeps_audit(
    admin_client, admin_user, linked_parent, student
):
    from django.contrib.auth.signals import user_logged_in
    from django.test import RequestFactory

    user_logged_in.send(sender=UserModel, request=RequestFactory().get("/"), user=student)

    response = admin_client.post(f"{USERS}{student.pk}/delete/", {"post": "yes"})

    assert response.status_code == 302
    assert not UserModel.objects.filter(pk=student.pk).exists()
    assert linked_parent.child_links.count() == 0
    earlier = AuditLogModel.objects.get(action="auth.login", actor_username="student1")
    assert earlier.actor_id is None
    assert [(r["action"], r["target_id"], r["metadata"]) for r in admin_rows()] == [
        ("accounts.deleted", str(student.pk), {"fields": []})
    ]


def test_bulk_delete_audits_every_account(admin_client):
    first, second = StudentFactory(), StudentFactory()

    response = admin_client.post(
        USERS,
        {"action": "delete_selected", "_selected_action": [first.pk, second.pk], "post": "yes"},
    )

    assert response.status_code == 302
    assert not UserModel.objects.filter(pk__in=[first.pk, second.pk]).exists()
    assert sorted(r["target_id"] for r in admin_rows("accounts.deleted")) == sorted(
        [str(first.pk), str(second.pk)]
    )


def test_last_active_admin_has_no_delete_button(admin_client, admin_user):
    response = admin_client.get(f"{USERS}{admin_user.pk}/change/")

    assert f"{admin_user.pk}/delete/" not in response.content.decode()


def test_deleting_yourself_as_last_active_admin_is_forbidden(admin_client, admin_user):
    response = admin_client.post(f"{USERS}{admin_user.pk}/delete/", {"post": "yes"})

    assert response.status_code == 403
    assert UserModel.objects.filter(pk=admin_user.pk).exists()
    assert admin_rows() == []


def test_bulk_delete_that_would_remove_every_active_admin_is_refused(admin_client, admin_user):
    other = AdminFactory(username="other-admin")
    student = StudentFactory()
    selected = [admin_user.pk, other.pk, student.pk]

    response = admin_client.post(
        USERS,
        {"action": "delete_selected", "_selected_action": selected, "post": "yes"},
        follow=True,
    )

    assert response.status_code == 200
    assert LAST_ADMIN in [str(m) for m in response.context["messages"]]
    assert UserModel.objects.filter(pk__in=selected).count() == 3
    assert admin_rows() == []


def test_bulk_delete_keeping_one_active_admin_is_allowed(admin_client, admin_user):
    other = AdminFactory(username="other-admin")

    response = admin_client.post(
        USERS, {"action": "delete_selected", "_selected_action": [other.pk], "post": "yes"}
    )

    assert response.status_code == 302
    assert not UserModel.objects.filter(pk=other.pk).exists()


def test_another_admin_can_be_deleted_while_you_remain(admin_client):
    other = AdminFactory(username="other-admin")

    response = admin_client.post(f"{USERS}{other.pk}/delete/", {"post": "yes"})

    assert response.status_code == 302
    assert admin_rows("accounts.deleted")[0]["target_id"] == str(other.pk)


def test_account_bulk_delete_is_the_guarded_action(admin_client):
    response = admin_client.get(USERS)

    func, name, _ = response.context["cl"].model_admin.get_actions(response.wsgi_request)[
        "delete_selected"
    ]
    assert (func, name) == (delete_selected, "delete_selected")
    assert list(func.allowed_permissions) == ["delete"]


def test_bulk_delete_confirmation_page_is_shown_first(admin_client):
    student = StudentFactory()

    response = admin_client.post(
        USERS, {"action": "delete_selected", "_selected_action": [student.pk]}
    )

    assert response.status_code == 200
    assert UserModel.objects.filter(pk=student.pk).exists()


def test_parent_with_links_is_deleted_with_its_links(admin_client):
    link = ParentChildLinkFactory(parent=ParentFactory(), student=StudentFactory())

    admin_client.post(f"{USERS}{link.parent_id}/delete/", {"post": "yes"})

    assert not type(link).objects.exists()
