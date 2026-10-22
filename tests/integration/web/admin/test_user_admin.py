"""Story 1.9 AC 3, 4, 9: account create/edit/password/delete in the admin, guarded and audited."""

import pytest

from infrastructure.persistence.accounts.models import UserModel
from infrastructure.persistence.audit.models import AuditLogModel
from tests.factories.accounts import (
    AdminFactory,
    StudentFactory,
    TeacherFactory,
)
from tests.integration.web.admin.admin_helpers import (
    STRONG_PASSWORD,
    USERS,
    admin_rows,
    change_data,
)

pytestmark = pytest.mark.django_db
LAST_ADMIN = "There must be at least one active administrator."
STUDENT_LINKS = "Remove this student&#x27;s parent links before changing the role."
PARENT_LINKS = "Remove this parent&#x27;s child links before changing the role."
NEW_STUDENT = {
    "username": "ana",
    "full_name": "Ana Pop",
    "date_of_birth": "2018-03-02",
    "role": "STUDENT",
    "preferred_language": "ro",
    "password1": STRONG_PASSWORD,
    "password2": STRONG_PASSWORD,
}


def _form(response):
    return response.context["adminform"].form


# --- AC 3: forms ------------------------------------------------------------------------------
def test_add_form_has_exactly_the_platform_fields(admin_client):
    form = _form(admin_client.get(f"{USERS}add/"))

    assert list(form.fields) == [
        "username",
        "full_name",
        "date_of_birth",
        "role",
        "preferred_language",
        "password1",
        "password2",
    ]


def test_change_form_adds_active_flag_password_link_and_read_only_dates(admin_client, student):
    response = admin_client.get(f"{USERS}{student.pk}/change/")
    form = _form(response)

    assert set(form.fields) == {
        "username",
        "password",
        "full_name",
        "date_of_birth",
        "role",
        "preferred_language",
        "is_active",
    }
    assert set(response.context["adminform"].readonly_fields) == {"last_login", "date_joined"}
    assert "../password/" in response.content.decode()


@pytest.mark.parametrize("url_suffix", ["add/", "{pk}/change/"])
def test_staff_flags_groups_and_permissions_are_never_editable(admin_client, student, url_suffix):
    response = admin_client.get(USERS + url_suffix.format(pk=student.pk))

    shown = set(_form(response).fields)
    assert not shown & {"groups", "user_permissions", "is_staff", "is_superuser"}
    assert 'name="is_staff"' not in response.content.decode()


def test_changelist_columns_filters_and_search(admin_client):
    response = admin_client.get(USERS)
    changelist = response.context["cl"]

    assert list(changelist.list_display) == [
        "action_checkbox",
        "username",
        "full_name",
        "role",
        "preferred_language",
        "is_active",
        "last_login",
    ]
    assert [f.title for f in changelist.filter_specs] == [
        "role",
        "active",
        "preferred language",
    ]
    assert changelist.search_fields == ("username", "full_name")


def test_search_finds_by_full_name(admin_client):
    StudentFactory(username="ana", full_name="Ana Popescu")
    StudentFactory(username="bob", full_name="Bob Ionescu")

    response = admin_client.get(USERS, {"q": "Popescu"})

    assert [u.username for u in response.context["cl"].result_list] == ["ana"]


# --- Create -----------------------------------------------------------------------------------
def test_admin_creates_a_student_and_the_audit_has_field_names_only(admin_client, admin_user):
    response = admin_client.post(f"{USERS}add/", NEW_STUDENT, follow=True)

    ana = UserModel.objects.get(username="ana")
    assert response.redirect_chain[0][1] == 302
    assert next(str(m) for m in response.context["messages"]).startswith("The account")
    assert (ana.full_name, str(ana.date_of_birth), ana.role) == ("Ana Pop", "2018-03-02", "STUDENT")
    assert ana.check_password(STRONG_PASSWORD)
    assert (ana.is_staff, ana.is_superuser) == (False, False)
    assert admin_rows() == [
        {
            "action": "accounts.created",
            "actor_id": admin_user.pk,
            "actor_username": "admin1",
            "target_id": str(ana.pk),
            # form.changed_data: preferred_language stayed at its default ("ro").
            "metadata": {"fields": ["date_of_birth", "full_name", "role", "username"]},
        }
    ]
    assert "2018-03-02" not in str(admin_rows())
    assert STRONG_PASSWORD not in str(admin_rows())


@pytest.mark.parametrize(
    ("password", "reason"),
    [
        ("12345678", "This password is too common."),
        ("short1", "This password is too short."),
        ("48151623", "This password is entirely numeric."),
    ],
)
def test_weak_password_is_refused_with_the_reason(admin_client, password, reason):
    data = {**NEW_STUDENT, "password1": password, "password2": password}

    response = admin_client.post(f"{USERS}add/", data)

    assert response.status_code == 200
    assert reason in response.content.decode()
    assert not UserModel.objects.filter(username="ana").exists()
    assert admin_rows() == []


def test_mismatched_passwords_are_refused(admin_client):
    response = admin_client.post(f"{USERS}add/", {**NEW_STUDENT, "password2": "Other-pass-2026"})

    assert response.status_code == 200
    assert not UserModel.objects.filter(username="ana").exists()


def test_forged_staff_fields_in_the_post_are_ignored(admin_client):
    forged = {**NEW_STUDENT, "role": "TEACHER", "is_staff": "on", "is_superuser": "on"}

    admin_client.post(f"{USERS}add/", forged)

    created = UserModel.objects.get(username="ana")
    assert (created.role, created.is_staff, created.is_superuser) == ("TEACHER", False, False)


