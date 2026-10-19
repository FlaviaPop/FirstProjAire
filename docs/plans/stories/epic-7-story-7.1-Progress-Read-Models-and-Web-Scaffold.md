### Story 7.1: Progress Read Models & Web Scaffold

**BUILDID**: CYCLE-3 | **GitHub**: LOCAL | **AzureDevOps**: LOCAL | **Epic**: 7 - Progress & Score Visibility | **ID**: 7.1 | **Date**: 2026-10-19
**File**: `docs/plans/stories/epic-7-story-7.1-Progress-Read-Models-and-Web-Scaffold.md`
**Build Ref**: `docs/plans/builds/cycle-3/cycle-plan.md` — CYCLE-3 (Workshop Day 2: progress and score visibility with record scoping)
**Wave**: 11
**Requires**: [6.2]
**Enables**: [7.2, 7.3, 7.4]
**Files Touched**:
  - src/infrastructure/persistence/progress/queries.py
  - src/infrastructure/web/progress/__init__.py
  - src/infrastructure/web/progress/urls.py
  - src/infrastructure/web/progress/views/__init__.py
  - src/infrastructure/web/static/css/progress.css
  - src/infrastructure/web/templates/progress/_chapter_progress.html
  - src/config/urls.py
  - tests/integration/persistence/progress/test_progress_queries.py
**Roles Ref**: docs/requirements.md#roles--permissions-matrix — single-actor — no role variation in this story's *code paths* (read models + scaffold, no route); the queries embed the role-scoped `RecordAccessPolicy` that Stories 7.2–7.4 rely on
**QA Candidate**: No — query services, an empty URL scaffold, a shared partial and CSS, with no route. Correctness (counting rules, scoping, query bounds) is proven here by integration tests. User-observable behaviour is checked in 7.2–7.4 and 7.5.

---

#### 👤 User Reference

**Description**:
Next cycle's progress pages all need the same numbers for each student, per chapter:
- **Lesson:** has the student opened it?
- **Exercises:** how many has the student finished, out of the ones currently available?
- **Test:** is it available, and if the student took it, what was the score?

This story calculates those numbers once, the same way for every page, following the agreed rules:
- **Visible content only:** lessons and exercises count only if they're currently visible to students.
- **Earned scores stay:** a score the student earned **stays visible** even if the test is later blocked.

It also enforces who may see whose numbers. That decision is never made from what's typed in the address bar; it's always taken from who is signed in:
- a student only their own
- a parent only children an administrator linked to them
- teachers and administrators every pilot student

Finally, it prepares the skeleton the progress pages plug into: the web address group, a shared "chapter progress" display block and its styling.

**Acceptance Criteria** (plain-English):
- For any student, the platform can list each pilot chapter with lesson read or not, exercises finished out of available ones, and test status with the score when taken.
- Only content currently visible to students is counted; earned scores remain shown even for blocked tests.
- Asking for another student's progress is refused as "not found" unless the viewer is that student, an administrator-linked parent, a teacher or an administrator.
- A parent's list of children contains only children linked by the administrator.
- Teachers and administrators can get every pilot student's test scores in one list, optionally filtered by subject or chapter.
- These calculations are fast (a small, fixed number of database queries).

**User Flow**:
Actor: system — no role variation.

**Flow Diagram** (display/state matrix for one chapter row):

| Lesson state | Student opened it? | Shown as |
|---|---|---|
| ACTIVE | yes | Read |
| ACTIVE | no | Not read |
| none / hidden | any | Not available |

| Test state | Student attempt? | Shown as |
|---|---|---|
| any (even BLOCKED) | yes | Submitted · score N |
| PUBLISHED + ACTIVE | no | Available |
| draft / hidden / none | no | Not available |

| Viewer | Requested student | Result |
|---|---|---|
| Student S | S | allowed |
| Student S | T ≠ S | NotFound (404) |
| Parent P linked to S | S | allowed |
| Parent P not linked to S | S | NotFound (404) |
| Teacher / Admin | any student | allowed |
| any | non-student or unknown id | NotFound (404) |

---

#### 🤖 AI Agent Reference

