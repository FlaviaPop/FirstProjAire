"""Schema contract of GradeModel / SubjectModel and the integrity rules the DB enforces."""

import pytest
from django.db import IntegrityError, models, transaction
from django.db.models import ProtectedError

from infrastructure.persistence.catalogue.models import GradeModel, SubjectModel

pytestmark = pytest.mark.django_db


def test_duplicate_subject_code_in_grade_is_rejected():
    grade = GradeModel.objects.get(code="2")

    with pytest.raises(IntegrityError), transaction.atomic():
        SubjectModel.objects.create(
            grade=grade, code="MEM", sort_order=99, name_ro="x", name_en="x"
        )


def test_duplicate_sort_order_in_grade_is_rejected():
    grade = GradeModel.objects.get(code="2")

    with pytest.raises(IntegrityError), transaction.atomic():
        SubjectModel.objects.create(grade=grade, code="NEW", sort_order=1, name_ro="x", name_en="x")


def test_same_subject_code_is_allowed_in_another_grade():
    grade = GradeModel.objects.create(code="9", sort_order=10, name_ro="Clasa a IX-a", name_en="9")

    subject = SubjectModel.objects.create(
        grade=grade, code="MEM", sort_order=1, name_ro="x", name_en="x"
    )

    assert subject.pk is not None


def test_duplicate_grade_code_is_rejected():
    with pytest.raises(IntegrityError), transaction.atomic():
        GradeModel.objects.create(code="2", sort_order=42, name_ro="x", name_en="x")


def test_duplicate_grade_sort_order_is_rejected():
    with pytest.raises(IntegrityError), transaction.atomic():
        GradeModel.objects.create(code="Z", sort_order=2, name_ro="x", name_en="x")


def test_grade_with_subjects_cannot_be_deleted():
    with pytest.raises(ProtectedError):
        GradeModel.objects.get(code="2").delete()


def test_new_subject_is_inactive_by_default():
    grade = GradeModel.objects.get(code="2")

    subject = SubjectModel.objects.create(
        grade=grade, code="NEW", sort_order=50, name_ro="x", name_en="x"
    )

    assert subject.is_active is False


def _field(model: type[models.Model], name: str) -> models.Field:
    return model._meta.get_field(name)  # type: ignore[return-value]


def test_grade_model_schema_matches_the_story_contract():
    meta = GradeModel._meta

    assert meta.db_table == "catalogue_grade"
    assert meta.app_label == "catalogue"
    assert list(meta.ordering) == ["sort_order"]
    assert (_field(GradeModel, "code").max_length, _field(GradeModel, "code").unique) == (2, True)
    assert isinstance(_field(GradeModel, "sort_order"), models.PositiveSmallIntegerField)
    assert _field(GradeModel, "sort_order").unique is True
    assert (
        _field(GradeModel, "name_ro").max_length == _field(GradeModel, "name_en").max_length == 80
    )


def test_subject_model_schema_matches_the_story_contract():
    meta = SubjectModel._meta
    grade_fk = _field(SubjectModel, "grade")

    assert meta.db_table == "catalogue_subject"
    assert list(meta.ordering) == ["grade__sort_order", "sort_order"]
    assert grade_fk.related_model is GradeModel
    assert grade_fk.remote_field.on_delete is models.PROTECT
    assert grade_fk.remote_field.related_name == "subjects"
    assert _field(SubjectModel, "code").max_length == 8
    assert isinstance(_field(SubjectModel, "sort_order"), models.PositiveSmallIntegerField)
    assert _field(SubjectModel, "name_ro").max_length == 120
    assert _field(SubjectModel, "name_en").max_length == 120
    assert _field(SubjectModel, "is_active").default is False


def test_subject_unique_constraints_are_named_as_specified():
    constraints = {c.name: tuple(c.fields) for c in SubjectModel._meta.constraints}

    assert constraints == {
        "uniq_subject_code_per_grade": ("grade", "code"),
        "uniq_subject_order_per_grade": ("grade", "sort_order"),
    }
