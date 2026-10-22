# Code Review - Story 2.1: Catalogue Data

**Date**: 2026-10-22
**Reviewed By**: REVIEWER Agent
**Review Number**: 1
**Review Mode**: INITIAL_REVIEW
**Status**: ⚠️ APPROVED WITH COMMENTS

---

## Review Metadata

**Previous Review**: None
**Previous Status**: N/A
**Files Changed Since Last Review**: All (first review). Reviewed at `main` @ `e82d2fd`
**Severity Threshold Applied**: All

---

## Review Summary

**Components Reviewed**:
- `src/infrastructure/persistence/catalogue/apps.py`
- `src/infrastructure/persistence/catalogue/models.py` (48 lines)
- `migrations/0001_initial.py`
- `migrations/0002_seed_catalogue.py` (195 lines, reviewed by hand because migrations are excluded from ruff and coverage)
- `src/config/settings/base.py` (`INSTALLED_APPS`)
- `tests/factories/catalogue.py`

**Lines of Code**: ~260 production lines (mostly inlined seed data), ~590 test lines
**Tests Reviewed**: Yes:
- `tests/integration/persistence/catalogue/test_catalogue_seed.py` (227)
- `test_catalogue_constraints.py` (103)
- `test_catalogue_seed_migration.py` (128)
- `test_catalogue_migrate_commands.py` (98; separate `manage.py` processes)
- `test_catalogue_factories.py` (32)

**Coverage**: 100% overall (catalogue `models.py` 25/25). Migrations are omitted from coverage by config; the seed functions are exercised directly by `test_catalogue_seed_migration.py`.

**Overall Assessment**: A careful, well-tested data story:
- The seed matches the owner-confirmed tables exactly. I recounted it (5 + 8 + 8 + 8 + 9 + 11 + 14 + 15 + 17 + 16 = 111 subjects, 10 levels), and the tests compare it against an **independent copy** of the tables, not the migration's own constants.
- Reversibility is proven both in-process (including a real `PROTECT` stand-in for CYCLE-2 content) and through real `manage.py migrate` / `migrate catalogue zero` round-trips in separate processes.
- The owner's AC 10 confirmation is recorded in the self-review.

The findings are small and concern test support and debuggability:
- The factories collide on `sort_order` for every new code (ISS-001).
- `SubjectModel.__str__` shows the grade's database id, so grade 2's English reads `"4:EN"` (ISS-002).
- Empty names are only prevented by tests of the seed, not by the database (ISS-003).

---

## Evidence Verified (re-run by REVIEWER, 2026-10-22)

```
$ uv run ruff format --check .        → 130 files already formatted
$ uv run ruff check .                 → All checks passed!
$ uv run mypy                         → Success: no issues found in 95 source files
$ PYTHONPATH=src uv run lint-imports  → Contracts: 2 kept, 0 broken.
$ manage.py makemigrations --check --dry-run → No changes detected
$ uv run pytest -q --cov=src --cov-branch --cov-fail-under=85
src/infrastructure/persistence/catalogue/apps.py              5      0      0      0   100%
src/infrastructure/persistence/catalogue/models.py           25      0      0      0   100%
TOTAL                                                       701      0     82      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
782 passed in 7.05s
$ uv run pytest -q tests/integration/persistence/catalogue → 46 passed in 2.37s (includes the 4 subprocess migrate tests)
```

**Probes**: a temporary test file, deleted afterwards. The working tree was clean after the run.

```
PROBE str(grade 2 EN)  -> '4:EN'      ← ISS-002 (reads as grade 4)
PROBE str(grade 4 EN)  -> '6:EN'      ← ISS-002
PROBE str(grade K DLC) -> '1:DLC'     ← ISS-002 (reads as grade 1)
PROBE SubjectFactory(code='NEW')  [grade 2]       -> IntegrityError: UNIQUE constraint failed: catalogue_subject.grade_id, catalogue_subject.sort_order   ← ISS-001
PROBE GradeFactory(code='9')                      -> IntegrityError: UNIQUE constraint failed: catalogue_grade.sort_order   ← ISS-001
PROBE SubjectFactory(code='X', grade=grade 3)     -> IntegrityError (same)   ← ISS-001
PROBE SubjectModel.create(name_ro='', name_en='') -> created               ← ISS-003
```

---

## Acceptance Criteria Check