def test_non_default_language_is_listed_among_created_fields(admin_client):
    admin_client.post(f"{USERS}add/", {**NEW_STUDENT, "preferred_language": "en"})

    assert "preferred_language" in admin_rows()[0]["metadata"]["fields"]


def test_admin_can_create_another_admin_who_gets_access(admin_client):
    admin_client.post(f"{USERS}add/", {**NEW_STUDENT, "username": "boss", "role": "ADMIN"})

    boss = UserModel.objects.get(username="boss")
    assert (boss.is_staff, boss.is_superuser) == (True, True)


# --- Edit ---------------------------------------------------------------------------------------
def test_account_change_audit_has_field_names_only(admin_client):
    student = StudentFactory(full_name="Ana Pop")

    response = admin_client.post(
        f"{USERS}{student.pk}/change/",
        change_data(student, full_name="Ana Popescu", date_of_birth="2018-03-03"),
    )

    assert response.status_code == 302
    entry = AuditLogModel.objects.get(action="accounts.updated")
    assert entry.metadata == {"fields": ["date_of_birth", "full_name"]}
    assert "2018-03-03" not in str(entry.metadata)
    assert "Popescu" not in str(entry.metadata)


def test_save_without_changes_still_writes_exactly_one_row(admin_client, student):
    admin_client.post(f"{USERS}{student.pk}/change/", change_data(student))

    assert [(r["action"], r["metadata"]) for r in admin_rows()] == [
        ("accounts.updated", {"fields": []})
    ]


def test_setting_admin_role_on_a_teacher_grants_access_and_writes_two_rows(
    admin_client, admin_user
):
    teacher = TeacherFactory(username="t2")

    response = admin_client.post(f"{USERS}{teacher.pk}/change/", change_data(teacher, role="ADMIN"))

    teacher.refresh_from_db()
    assert response.status_code == 302
    assert (teacher.is_staff, teacher.is_superuser) == (True, True)
    assert [(r["action"], r["target_id"], r["metadata"]) for r in admin_rows()] == [
        ("accounts.updated", str(teacher.pk), {"fields": ["role"]}),
        ("accounts.role_changed", str(teacher.pk), {"fields": ["role"]}),
    ]


def test_role_change_with_other_fields_lists_every_changed_field(admin_client):
    teacher = TeacherFactory(username="t2")

    admin_client.post(
        f"{USERS}{teacher.pk}/change/", change_data(teacher, role="PARENT", full_name="New")
    )

    assert [r["metadata"] for r in admin_rows()] == [
        {"fields": ["full_name", "role"]},
        {"fields": ["role"]},
    ]


def test_deactivating_an_account_is_audited(admin_client, student):
    admin_client.post(f"{USERS}{student.pk}/change/", change_data(student, is_active=""))

    student.refresh_from_db()
    assert student.is_active is False
    assert admin_rows()[0]["metadata"] == {"fields": ["is_active"]}


# --- AC 4: guards -----------------------------------------------------------------------------
@pytest.mark.parametrize("change", [{"role": "TEACHER"}, {"is_active": ""}])
def test_last_active_admin_cannot_be_demoted_or_deactivated(admin_client, admin_user, change):
    response = admin_client.post(
        f"{USERS}{admin_user.pk}/change/", change_data(admin_user, **change)
    )

    admin_user.refresh_from_db()
    assert response.status_code == 200
    assert LAST_ADMIN in response.content.decode()
    assert (admin_user.role, admin_user.is_active, admin_user.is_staff) == ("ADMIN", True, True)
    assert admin_rows() == []


def test_an_inactive_second_admin_does_not_count(admin_client, admin_user):
    AdminFactory(username="dormant", is_active=False)

    response = admin_client.post(
        f"{USERS}{admin_user.pk}/change/", change_data(admin_user, role="TEACHER")
    )

    assert LAST_ADMIN in response.content.decode()


def test_an_admin_can_be_demoted_while_another_active_admin_exists(admin_client):
    other = AdminFactory(username="other-admin")

    response = admin_client.post(f"{USERS}{other.pk}/change/", change_data(other, role="TEACHER"))

    other.refresh_from_db()
    assert response.status_code == 302
    assert (other.role, other.is_staff) == ("TEACHER", False)


def test_linked_student_role_change_is_refused(admin_client, linked_parent, student):
    response = admin_client.post(
        f"{USERS}{student.pk}/change/", change_data(student, role="TEACHER")
    )

    student.refresh_from_db()
    assert response.status_code == 200
    assert STUDENT_LINKS in response.content.decode()
    assert student.role == "STUDENT"


def test_linked_parent_role_change_is_refused_with_its_own_message(
    admin_client, linked_parent, student
):
    response = admin_client.post(
        f"{USERS}{linked_parent.pk}/change/", change_data(linked_parent, role="STUDENT")
    )

    linked_parent.refresh_from_db()
    assert response.status_code == 200
    assert PARENT_LINKS in response.content.decode()
    assert STUDENT_LINKS not in response.content.decode()
    assert linked_parent.role == "PARENT"


def test_linked_student_can_still_be_edited_without_a_role_change(
    admin_client, linked_parent, student
):
    response = admin_client.post(
        f"{USERS}{student.pk}/change/", change_data(student, full_name="Ana Maria")
    )

    assert response.status_code == 302


def test_unlinked_student_role_can_change(admin_client, student):
    response = admin_client.post(
        f"{USERS}{student.pk}/change/", change_data(student, role="PARENT")
    )

    student.refresh_from_db()
    assert response.status_code == 302
    assert student.role == "PARENT"
