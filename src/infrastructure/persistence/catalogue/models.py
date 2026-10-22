"""Grade and subject reference data (K-8). Seeded by migration 0002; there is no admin editing.

The catalogue holds no business rules, so it has no domain package. Read access goes through
the catalogue query service (Story 2.2). Names are paired `_ro`/`_en` columns (ADR-006).
"""

from typing import ClassVar

from django.db import models


class GradeModel(models.Model):
    code = models.CharField(max_length=2, unique=True)
    sort_order = models.PositiveSmallIntegerField(unique=True)
    name_ro = models.CharField(max_length=80)
    name_en = models.CharField(max_length=80)

    class Meta:
        db_table = "catalogue_grade"
        ordering: ClassVar[list[str]] = ["sort_order"]
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(
                condition=~models.Q(name_ro="") & ~models.Q(name_en=""),
                name="grade_names_not_empty",
            ),
        ]

    def __str__(self) -> str:
        return self.code


class SubjectModel(models.Model):
    # PROTECT: a grade can't disappear while subjects (and, from CYCLE-2, content) depend on it.
    grade = models.ForeignKey(GradeModel, on_delete=models.PROTECT, related_name="subjects")
    code = models.CharField(max_length=8)
    # Not in the architecture ER: a stable, curriculum-conventional display order (story 2.1).
    sort_order = models.PositiveSmallIntegerField()
    name_ro = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120)
    # Requirements: only grade 2 CLR, MEM and EN are active in the MVP.
    is_active = models.BooleanField(default=False)

    class Meta:
        db_table = "catalogue_subject"
        ordering: ClassVar[list[str]] = ["grade__sort_order", "sort_order"]
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(fields=["grade", "code"], name="uniq_subject_code_per_grade"),
            models.UniqueConstraint(
                fields=["grade", "sort_order"], name="uniq_subject_order_per_grade"
            ),
            # Both languages always present (ADR-006); also guards later data migrations.
            models.CheckConstraint(
                condition=~models.Q(name_ro="") & ~models.Q(name_en=""),
                name="subject_names_not_empty",
            ),
        ]

    def __str__(self) -> str:
        # Grade *code* ("2:EN"), not its id: grade 2's id is 4 (review v1 ISS-002).
        return f"{self.grade.code}:{self.code}"
