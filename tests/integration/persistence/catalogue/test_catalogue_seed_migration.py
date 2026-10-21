"""Forward/reverse behaviour of the 0002_seed_catalogue data migration (patterns §6.4).

The seed functions are called with the live app registry. It resolves the same model names as
the historical registry, which lets each test run inside the rolled-back `db` transaction.
"""

import importlib
from collections.abc import Iterator

import pytest
from django.apps import apps as live_apps
from django.db import connection, models, transaction
from django.db.models import ProtectedError

from infrastructure.persistence.catalogue.models import GradeModel, SubjectModel

pytestmark = pytest.mark.django_db

seed_migration = importlib.import_module(
    "infrastructure.persistence.catalogue.migrations.0002_seed_catalogue"
)

SEEDED_GRADES = 9
SEEDED_SUBJECTS = 106


def _snapshot() -> list[tuple[str, str, int, str, str, bool]]:
    return list(
        SubjectModel.objects.values_list(
            "grade__code", "code", "sort_order", "name_ro", "name_en", "is_active"
        )
    )


def test_rerunning_the_seed_on_a_seeded_db_creates_nothing():
    before = _snapshot()

    seed_migration.seed(live_apps, None)

    assert GradeModel.objects.count() == SEEDED_GRADES
    assert _snapshot() == before


def test_rerunning_the_seed_after_a_partial_run_creates_only_missing_rows():
    before = _snapshot()
    SubjectModel.objects.filter(grade__code="8").delete()
    GradeModel.objects.filter(code="8").delete()

    seed_migration.seed(live_apps, None)

    assert GradeModel.objects.count() == SEEDED_GRADES
    assert sorted(_snapshot()) == sorted(before)


def test_unseed_removes_every_seeded_row():
    seed_migration.unseed(live_apps, None)

    assert GradeModel.objects.count() == 0
    assert SubjectModel.objects.count() == 0


def test_unseed_leaves_rows_added_later_by_other_means_untouched():
    later_grade = GradeModel.objects.create(code="9", sort_order=9, name_ro="IX", name_en="9")
    SubjectModel.objects.create(
        grade=later_grade, code="MAT", sort_order=1, name_ro="Matematică", name_en="Math"
    )

    seed_migration.unseed(live_apps, None)

    assert list(GradeModel.objects.values_list("code", flat=True)) == ["9"]
    assert list(SubjectModel.objects.values_list("grade__code", "code")) == [("9", "MAT")]


def test_unseed_fails_loudly_when_a_seeded_grade_holds_a_later_subject():
    grade = GradeModel.objects.get(code="2")
    SubjectModel.objects.create(grade=grade, code="NEW", sort_order=50, name_ro="x", name_en="x")

    with pytest.raises(ProtectedError), transaction.atomic():
        seed_migration.unseed(live_apps, None)

    assert GradeModel.objects.count() == SEEDED_GRADES
    assert SubjectModel.objects.count() == SEEDED_SUBJECTS + 1


@pytest.fixture
def later_content_model() -> Iterator[type[models.Model]]:
    """Stand-in for a CYCLE-2 content table holding a PROTECT foreign key to a subject."""
    with connection.cursor() as cursor:
        cursor.execute(
            "CREATE TABLE catalogue_probe_chapter (id integer PRIMARY KEY AUTOINCREMENT,"
            " subject_id bigint NOT NULL REFERENCES catalogue_subject (id))"
        )

    # Registered under an installed label: Django builds reverse relations (which drive
    # PROTECT) only from installed apps. Unregistered again on teardown.
    class ProbeChapterModel(models.Model):
        subject = models.ForeignKey(SubjectModel, on_delete=models.PROTECT, related_name="+")

        class Meta:
            app_label = "catalogue"
            db_table = "catalogue_probe_chapter"
            managed = False

        def __str__(self) -> str:
            return f"probe:{self.pk}"

    yield ProbeChapterModel
    del live_apps.all_models["catalogue"]["probechaptermodel"]
    live_apps.clear_cache()


def test_unseed_fails_loudly_when_later_content_references_a_subject(later_content_model):
    later_content_model.objects.create(
        subject=SubjectModel.objects.get(grade__code="2", code="MEM")
    )

    with pytest.raises(ProtectedError), transaction.atomic():
        seed_migration.unseed(live_apps, None)

    assert GradeModel.objects.count() == SEEDED_GRADES
    assert SubjectModel.objects.count() == SEEDED_SUBJECTS


def test_seed_migration_runs_after_the_schema_and_is_reversible():
    migration = seed_migration.Migration("0002_seed_catalogue", "catalogue")

    assert migration.dependencies == [("catalogue", "0001_initial")]
    assert migration.operations[0].reversible is True
