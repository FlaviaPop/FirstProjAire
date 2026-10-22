"""Story 1.9 Step 4: DjangoParentLinks implements ParentLinkPort on the ORM."""

import datetime

import pytest
from django.db import transaction

from application.accounts.link_parent import LinkExists
from infrastructure.persistence.accounts.models import ParentChildLinkModel
from infrastructure.persistence.accounts.repositories import DjangoParentLinks
from tests.factories.accounts import AdminFactory, ParentFactory, StudentFactory, TeacherFactory

pytestmark = pytest.mark.django_db
AT = datetime.datetime(2026, 10, 20, 8, 0, tzinfo=datetime.UTC)


@pytest.mark.parametrize(
    ("factory", "role"),
    [(StudentFactory, "STUDENT"), (ParentFactory, "PARENT"), (TeacherFactory, "TEACHER")],
)
def test_role_of_reads_the_stored_role(factory, role):
    assert DjangoParentLinks().role_of(factory().pk) == role


def test_role_of_an_unknown_account_is_none():
    assert DjangoParentLinks().role_of(987654) is None


def test_add_stores_the_link_with_creator_and_time_and_returns_its_id():
    parent, student, admin = ParentFactory(), StudentFactory(), AdminFactory()
    links = DjangoParentLinks()

    link_id = links.add(parent.pk, student.pk, admin.pk, AT)

    link = ParentChildLinkModel.objects.get(pk=link_id)
    assert (link.parent_id, link.student_id, link.created_by_id) == (
        parent.pk,
        student.pk,
        admin.pk,
    )
    assert link.created_at == AT
    assert links.exists(parent.pk, student.pk) is True
    assert links.exists(student.pk, parent.pk) is False


def test_duplicate_insert_is_mapped_to_link_exists():
    parent, student, admin = ParentFactory(), StudentFactory(), AdminFactory()
    links = DjangoParentLinks()
    links.add(parent.pk, student.pk, admin.pk, AT)

    with pytest.raises(LinkExists) as error, transaction.atomic():
        links.add(parent.pk, student.pk, admin.pk, AT)

    assert error.value.__cause__.__class__.__name__ == "IntegrityError"
    assert ParentChildLinkModel.objects.count() == 1


def test_remove_returns_the_pair_once_then_none():
    parent, student, admin = ParentFactory(), StudentFactory(), AdminFactory()
    links = DjangoParentLinks()
    link_id = links.add(parent.pk, student.pk, admin.pk, AT)

    assert links.remove(link_id) == (parent.pk, student.pk)
    assert links.remove(link_id) is None
    assert ParentChildLinkModel.objects.count() == 0


# --- Story 1.9 AC 12, 13: composition root and shared fixtures ---------------------------------
def test_container_wires_the_account_use_cases_to_django_adapters():
    from application.accounts.link_parent import LinkParent, UnlinkParent
    from application.accounts.manage_account import AuditAccountChange
    from infrastructure import container
    from infrastructure.persistence.audit.repositories import DjangoAuditPort
    from infrastructure.persistence.common.unit_of_work import DjangoUnitOfWork
    from infrastructure.system_clock import SystemClock

    link, unlink, audit = (
        container.link_parent(),
        container.unlink_parent(),
        container.audit_account_change(),
    )

    assert isinstance(link, LinkParent)
    assert isinstance(unlink, UnlinkParent)
    assert isinstance(audit, AuditAccountChange)
    for use_case in (link, unlink, audit):
        assert isinstance(use_case._audit, DjangoAuditPort)
        assert isinstance(use_case._uow, DjangoUnitOfWork)
    assert isinstance(link._links, DjangoParentLinks)
    assert isinstance(unlink._links, DjangoParentLinks)
    assert isinstance(link._clock, SystemClock)


def test_linked_parent_fixture_links_the_parent_to_student(linked_parent, student, parent):
    assert linked_parent == parent
    assert [link.student for link in linked_parent.child_links.all()] == [student]


def test_unlinked_parent_fixture_is_a_parent_without_children(unlinked_parent, linked_parent):
    assert (unlinked_parent.role, unlinked_parent.username) == ("PARENT", "parent2")
    assert unlinked_parent.child_links.count() == 0


def test_link_factory_builds_a_parent_and_a_student():
    from tests.factories.accounts import ParentChildLinkFactory

    link = ParentChildLinkFactory()

    assert (link.parent.role, link.student.role) == ("PARENT", "STUDENT")
