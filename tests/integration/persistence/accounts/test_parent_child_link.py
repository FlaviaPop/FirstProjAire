"""Story 1.9 AC 5: the database itself rejects duplicate and self links.

transaction=True: the constraints are checked by SQLite, not by a rolled-back test transaction.
No test here may write audit rows (append-only triggers would block the flush).
"""

import datetime

import pytest
from django.db import IntegrityError, transaction

from infrastructure.persistence.accounts.models import ParentChildLinkModel
from tests.factories.accounts import AdminFactory, ParentFactory, StudentFactory

pytestmark = pytest.mark.django_db(transaction=True)
AT = datetime.datetime(2026, 10, 20, 8, 0, tzinfo=datetime.UTC)


def test_database_rejects_duplicate_and_self_links():
    parent, student = ParentFactory(), StudentFactory()
    ParentChildLinkModel.objects.create(parent=parent, student=student, created_at=AT)

    with pytest.raises(IntegrityError), transaction.atomic():
        ParentChildLinkModel.objects.create(parent=parent, student=student, created_at=AT)
    with pytest.raises(IntegrityError), transaction.atomic():
        ParentChildLinkModel.objects.create(parent=parent, student=parent, created_at=AT)

    assert ParentChildLinkModel.objects.count() == 1


def test_table_and_constraint_names_match_the_architecture():
    meta = ParentChildLinkModel._meta

    assert meta.db_table == "accounts_parent_child_link"
    assert {c.name for c in meta.constraints} == {"uniq_parent_student", "parent_not_student"}


def test_deleting_either_party_cascades_its_links():
    parent, student, other = ParentFactory(), StudentFactory(), StudentFactory()
    ParentChildLinkModel.objects.create(parent=parent, student=student, created_at=AT)
    ParentChildLinkModel.objects.create(parent=parent, student=other, created_at=AT)

    student.delete()
    assert list(ParentChildLinkModel.objects.values_list("student_id", flat=True)) == [other.pk]

    parent.delete()
    assert ParentChildLinkModel.objects.count() == 0


def test_deleting_the_creating_admin_keeps_the_link():
    admin = AdminFactory()
    link = ParentChildLinkModel.objects.create(
        parent=ParentFactory(), student=StudentFactory(), created_by=admin, created_at=AT
    )

    admin.delete()

    link.refresh_from_db()
    assert link.created_by_id is None


def test_related_names_navigate_both_directions():
    parent, student = ParentFactory(), StudentFactory()
    ParentChildLinkModel.objects.create(parent=parent, student=student, created_at=AT)

    assert [link.student for link in parent.child_links.all()] == [student]
    assert [link.parent for link in student.parent_links.all()] == [parent]


def test_str_names_both_accounts_by_username():
    link = ParentChildLinkModel.objects.create(
        parent=ParentFactory(username="mama"), student=StudentFactory(username="ana"), created_at=AT
    )

    assert str(link) == "mama → ana"