| AC | Result | Evidence |
|----|--------|----------|
| 1 App `catalogue` installed | ✅ | `base.py:22`; `apps.py` (`label="catalogue"`) |
| 2 `GradeModel` schema | ✅ | `test_grade_model_schema_matches_the_story_contract` |
| 3 `SubjectModel` schema, `PROTECT`, named constraints, ordering | ✅ | `test_subject_model_schema…`, `test_subject_unique_constraints_are_named_as_specified`, `test_default_ordering…` |
| 4 Seed: 10 levels `K`=0, `P`=1, `1..8`=2..9; listed order from 1; only grade 2 CLR/MEM/EN active | ✅ | `test_ten_levels_in_display_order`, `test_each_grade_has_its_proposed_subjects_in_display_order` (×10), `test_only_grade_two_clr_mem_en_are_active` |
| 5 Reverse removes only seeded rows; fails loudly on dependants | ✅ | `test_unseed_leaves_rows_added_later…`, `test_unseed_fails_loudly_when_a_seeded_grade_holds_a_later_subject`, `…_when_later_content_references_a_subject` (real `PROTECT` FK stand-in) |
| 6 Historical models only; idempotent `get_or_create` | ✅ | `0002` imports only `django.db` and typing; `test_rerunning_the_seed_on_a_seeded_db_creates_nothing`, `…_after_a_partial_run_creates_only_missing_rows` |
| 7 Counts 10 / 111; exactly 3 active; names non-empty | ✅ (for the seed; see ISS-003) | `test_subject_total_matches_the_proposal`, `test_every_name_is_bilingual`, subprocess `COUNTS == "10 111"` |
| 8 `makemigrations --check`; `zero` round-trip | ✅ | Gate above; `test_migrate_catalogue_zero_then_migrate_round_trips` |
| 9 `GradeFactory` / `SubjectFactory` with `get_or_create` on codes | ⚠️ | Seeded codes work; **new codes collide** unless `sort_order` is passed (ISS-001) |
| 10 Owner confirmation recorded | ✅ | `docs/stories-implemented/story-2.1-review.md` "Owner confirmation (AC 10)", 2026-10-21; Story 2.1 and 2.2 docs updated |

---

## Checklist Results

### Correctness
- [x] ✅ Seeded content equals the confirmed tables (independent oracle in tests)
- [x] ✅ Forward is idempotent; reverse is exact and refuses to orphan
- [x] ✅ Constraints enforced in the DB (`IntegrityError` and `ProtectedError` tested)
- [x] ⚠️ `__str__` uses the grade id, not the code (ISS-002)

### Pattern Adherence
- [x] ✅ §6.2: `<Entity>Model`, explicit `db_table`, named `Meta.constraints`
- [x] ✅ §6.4: reversible `RunPython`, data inlined, no fixtures, no import of `models.py`
- [x] ✅ ADR-006: paired `_ro`/`_en` columns
- [x] ✅ No domain package (no business rules), as the story specifies; import-linter kept

### Testing
- [x] ✅ Tests compare against an independent copy of the owner's tables
- [x] ✅ Real `manage.py` processes prove install, restart, repeat and rollback
- [x] ✅ `PROTECT` from future content is proven with a managed=False stand-in that is cleaned up on teardown
- [x] ⚠️ The factory test hides the `sort_order` collision by always passing `sort_order` (ISS-001)

### Documentation
- [x] ✅ Docstrings explain why the data is inlined, the reverse semantics and the "0003 for changes" rule
- [x] ✅ Self-review records the subject-count reasoning and the owner decision

### Security
- [x] ✅ Reference data only; no personal data; no routes

### Performance
- [x] ✅ 111 rows seeded once; `Meta.ordering` on indexed unique columns

### SOLID / Anti-Monolith
- [x] ✅ Self-contained app; no dependencies on other contexts

---

## Issues Found

### ISS-001: The catalogue factories collide on `sort_order` for any new code 🟡 Medium

**Category**: Testing / Maintainability
**File**: `tests/factories/catalogue.py:14, 28`
**Pattern Reference**: Story 2.1 AC 9 ("for Story 2.2 and CYCLE-2 tests"); patterns §12.3 (factories give valid defaults)

**Issue**:
Both factories hard-code `sort_order` (grade `3`, subject `2`). `django_get_or_create` looks up by code only, so for a **seeded** code the defaults are ignored and the seeded row comes back. For any **new** code the hard-coded `sort_order` is inserted and collides with the seeded row that already holds it:
- `GradeFactory(code="9")` → `IntegrityError: UNIQUE constraint failed: catalogue_grade.sort_order`
- `SubjectFactory(code="NEW")` in grade 2, or `SubjectFactory(code="X", grade=<grade 3>)` → `UNIQUE … (grade_id, sort_order)`

`test_factories_create_new_rows_for_unseeded_codes` passes only because it supplies `sort_order` explicitly. Story 2.2 and the CYCLE-2 content stories will need extra subjects (for example an inactive subject, or a second active one) and will hit this first.

Also, `SubjectFactory` defaults to `is_active=True`, so a new subject created in any grade is silently active, which contradicts the catalogue's main invariant. The seeded MEM row keeps `True` regardless, because `get_or_create` doesn't apply defaults to existing rows.

**Current Code**:
```python
class GradeFactory(factory.django.DjangoModelFactory):
    ...
    sort_order = 3
...
class SubjectFactory(factory.django.DjangoModelFactory):
    ...
    sort_order = 2
    ...
    is_active = True
```