**Must Read**:
- `docs/architecture/design/00-system-architecture-greenfield.md` — Progress read model (counted over visible content; submitted score stays shown), Roles & Authorization (`RecordAccessPolicy`, 404 for out-of-scope)
- `docs/architecture/design/01-patterns-and-standards-greenfield.md` — §6.3 query services (scope **inside** the query, DTOs, `select_related`/`prefetch_related`), §6.3 `child_progress` reference
- `docs/plans/stories/epic-1-story-1.3-RBAC-Core.md` — `can_view_student_records`
- `docs/plans/stories/epic-1-story-1.9-Admin-Accounts-and-Parent-Links.md` — `ParentChildLinkModel`
- `docs/plans/stories/epic-4-story-4.1-Progress-Data-and-Use-Cases.md` — `LessonViewModel`, `ExerciseCompletionModel`
- `docs/plans/stories/epic-6-story-6.2-Assessment-Data-Model.md` — `TestAttemptModel`

**Description**:
1. **`persistence/progress/queries.py`:**
   - `student_progress_for(viewer_id, viewer_role, student_id) -> StudentProgressDTO`:
     - loads `linked_student_ids` server-side (`ParentChildLinkModel.objects.filter(parent_id=viewer_id)` only when the viewer is a PARENT)
     - applies `can_view_student_records`
     - raises `NotFound` when denied **or** when `student_id` isn't an existing STUDENT
     - builds `subjects → chapters → ChapterProgressDTO`
   - `linked_children(parent_id) -> tuple[ChildDTO(student_id, full_name, tests_submitted, tests_available)]`
   - `scores_overview(subject_id: int | None = None, chapter_number: int | None = None) -> ScoresDTO(columns, rows)`:
     - columns: chapters of active subjects whose test is PUBLISHED or has ≥ 1 attempt, ordered subject then number
     - rows: active STUDENT accounts by `full_name`, each with one score per column or `None`
     - the caller (7.4) has already enforced `scores:view-all`
