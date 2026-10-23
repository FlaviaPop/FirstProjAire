"""Story 2.2 AC 1-2: the catalogue query service (read side, ADR-005) over the Story 2.1 seed."""

import dataclasses

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from domain.common.errors import NotFound
from infrastructure.persistence.catalogue.models import GradeModel, SubjectModel
from infrastructure.persistence.catalogue.queries import (
    GradeDTO,
    SubjectDTO,
    active_subject,
    catalogue_overview,
)
from tests.factories.catalogue import GradeFactory, SubjectFactory

pytestmark = pytest.mark.django_db


# --- Story Tests block ----------------------------------------------------------------------------


def test_overview_uses_two_queries(django_assert_num_queries):
    with django_assert_num_queries(2):
        grades = catalogue_overview()

    assert [g.code for g in grades] == ["K", "P", "1", "2", "3", "4", "5", "6", "7", "8"]
    assert [g.code for g in grades if g.has_active] == ["2"]


def test_active_subject_carries_grade_names():
    subject = SubjectModel.objects.get(grade__code="2", code="EN")

    dto = active_subject(subject.pk)

    assert (dto.code, dto.grade_name_en) == ("EN", "Grade 2")


def test_inactive_subject_is_not_found():
    subject = SubjectModel.objects.filter(is_active=False).first()

    with pytest.raises(NotFound):
        active_subject(subject.pk)


# --- AC 1: shape and ordering ---------------------------------------------------------------------


def test_overview_returns_a_tuple_of_frozen_grade_dtos_with_subject_tuples():
    grades = catalogue_overview()

    assert isinstance(grades, tuple)
    assert all(isinstance(g, GradeDTO) and isinstance(g.subjects, tuple) for g in grades)
    assert all(isinstance(s, SubjectDTO) for g in grades for s in g.subjects)
    with pytest.raises(dataclasses.FrozenInstanceError):
        grades[0].code = "X"  # type: ignore[misc]


def test_overview_lists_every_seeded_subject_once():
    grades = catalogue_overview()

    ids = [s.id for g in grades for s in g.subjects]
    assert len(ids) == len(set(ids)) == SubjectModel.objects.count() == 111


def test_subjects_are_ordered_by_sort_order_within_each_grade():
    grade_2 = next(g for g in catalogue_overview() if g.code == "2")

    assert [s.code for s in grade_2.subjects] == [
        "CLR",
        "MEM",
        "EN",
        "DP",
        "MM",
        "AVAP",
        "EF",
        "REL",
    ]


def test_new_rows_follow_their_sort_order_not_their_insertion_order():
    grade_5 = GradeModel.objects.get(code="5")
    late = SubjectFactory(grade=grade_5, code="ZZZ", sort_order=0, name_ro="Ro", name_en="En")
    extra_grade = GradeFactory(code="9", name_ro="Clasa a IX-a", name_en="Grade 9")

    grades = catalogue_overview()

    assert grades[-1].code == extra_grade.code
    assert grades[-1].subjects == ()
    assert next(g for g in grades if g.code == "5").subjects[0].id == late.pk


def test_query_count_stays_two_when_subjects_are_added(django_assert_num_queries):
    for code in ("X1", "X2", "X3"):
        SubjectFactory(grade=GradeModel.objects.get(code="8"), code=code)

    with django_assert_num_queries(2):
        catalogue_overview()


def test_dto_names_are_bilingual_with_diacritics_intact():
    grades = catalogue_overview()
    mem = next(s for s in grades[3].subjects if s.code == "MEM")

    assert (grades[0].name_ro, grades[0].name_en) == ("Grădiniță", "Kindergarten")
    assert (mem.name_ro, mem.name_en) == (
        "Matematică și explorarea mediului",
        "Mathematics and Environmental Exploration",
    )


def test_has_active_is_false_for_a_grade_without_subjects():
    assert GradeDTO("X", "Ro", "En", ()).has_active is False


def test_only_grade_2_clr_mem_en_are_active():
    active = [(g.code, s.code) for g in catalogue_overview() for s in g.subjects if s.is_active]

    assert active == [("2", "CLR"), ("2", "MEM"), ("2", "EN")]


def test_overview_is_empty_when_the_catalogue_is_empty():
    SubjectModel.objects.all().delete()
    GradeModel.objects.all().delete()

    assert catalogue_overview() == ()


# --- AC 2: active_subject ------------------------------------------------------------------------


def test_active_subject_returns_both_languages_of_subject_and_grade():
    subject = SubjectModel.objects.get(grade__code="2", code="MEM")

    dto = active_subject(subject.pk)

    assert dto == SubjectDTO(
        id=subject.pk,
        code="MEM",
        name_ro="Matematică și explorarea mediului",
        name_en="Mathematics and Environmental Exploration",
        is_active=True,
        grade_name_ro="Clasa a II-a",
        grade_name_en="Grade 2",
    )


def test_active_subject_reads_with_one_query(django_assert_num_queries):
    subject = SubjectModel.objects.get(grade__code="2", code="CLR")

    with django_assert_num_queries(1):
        active_subject(subject.pk)


def test_unknown_subject_is_not_found():
    missing = SubjectModel.objects.order_by("-pk").first().pk + 1000

    with pytest.raises(NotFound):
        active_subject(missing)


def test_every_inactive_subject_is_not_found():
    inactive = SubjectModel.objects.filter(is_active=False).values_list("pk", flat=True)

    for subject_id in inactive:
        with pytest.raises(NotFound):
            active_subject(subject_id)


def test_inactive_and_unknown_raise_the_same_error():
    inactive = SubjectModel.objects.filter(is_active=False).first().pk

    with pytest.raises(NotFound) as for_inactive:
        active_subject(inactive)
    with pytest.raises(NotFound) as for_unknown:
        active_subject(999_999)

    assert str(for_inactive.value) == str(for_unknown.value) == "subject"
    assert for_inactive.value.code == for_unknown.value.code == "not_found"


def test_queries_only_read():
    subject_id = SubjectModel.objects.get(grade__code="2", code="EN").pk
    flags_before = list(SubjectModel.objects.values_list("pk", "is_active"))

    with CaptureQueriesContext(connection) as queries:
        catalogue_overview()
        active_subject(subject_id)

    assert all(q["sql"].lstrip().upper().startswith("SELECT") for q in queries)
    assert list(SubjectModel.objects.values_list("pk", "is_active")) == flags_before
