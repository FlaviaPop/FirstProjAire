"""Catalogue read side (CQRS-lite, ADR-005): grades and subjects as frozen DTOs for the web pages.

DTOs carry the paired `name_ro`/`name_en` fields so templates read them with `{% localized %}`.
"""

from dataclasses import dataclass

from django.db.models import Prefetch

from domain.common.errors import NotFound
from infrastructure.persistence.catalogue.models import GradeModel, SubjectModel


@dataclass(frozen=True)
class SubjectDTO:
    id: int
    code: str
    name_ro: str
    name_en: str
    is_active: bool
    grade_name_ro: str = ""
    grade_name_en: str = ""


@dataclass(frozen=True)
class GradeDTO:
    code: str
    name_ro: str
    name_en: str
    subjects: tuple[SubjectDTO, ...]

    @property
    def has_active(self) -> bool:
        """True when at least one subject of this grade is usable (shown as the pilot grade)."""
        return any(subject.is_active for subject in self.subjects)


def catalogue_overview() -> tuple[GradeDTO, ...]:
    """Every grade by `sort_order`, each with its subjects by `sort_order`: exactly 2 queries."""
    grades = GradeModel.objects.order_by("sort_order").prefetch_related(
        Prefetch("subjects", queryset=SubjectModel.objects.order_by("sort_order"))
    )
    return tuple(
        GradeDTO(
            grade.code,
            grade.name_ro,
            grade.name_en,
            tuple(
                SubjectDTO(s.pk, s.code, s.name_ro, s.name_en, s.is_active)
                for s in grade.subjects.all()
            ),
        )
        for grade in grades
    )


def active_subject(subject_id: int) -> SubjectDTO:
    """The active subject `subject_id` with its grade names (one query).

    Raises:
        NotFound: when the id doesn't exist or the subject is inactive. Both cases raise the
            same error, so the 404 never reveals that an inactive subject exists.
    """
    # Scope inside the query (patterns §6.3): an inactive subject is never loaded at all.
    subject = (
        SubjectModel.objects.select_related("grade").filter(pk=subject_id, is_active=True).first()
    )
    if subject is None:
        raise NotFound("subject")
    return SubjectDTO(
        subject.pk,
        subject.code,
        subject.name_ro,
        subject.name_en,
        True,
        subject.grade.name_ro,
        subject.grade.name_en,
    )