2. **Web scaffold:**
   - `web/progress/` (`app_name = "progress"`, `urlpatterns = []`) included at `""` in `i18n_patterns`
   - empty `views/` package
   - shared partial `templates/progress/_chapter_progress.html` (renders one `ChapterProgressDTO` with `ui_progress`, `ui_score`, status text; parameter `interactive` to show learner links only on the student's own page)
   - `static/css/progress.css`

**Design Tokens** (FE — shared partial; theme from body class):
- Chapter progress card: `ui_card`; heading "Chapter {n}: {title}" 20px/600 (student) / 16px/600 (staff).
- Lesson line: `check-circle` (`#15803D`) "Read" / `x-circle` (`#4B5563`) "Not read" / "Not available" (`#4B5563`), always with text.
- Exercises line: `ui_progress done total label="Exercises"`; total 0 → "No exercises yet".
- Test line: submitted → `ui_score` (compact) + "Submitted {date}"; available → "Available" (`#0E7490`); not available → "Not available yet" (`#4B5563`).
- Learner links (only when `interactive`): "Read lesson", "Practise", "Take the test" (secondary buttons, 44px in student theme).

**Acceptance Criteria**:
1. `student_progress_for` returns, for each active subject (ordered), its chapters (ordered by number) with:
   - `lesson_state ∈ {"read", "not_read", "unavailable"}`
   - `exercises_done` (completions of currently ACTIVE exercises only) and `exercises_total` (ACTIVE exercises)
   - `test_state ∈ {"submitted", "available", "unavailable"}`, plus `score`/`submitted_at` when submitted (regardless of the test's current moderation status)
   - ≤ **6** SQL queries for any number of chapters
2. Scoping follows the viewer/requested-student matrix exactly. The function accepts no client-supplied identity other than the requested `student_id`, and `viewer_id`/`viewer_role` must come from `request.user` (docstring + 7.2–7.4 tests).
3. `linked_children(parent_id)` returns only students linked to that parent, ordered by `full_name`, with `tests_submitted` (attempt count) and `tests_available` (PUBLISHED + ACTIVE tests in active subjects); ≤ 3 queries.
4. `scores_overview` returns columns and rows as described. A BLOCKED test that has attempts still appears as a column with its scores. Filters narrow the columns. ≤ 3 queries.
5. Inactive students (`is_active=False`) are excluded from `scores_overview` and from parents' lists; their own progress is still readable by teachers/admins via `student_progress_for`.
6. `web/progress/urls.py` is included in `config/urls.py` (empty patterns, so the URL-coverage test passes). The partial renders a `ChapterProgressDTO` (tested via `render_to_string`).
7. Coverage ≥ 90% for `queries.py`.

**RBAC Enforcement**:
No role-differentiated access — single actor.
- No route here. The scoping rule lives **inside** `student_progress_for` (patterns §6.3: scope inside the query, never after loading). `linked_student_ids` is always loaded from the DB for the viewer; request parameters can't extend it (IDOR guard). Route-level permissions are added by 7.2 (`scores:view-own`), 7.3 (`child-progress:view` + `child-scores:view`) and 7.4 (`scores:view-all`).

**System responses + error cases** (query contract):

| Trigger | Response | Side-effect |
|---------|----------|-------------|
| Student S asks for S | `StudentProgressDTO` | none |
| Same call repeated | identical DTO | none |
| Student S asks for T | `NotFound` | none |
| Parent linked to S asks for S | DTO | none |
| Parent not linked asks for S | `NotFound` | none |
| Teacher/Admin asks for any student | DTO | none |
| Any viewer asks for a teacher's id / unknown id | `NotFound` | none |
| Chapter with BLOCKED lesson | `lesson_state="unavailable"` | none |
| 1 of 6 exercises BLOCKED, student finished the blocked one + 2 others | `exercises_done=2, exercises_total=5` | none |
| Test BLOCKED after the student's attempt | `test_state="submitted"`, score shown | none |
| `scores_overview(subject_id=MEM)` | only MEM columns | none |

**Prerequisites**:
- Story 6.2 (attempt model) merged; CYCLE-1/2 models (links, progress records, content).

**Context**: `docs/architecture/design/01-patterns-and-standards-greenfield.md`, `src/domain/accounts/access_policy.py`, `src/infrastructure/persistence/accounts/models.py`, `src/infrastructure/persistence/progress/models.py`, `src/infrastructure/persistence/assessment/models.py`, `src/infrastructure/persistence/content/models.py`

**Patterns**: Query services with in-query scoping (§6.3), Primitives (§11.2) — see `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Steps**:

1. **Tests first** (matrix-driven scoping tests; counting rules; query-count bounds).

2. **Scoping entry point** (excerpt):
   ```python
   # src/infrastructure/persistence/progress/queries.py
   def student_progress_for(viewer_id: int, viewer_role: str, student_id: int) -> StudentProgressDTO:
       """Progress of one student, visible only per RecordAccessPolicy.

       viewer_id / viewer_role MUST come from request.user (session) — never from request input.
       """
       linked = (set(ParentChildLinkModel.objects.filter(parent_id=viewer_id).values_list("student_id", flat=True))
                 if viewer_role == "PARENT" else set())
       if not can_view_student_records(viewer_id, viewer_role, student_id, linked):
           raise NotFound("student")  # 404, never 403: do not reveal the child exists
       student = UserModel.objects.filter(pk=student_id, role="STUDENT").only("id", "full_name").first()
       if student is None:
           raise NotFound("student")
       return _build_progress(student)
   ```

3. **Builder** `_build_progress(student)`: one query each for active subjects with chapters (prefetch), visible lessons + this student's views, visible exercises count + this student's completions on visible ones, visible tests, and this student's attempts. Combine in Python into DTOs (≤ 6 queries).

4. **Scaffold** (`urls.py`, `views/__init__.py`, include in `config/urls.py`), **partial**, **CSS**, then **all gates**.

**Tests**:

```python
# tests/integration/persistence/progress/test_progress_queries.py
import pytest

from domain.common.errors import NotFound
from infrastructure.persistence.catalogue.models import SubjectModel
from infrastructure.persistence.content.models import ChapterTestModel, ExerciseModel, LessonModel
from infrastructure.persistence.progress.models import ExerciseCompletionModel, LessonViewModel
from infrastructure.persistence.progress.queries import linked_children, scores_overview, student_progress_for
from tests.factories.accounts import ParentChildLinkFactory, ParentFactory, StudentFactory
from tests.factories.assessment import attempt_for
from tests.factories.content import complete_chapter

pytestmark = pytest.mark.django_db
NOW = "2026-11-08T09:00Z"


@pytest.fixture
def setup():
    mem = SubjectModel.objects.get(grade__code="2", code="MEM")
    chapter = complete_chapter(mem, 1)
    student, other = StudentFactory(), StudentFactory()
    return mem, chapter, student, other


def chapter_row(dto, number=1, code="MEM"):
    subject = next(s for s in dto.subjects if s.code == code)
    return next(c for c in subject.chapters if c.number == number)


@pytest.mark.parametrize(("viewer", "allowed"), [("self", True), ("other_student", False), ("linked_parent", True),
                                                  ("unlinked_parent", False), ("teacher", True), ("admin", True)])
def test_scoping_matrix(setup, viewer, allowed, teacher, admin_user):
    _, _, student, other = setup
    linked = ParentFactory()
    ParentChildLinkFactory(parent=linked, student=student)
    viewers = {"self": student, "other_student": other, "linked_parent": linked,
               "unlinked_parent": ParentFactory(), "teacher": teacher, "admin": admin_user}
    who = viewers[viewer]

    if allowed:
        assert student_progress_for(who.pk, who.role, student.pk).student_id == student.pk
    else:
        with pytest.raises(NotFound):
            student_progress_for(who.pk, who.role, student.pk)


def test_non_student_ids_are_not_found(setup, teacher, admin_user):
    with pytest.raises(NotFound):
        student_progress_for(admin_user.pk, "ADMIN", teacher.pk)


def test_counts_only_visible_content_and_keeps_blocked_scores(setup):
    _, chapter, student, _ = setup
    LessonViewModel.objects.create(student=student, lesson=chapter.lesson, first_viewed_at=NOW)
    exercises = list(ExerciseModel.objects.filter(chapter=chapter).order_by("position"))
    for exercise in exercises[:3]:
        ExerciseCompletionModel.objects.create(student=student, exercise=exercise, completed_at=NOW)
    ExerciseModel.objects.filter(pk=exercises[0].pk).update(moderation_status="BLOCKED")
    attempt_for(student, chapter.test, correct_positions={1, 2})
    ChapterTestModel.objects.filter(pk=chapter.test.pk).update(moderation_status="BLOCKED")

    row = chapter_row(student_progress_for(student.pk, "STUDENT", student.pk))

    assert (row.lesson_state, row.exercises_done, row.exercises_total) == ("read", 2, 4)
    assert (row.test_state, row.score) == ("submitted", 20)


def test_hidden_lesson_is_unavailable(setup):
    _, chapter, student, _ = setup
    LessonModel.objects.filter(chapter=chapter).update(moderation_status="FLAGGED")

    assert chapter_row(student_progress_for(student.pk, "STUDENT", student.pk)).lesson_state == "unavailable"


def test_progress_query_count_is_bounded(setup, django_assert_max_num_queries):
    mem, _, student, _ = setup
    complete_chapter(mem, 2)
    complete_chapter(mem, 3)

    with django_assert_max_num_queries(6):
        student_progress_for(student.pk, "STUDENT", student.pk)


def test_parent_sees_only_linked_children(setup):
    _, _, student, other = setup
    parent = ParentFactory()
    ParentChildLinkFactory(parent=parent, student=student)

    assert [c.student_id for c in linked_children(parent.pk)] == [student.pk]


def test_scores_overview_includes_blocked_test_scores(setup):
    _, chapter, student, other = setup
    attempt_for(student, chapter.test, correct_positions=set(range(1, 11)))
    ChapterTestModel.objects.filter(pk=chapter.test.pk).update(moderation_status="BLOCKED")

    overview = scores_overview()

    column = next(i for i, c in enumerate(overview.columns) if c.chapter_id == chapter.pk)
    scores = {r.student_id: r.scores[column] for r in overview.rows}
    assert scores[student.pk] == 100 and scores[other.pk] is None
```

Manual: none (no route). Reviewers check the scoping entry point and the query-count assertions.

**Quality**: ruff 0; mypy passes; tests pass; coverage ≥ 90% for `queries.py`; query bounds asserted; no `TODO`.

**OUT**:
- ❌ The pages themselves (7.2 student, 7.3 parent, 7.4 scores).
- ❌ Exporting data, charts or trends (not required).
- ❌ Per-question test details (final score only).

**Evidence**: pytest output (scoping matrix, counting rules, bounds), coverage %, all recorded in `docs/stories-implemented/story-7.1-review.md` under "## DoD Evidence".
