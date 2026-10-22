"""Story 1.9 AC 8: parent-child links are created/deleted through LinkParent/UnlinkParent."""

import pytest
from django.urls import path
from django.utils import translation

from application.accounts.link_parent import LinkExists
from domain.common.errors import Violation
from infrastructure.persistence.accounts.models import ParentChildLinkModel
from infrastructure.persistence.accounts.repositories import DjangoParentLinks
from infrastructure.web.common.errors import ERROR_MESSAGES, violation_message
from tests.factories.accounts import (
    AdminFactory,
    ParentChildLinkFactory,
    ParentFactory,
    StudentFactory,
    TeacherFactory,
)
from tests.integration.web.admin.admin_helpers import LINKS, admin_rows

pytestmark = pytest.mark.django_db
ADD = f"{LINKS}add/"
DUPLICATE = "This parent is already linked to this student."
NOT_PARENT = "The selected parent account isn&#x27;t a Parent/Guardian."
NOT_STUDENT = "The selected child account isn&#x27;t a Student."


def test_admin_links_parent_and_duplicate_is_refused(admin_client, admin_user):
    parent, student = ParentFactory(), StudentFactory()

    first = admin_client.post(ADD, {"parent": parent.pk, "student": student.pk})
    second = admin_client.post(ADD, {"parent": parent.pk, "student": student.pk})

    assert first.status_code == 302
    assert second.status_code == 200
    assert second.content.decode().count(DUPLICATE) == 1  # the rule's text, shown once
    assert "already exists" not in second.content.decode()
    assert ParentChildLinkModel.objects.count() == 1
    link = ParentChildLinkModel.objects.get()
    assert admin_rows() == [
        {
            "action": "accounts.parent_linked",
            "actor_id": admin_user.pk,
            "actor_username": "admin1",
            "target_id": str(link.pk),
            "metadata": {"parent_id": parent.pk, "student_id": student.pk},
        }
    ]


def test_link_is_created_by_the_session_admin_whatever_the_post_says(admin_client, admin_user):
    parent, student, someone_else = ParentFactory(), StudentFactory(), AdminFactory()

    admin_client.post(
        ADD,
        {
            "parent": parent.pk,
            "student": student.pk,
            "created_by": someone_else.pk,
            "actor_id": someone_else.pk,
            "created_at": "2001-01-01T00:00",
        },
    )

    link = ParentChildLinkModel.objects.get()
    assert link.created_by_id == admin_user.pk
    assert link.created_at.year == 2026
    assert admin_rows()[0]["actor_id"] == admin_user.pk


def test_add_form_offers_only_active_parents_and_students(admin_client):
    parent, student = ParentFactory(), StudentFactory()
    ParentFactory(is_active=False)
    TeacherFactory()

    form = admin_client.get(ADD).context["adminform"].form

    assert list(form.fields) == ["parent", "student"]
    assert list(form.fields["parent"].queryset) == [parent]
    assert list(form.fields["student"].queryset) == [student]


@pytest.mark.parametrize(
    ("parent_factory", "student_factory", "message"),
    [
        (TeacherFactory, StudentFactory, NOT_PARENT),
        (AdminFactory, StudentFactory, NOT_PARENT),
        (ParentFactory, ParentFactory, NOT_STUDENT),
        (ParentFactory, TeacherFactory, NOT_STUDENT),
    ],
)
def test_wrong_roles_are_refused_with_a_form_error_naming_the_rule(
    admin_client, parent_factory, student_factory, message
):
    response = admin_client.post(
        ADD, {"parent": parent_factory().pk, "student": student_factory().pk}
    )

    assert response.status_code == 200
    assert message in response.content.decode()
    assert ParentChildLinkModel.objects.count() == 0
    assert admin_rows() == []


def test_same_account_on_both_sides_is_refused(admin_client):
    parent = ParentFactory()

    response = admin_client.post(ADD, {"parent": parent.pk, "student": parent.pk})

    assert response.status_code == 200
    assert NOT_STUDENT in response.content.decode()
    assert ParentChildLinkModel.objects.count() == 0


