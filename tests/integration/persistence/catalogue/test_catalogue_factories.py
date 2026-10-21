"""GradeFactory / SubjectFactory reuse seeded rows (get_or_create on codes) for later stories."""

import pytest

from infrastructure.persistence.catalogue.models import GradeModel, SubjectModel
from tests.factories.catalogue import GradeFactory, SubjectFactory

pytestmark = pytest.mark.django_db


def test_grade_factory_returns_the_seeded_grade_two():
    grade = GradeFactory()

    assert grade == GradeModel.objects.get(code="2")
    assert GradeModel.objects.count() == 9


def test_subject_factory_returns_the_seeded_active_mem_subject():
    subject = SubjectFactory()

    assert subject == SubjectModel.objects.get(grade__code="2", code="MEM")
    assert subject.is_active is True
    assert SubjectModel.objects.count() == 106


def test_factories_create_new_rows_for_unseeded_codes():
    grade = GradeFactory(code="9", sort_order=9, name_ro="Clasa a IX-a", name_en="Grade 9")

    subject = SubjectFactory(grade=grade, code="PHY", sort_order=1)

    assert (subject.grade.code, subject.code) == ("9", "PHY")
    assert SubjectModel.objects.count() == 107