**Suggested Fix**: unique-by-default orders above the seeded range, and inactive by default:
```python
class GradeFactory(factory.django.DjangoModelFactory):
    ...
    sort_order = factory.Sequence(lambda n: 100 + n)  # seeded grades use 0-9


class SubjectFactory(factory.django.DjangoModelFactory):
    ...
    sort_order = factory.Sequence(lambda n: 100 + n)  # seeded subjects use 1-17 per grade
    is_active = False  # the seeded MEM row stays active: get_or_create keeps existing rows
```

**Suggested Test**:
```python
def test_factories_create_new_rows_without_explicit_sort_order():
    grade = GradeFactory(code="9", name_ro="Clasa a IX-a", name_en="Grade 9")
    extra = SubjectFactory(grade=GradeModel.objects.get(code="2"), code="NEW")

    assert (grade.code, extra.code, extra.is_active) == ("9", "NEW", False)


def test_subject_factory_still_returns_the_seeded_active_mem_subject():
    assert SubjectFactory().is_active is True
```

---

### ISS-002: `SubjectModel.__str__` shows the grade's database id, which reads as a different grade 🟢 Low

**Category**: Correctness (debuggability)
**File**: `src/infrastructure/persistence/catalogue/models.py:47-48`; `tests/integration/persistence/catalogue/test_catalogue_seed.py:223-227`

**Issue**:
`f"{self.grade_id}:{self.code}"` prints the grade's primary key. Seeded grade 2 has id 4, so its English subject prints as `"4:EN"`, grade K's first domain as `"1:DLC"` (probe). The obvious reading is "grade 4" or "grade 1". These strings show up in shells, error messages, admin and log lines. The test is named `…identifies_grade_and_subject_by_code` but asserts the id form.

**Current Code**:
```python
def __str__(self) -> str:
    return f"{self.grade_id}:{self.code}"
```

**Suggested Fix**:
```python
def __str__(self) -> str:
    # Grade *code* ("2:EN"), not the id: grade 2's id is 4. One query unless grade is loaded.
    return f"{self.grade.code}:{self.code}"
```
Update the test to `assert str(subject) == "2:EN"`.

---

### ISS-003: Empty bilingual names are prevented only by tests of the seed, not by the database 🟢 Low

**Category**: Correctness (defence in depth)
**File**: `src/infrastructure/persistence/catalogue/models.py:15-16, 32-33`
**Pattern Reference**: Story 2.1 AC 7 ("every name field is non-empty in both languages"); ADR-006; Story 1.4 `localized()` ("never silently show the other language")

**Issue**:
AC 7 is verified for the seeded rows only. The schema accepts `name_ro=""` / `name_en=""` (probe: created). Catalogue changes are made through follow-up data migrations (`0003_…`, per the story), and those run without the seed tests guarding them. A blank name would render as an empty heading through `localized()`.

**Suggested Fix**: a schema migration `0003_name_not_empty` with check constraints:
```python
constraints = [
    ...,
    models.CheckConstraint(
        condition=~models.Q(name_ro="") & ~models.Q(name_en=""),
        name="subject_names_not_empty",
    ),
]
```
Add the same `grade_names_not_empty` constraint on `GradeModel`, with tests that an empty name raises `IntegrityError`.

---

## Issue Summary

| # | ID | Severity | Category | File | Status |
|---|-----|----------|----------|------|--------|
| 1 | ISS-001 | 🟡 Medium | Testing | `tests/factories/catalogue.py:14, 28` | Should Fix |
| 2 | ISS-002 | 🟢 Low | Correctness | `catalogue/models.py:47-48` | Optional |
| 3 | ISS-003 | 🟢 Low | Correctness | `catalogue/models.py` | Optional |

**Summary**:
- Blockers: 0
- High: 0
- Medium: 1
- Low: 2

---

## What Was Done Well

1. ✅ **Independent oracle**: the seed tests hold their own copy of the owner's tables, so a typo in the migration can't also "pass" the test.
2. ✅ **Real rollback proof**: subprocess `migrate` / `migrate catalogue zero` / `migrate` on a fresh SQLite file, exactly what install, restart and rollback do.
3. ✅ **`PROTECT` proven ahead of time** with a stand-in content table, so CYCLE-2 inherits a verified "reverse fails loudly" guarantee.
4. ✅ **Exact reverse**: deletes only seeded (grade, subject) pairs and leaves later rows alone (tested).
5. ✅ **Clear history**: the migration docstring explains why the data is inlined, and the self-review records the 111 vs 119 count reasoning and the owner's decision.

---

## Approval Status

**Decision**: ⚠️ APPROVED WITH COMMENTS

**Reason**: no blockers and no high-severity issues. ISS-001 should be fixed before Story 2.2 and CYCLE-2 tests start creating catalogue rows. ISS-002 and ISS-003 are cheap hardening.

**Next Steps**:
1. `aire-dev-remediate` for ISS-001 (recommended), with ISS-002 and ISS-003 optional.

---

## Sign-Off

**Reviewer**: REVIEWER Agent
**Date**: 2026-10-22
**Signature**: Approved with comments