def test_inactive_parent_cannot_be_linked(admin_client):
    response = admin_client.post(
        ADD, {"parent": ParentFactory(is_active=False).pk, "student": StudentFactory().pk}
    )

    assert response.status_code == 200
    assert ParentChildLinkModel.objects.count() == 0


def test_concurrent_duplicate_shows_the_form_error_and_keeps_one_row(admin_client, monkeypatch):
    parent, student = ParentFactory(), StudentFactory()
    ParentChildLinkFactory(parent=parent, student=student)  # the other request won the race
    monkeypatch.setattr(DjangoParentLinks, "exists", lambda self, p, s: False)  # not yet visible

    response = admin_client.post(ADD, {"parent": parent.pk, "student": student.pk})

    assert response.status_code == 200
    assert DUPLICATE in response.content.decode()
    assert ParentChildLinkModel.objects.count() == 1
    assert admin_rows() == []


def test_parent_can_have_several_children_and_child_several_parents(admin_client):
    mother, father = ParentFactory(), ParentFactory()
    ana, ion = StudentFactory(), StudentFactory()

    for parent, child in [(mother, ana), (mother, ion), (father, ana)]:
        assert admin_client.post(ADD, {"parent": parent.pk, "student": child.pk}).status_code == 302

    assert ParentChildLinkModel.objects.count() == 3
    assert len(admin_rows("accounts.parent_linked")) == 3


def test_deleting_a_link_unlinks_once_and_repeat_is_a_no_op(admin_client, admin_user):
    link = ParentChildLinkFactory()
    url = f"{LINKS}{link.pk}/delete/"

    first = admin_client.post(url, {"post": "yes"})
    second = admin_client.post(url, {"post": "yes"})

    assert (first.status_code, second.status_code) == (302, 302)
    assert ParentChildLinkModel.objects.count() == 0
    assert admin_rows() == [
        {
            "action": "accounts.parent_unlinked",
            "actor_id": admin_user.pk,
            "actor_username": "admin1",
            "target_id": str(link.pk),
            "metadata": {"parent_id": link.parent_id, "student_id": link.student_id},
        }
    ]


def test_bulk_unlink_audits_every_link(admin_client):
    links = [ParentChildLinkFactory(), ParentChildLinkFactory()]

    response = admin_client.post(
        LINKS,
        {"action": "delete_selected", "_selected_action": [x.pk for x in links], "post": "yes"},
    )

    assert response.status_code == 302
    assert ParentChildLinkModel.objects.count() == 0
    assert len(admin_rows("accounts.parent_unlinked")) == 2


def test_links_are_never_edited(admin_client):
    link = ParentChildLinkFactory()
    other_student = StudentFactory()

    view = admin_client.get(f"{LINKS}{link.pk}/change/")
    edit = admin_client.post(
        f"{LINKS}{link.pk}/change/", {"parent": link.parent_id, "student": other_student.pk}
    )

    link.refresh_from_db()
    assert view.status_code == 200
    assert 'name="_save"' not in view.content.decode()
    assert edit.status_code == 403
    assert link.student_id != other_student.pk


def test_changelist_shows_links(admin_client):
    link = ParentChildLinkFactory()

    response = admin_client.get(LINKS)

    assert list(response.context["cl"].result_list) == [link]


# --- Link codes reach the shared error renderer too (DomainErrorMiddleware) ---------------------
LINK_CODES = {
    "link_exists": "This parent is already linked to this student.",
    "parent_not_parent_role": "The selected parent account isn't a Parent/Guardian.",
    "student_not_student_role": "The selected child account isn't a Student.",
    "self_link": "A person can't be linked to themselves.",
}


@pytest.mark.parametrize(("code", "message"), LINK_CODES.items())
def test_link_codes_are_registered_error_messages(code, message):
    with translation.override("en"):
        assert violation_message(Violation(code)) == message
        assert str(ERROR_MESSAGES[code]) == message


def _conflict(request):
    raise LinkExists()


urlpatterns = [path("conflict", _conflict, name="conflict")]


@pytest.mark.urls(__name__)
def test_link_conflict_escaping_to_the_middleware_is_a_409_with_the_message(client):
    response = client.get("/conflict", HTTP_ACCEPT_LANGUAGE="en")

    assert response.status_code == 409
    assert DUPLICATE in response.content.decode()
