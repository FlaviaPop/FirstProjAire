### Story 3.1: Content Domain Rules

**BUILDID**: CYCLE-2 | **GitHub**: LOCAL | **AzureDevOps**: LOCAL | **Epic**: 3 - Teacher Content Authoring | **ID**: 3.1 | **Date**: 2026-10-19
**File**: `docs/plans/stories/epic-3-story-3.1-Content-Domain-Rules.md`
**Build Ref**: `docs/plans/builds/cycle-2/cycle-plan.md` — CYCLE-2 Content Authoring & Learning (Workshop Day 1: content model + rules)
**Wave**: 6
**Requires**: [1.10]
**Enables**: [3.4, 3.5, 3.7, 3.8, 4.1, 4.3]
**Files Touched**:
  - src/domain/common/numbers.py
  - src/domain/content/**
  - src/domain/moderation/**
  - src/application/content/__init__.py
  - tests/unit/domain/common/test_numbers.py
  - tests/unit/domain/content/**
  - tests/unit/domain/moderation/**
**Roles Ref**: docs/requirements.md#roles--permissions-matrix — single-actor — no role variation (pure business rules; who may invoke them is enforced by the web stories 3.5–3.8)
**QA Candidate**: No — pure domain library with no route, UI or persistence. It's verified exhaustively by unit tests at 100% coverage, and its behaviour becomes user-observable through Stories 3.5–3.8 and 4.3, where QA checks it.

---

#### 👤 User Reference

**Description**:
This story writes down, as precise rules the computer can check, everything the requirements say about how learning content must be built.

**Questions** (used by exercises and test questions). There are three kinds:
- **Multiple choice:** 2 to 6 answer options, each written in Romanian and English, exactly one of them correct.
- **True/false:** the correct answer is either "true" or "false".
- **Number:** the correct answer is a number. "2", "2.0" and "2,0" (the Romanian decimal comma) all mean the same number.

Every question must have its wording in both languages.

**Chapter tests** can be published only when:
- they have exactly 10 questions
- every question is worth at least 1 point
- the points add up to exactly 100
- every question is complete in both languages

When a test isn't ready, the rules list **every** problem at once (for example "question 4 has no correct answer" and "points total 95, must be 100"), so the teacher can fix them all in one go.

**Chapters and exercises:**
- each pilot subject has exactly chapters 1, 2 and 3
- a chapter can have at most 10 exercises
- a chapter needs at least 5 exercises to count as complete

**Moderation:** this story also defines the four states content can be in (active, flagged, blocked, resubmitted) and the one rule that matters already: only *active* content is ever shown to students and parents. The administrator's actions that change these states arrive in the next cycle.

Nothing visible changes yet; the teacher and student screens in the following stories use these rules.

**Acceptance Criteria** (plain-English):
- Multiple-choice questions need 2–6 options, each in both languages, with one correct option that exists.
- True/false questions need a true or false answer; number questions need a valid number as the answer.
- "2", "2.0", "2,0" and " 2.00 " are treated as the same number; text that isn't a number is rejected as a correct answer.
- Every question needs its wording in both Romanian and English.
- A test can be published only with exactly 10 questions, each worth at least 1 point, totalling exactly 100 points, and all complete.
- When a test can't be published, every reason is listed, each pointing to the question it concerns.
- Chapters are numbered 1 to 3 within a subject, and a number can't be used twice.
- A chapter can have at most 10 exercises, and needs at least 5 to count as complete.
- Only content in the "active" state counts as visible to students and parents.

**User Flow**:
Actor: system — no role variation.

**Flow Diagram** (rule matrix: pure domain story):

| Rule | Input | Valid when | Violation code (params) |
|------|-------|-----------|--------------------------|
| Prompt bilingual | `prompt_ro`, `prompt_en` | both non-blank | `prompt_missing_ro` / `prompt_missing_en` |
| MCQ options | `options` | 2–6 items, ids unique in a–f, `ro` and `en` non-blank | `options_count` {count} · `option_text_missing` {option} |
| MCQ key | `answer_key` | `{"option_id": x}` with x among option ids | `answer_key_invalid` |
| TF key | `answer_key` | `{"value": true|false}`; `options == []` | `answer_key_invalid` · `options_not_allowed` |
| NUMERIC key | `answer_key` | `{"value": canonical decimal}`; `options == []` | `answer_key_invalid` · `options_not_allowed` |
| Exercise explanation | `explanation_ro/en` | both non-blank | `explanation_missing_ro` / `explanation_missing_en` |
| Test count | questions | exactly 10, positions 1–10 unique | `questions_count` {count} · `positions_invalid` |
| Test points | each `points` | integer ≥ 1 | `points_below_minimum` {position} |
| Test total | Σ points | == 100 | `points_total_not_100` {total} |
| Test question validity | each question | no question violations | the question's code + {position} |
| Chapter number | number, taken numbers | 1 ≤ n ≤ 3 and not taken | `chapter_number_out_of_range` {number} · `chapter_number_taken` {number} |
| Exercise limit | current count | count < 10 | `exercises_limit` {limit} |
| Learner visibility | moderation status | status == ACTIVE | — (boolean) |

---

#### 🤖 AI Agent Reference

**Must Read**:
- `docs/requirements.md` — Features "Course lessons and practice", "Chapter tests" (10 questions, weights total 100, numeric equivalence), "Teacher-managed content and admin moderation"
- `docs/architecture/design/00-system-architecture-greenfield.md` — Key Domain Logic (scoring + numeric normalisation), Answer key formats table, Moderation state machine (statuses), Integrity rules
- `docs/architecture/design/01-patterns-and-standards-greenfield.md` — §4 domain pattern (frozen dataclasses, `StrEnum`, lookup tables), `parse_numeric` reference implementation, §3 layering (stdlib only)
- `docs/plans/stories/epic-1-story-1.1-Error-Handling-and-Observability.md` — `Violation`, `PolicyViolation`, `NotFound`

**Description**:
Pure-Python content rules and ports, the foundation for every CYCLE-2 authoring and learning story:
1. **`domain/common/numbers.py`:** `parse_numeric(raw) -> Decimal | None` (patterns §4 reference implementation) and `canonical_decimal(value) -> str` (no exponent, no trailing zeros, `-0` → `0`).
2. **`domain/content/questions.py`:** `QuestionKind` StrEnum; `Option` and `ExerciseDraft`/`QuestionDraft` frozen dataclasses; `validate_question(...)`, `validate_exercise(draft)`, `numeric_answer_key(raw)`.
3. **`domain/content/publication.py`:** `check_publishable(questions) -> list[Violation]`, with constants `QUESTIONS_PER_TEST = 10`, `TOTAL_POINTS = 100`, `MIN_POINTS = 1`.
4. **`domain/content/chapters.py`:** `CHAPTERS_PER_SUBJECT = 3`, `MAX_EXERCISES_PER_CHAPTER = 10`, `MIN_EXERCISES_FOR_READY = 5`, `validate_chapter_number(number, taken)`, `exercise_limit_violation(count)`, and `chapter_is_ready(...)`: the single launch-readiness rule (SC-2/FC-1) shared by the teacher dashboard (3.5) and the pilot readiness page (5.1).
5. **`domain/content/ports.py`:** Protocols `ChapterRepository`, `LessonRepository`, `ExerciseRepository`, `ChapterTestRepository`, implemented by Stories 3.5–3.8.
6. **`domain/moderation/status.py`:** `ModerationStatus` StrEnum + `is_visible_to_learners(status)`. The state machine itself is CYCLE-3.
7. **`application/content/__init__.py`:** empty package, so the wave-8 use-case stories never create it concurrently.

> **Refinement of patterns §4:** `parse_numeric` lives in `domain/common/numbers.py` instead of `domain/assessment/answer_checker.py`. Content needs it now to validate numeric answer keys; CYCLE-3's `AnswerChecker` imports it from here (no duplication).

**Acceptance Criteria**:
1. `parse_numeric` matches the patterns implementation (spaces incl. NBSP/NNBSP stripped, single comma → dot when no dot, `InvalidOperation` → `None`, non-finite → `None`). `canonical_decimal(Decimal("2.50")) == "2.5"`, `canonical_decimal(Decimal("1E+2")) == "100"`, `canonical_decimal(Decimal("-0.0")) == "0"`.
2. `QuestionKind` values are exactly `MCQ`, `TRUE_FALSE`, `NUMERIC`. `OPTION_IDS = ("a","b","c","d","e","f")`. `Option(id, ro, en)` is frozen.
3. `validate_question(kind, prompt_ro, prompt_en, options, answer_key) -> list[Violation]` implements the rule matrix rows "Prompt bilingual", "MCQ options", "MCQ key", "TF key" and "NUMERIC key". It returns **all** violations, in that order. Whitespace-only text counts as blank.
4. `numeric_answer_key(raw: str) -> dict | None` returns `{"value": canonical_decimal(parse_numeric(raw))}` or `None` when unparseable.
5. `ExerciseDraft(kind, prompt_ro, prompt_en, options, answer_key, explanation_ro, explanation_en)`; `validate_exercise(draft)` = question violations + explanation violations.
6. `QuestionDraft(position, kind, prompt_ro, prompt_en, options, answer_key, points)`; `check_publishable(questions)`:
   - `questions_count` if `len != 10`
   - `positions_invalid` if positions ≠ {1…10}
   - per question: `points_below_minimum` {position} when points < 1, plus each question violation with `position` added to its params
   - `points_total_not_100` {total} when Σ ≠ 100

   The empty list means publishable. Order: count, positions, per-question in position order, total.
7. `validate_chapter_number(number, taken: Collection[int])` → `chapter_number_out_of_range` or `chapter_number_taken`. `exercise_limit_violation(count)` → `Violation("exercises_limit", {"limit": 10})` when `count >= 10`, else `None`. `chapter_is_ready(has_active_lesson: bool, visible_exercises: int, test_visible: bool, test_questions: int) -> bool` ⇔ lesson active **and** `MIN_EXERCISES_FOR_READY ≤ visible_exercises ≤ MAX_EXERCISES_PER_CHAPTER` **and** test visible (PUBLISHED + ACTIVE; publishing already guarantees Σ points = 100) **and** `test_questions == QUESTIONS_PER_TEST`.
8. `ModerationStatus` values `ACTIVE`, `FLAGGED`, `BLOCKED`, `RESUBMITTED`; `is_visible_to_learners(s)` uses `==` (works for plain strings loaded from the DB).
9. `domain/content/ports.py` defines the four Protocols exactly as in Step 5 (method names and signatures are a contract for 3.5–3.8 and 4.x).
10. The domain packages import only the stdlib and `domain.*` (import-linter "Domain is framework-free" kept). `mypy --strict` passes.
11. Coverage of `src/domain/common/numbers.py`, `src/domain/content/**` and `src/domain/moderation/**` is **100%** (statements + branches).

**RBAC Enforcement**:
No role-differentiated access — single actor.
- Pure functions and Protocols; no identity is involved. Use cases in 3.5–3.8 receive `actor_id` from `request.user.pk` only.

**System responses + error cases** (function contract):

| Trigger | Response | Side-effect |
|---------|----------|-------------|
| `validate_question(MCQ, "Cât face 2+2?", "What is 2+2?", [a,b,c], {"option_id":"b"})` | `[]` | none |
| Same call repeated (idempotent) | `[]` (pure, deterministic) | none |
| MCQ with 1 option | `[Violation("options_count", {"count": 1})]` | none |
| MCQ key `{"option_id": "z"}` | `[Violation("answer_key_invalid")]` | none |
| TF with options present | `[Violation("options_not_allowed")]` | none |
| NUMERIC key `{"value": "abc"}` | `[Violation("answer_key_invalid")]` | none |
| Blank `prompt_en` and invalid key | both violations, prompt first | none |
| `check_publishable([])` (empty) | `[questions_count{count:0}, positions_invalid, points_total_not_100{total:0}]` | none |
| 10 valid questions, points 10×10 | `[]` | none |
| 10 valid questions, Σ = 95 | `[points_total_not_100{total:95}]` | none |
| Question 4 has `points=0` | includes `points_below_minimum{position:4}` | none |
| `validate_chapter_number(2, {1, 2})` | `[chapter_number_taken{number:2}]` | none |
| `exercise_limit_violation(10)` | `Violation("exercises_limit", {"limit":10})` | none |
| `is_visible_to_learners("BLOCKED")` | `False` | none |

**Prerequisites**:
- CYCLE-1 complete (Story 1.10): `domain/common/errors.py` (`Violation`, `PolicyViolation`) from Story 1.1 and the import-linter contracts from 1.0.

**Context**: `docs/architecture/design/00-system-architecture-greenfield.md`, `docs/architecture/design/01-patterns-and-standards-greenfield.md`, `src/domain/common/errors.py`

**Patterns**: Domain Pattern (§4), Layering (§3), Strategy via lookup table (§15), Unit tests (§12.2), Coverage 100% domain (§12.6) — see `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Steps**:

1. **Unit tests first** for every row of the rule matrix and the response table (parametrised).

2. **Numbers:**
   ```python
   # src/domain/common/numbers.py
   from decimal import Decimal, InvalidOperation

   _SPACES = (" ", " ", " ")


   def parse_numeric(raw: str) -> Decimal | None:
       """'2', '2.0', '2,0' and ' 2.00 ' → Decimal('2'); None when unparseable or non-finite."""
       cleaned = raw.strip()
       for space in _SPACES:
           cleaned = cleaned.replace(space, "")
       if cleaned.count(",") == 1 and "." not in cleaned:
           cleaned = cleaned.replace(",", ".")  # Romanian decimal comma
       try:
           value = Decimal(cleaned)
       except InvalidOperation:
           return None
       return value if value.is_finite() else None


   def canonical_decimal(value: Decimal) -> str:
       """Stable storage form for answer keys: no exponent, no trailing zeros, no negative zero."""
       text = format(value.normalize(), "f")
       return "0" if text in {"-0", "0"} else text
   ```

3. **Questions** (lookup table per kind):
   ```python
   # src/domain/content/questions.py
   from collections.abc import Callable, Mapping, Sequence
   from dataclasses import dataclass, field
   from enum import StrEnum

   from domain.common.errors import Violation
   from domain.common.numbers import canonical_decimal, parse_numeric

   OPTION_IDS = ("a", "b", "c", "d", "e", "f")
   MIN_OPTIONS, MAX_OPTIONS = 2, 6


   class QuestionKind(StrEnum):
       MCQ = "MCQ"
       TRUE_FALSE = "TRUE_FALSE"
       NUMERIC = "NUMERIC"


   @dataclass(frozen=True)
   class Option:
       id: str
       ro: str
       en: str


   def _blank(text: str) -> bool:
       return not text or not text.strip()


   def _mcq(options: Sequence[Option], key: Mapping[str, object]) -> list[Violation]:
       found: list[Violation] = []
       ids = [o.id for o in options]
       if not MIN_OPTIONS <= len(options) <= MAX_OPTIONS or len(set(ids)) != len(ids) or set(ids) - set(OPTION_IDS):
           found.append(Violation("options_count", {"count": len(options)}))
       found += [Violation("option_text_missing", {"option": o.id}) for o in options if _blank(o.ro) or _blank(o.en)]
       if key.get("option_id") not in ids:
           found.append(Violation("answer_key_invalid"))
       return found


   def _true_false(options: Sequence[Option], key: Mapping[str, object]) -> list[Violation]:
       found = [Violation("options_not_allowed")] if options else []
       if not isinstance(key.get("value"), bool):
           found.append(Violation("answer_key_invalid"))
       return found


   def _numeric(options: Sequence[Option], key: Mapping[str, object]) -> list[Violation]:
       found = [Violation("options_not_allowed")] if options else []
       value = key.get("value")
       if not isinstance(value, str) or parse_numeric(value) is None:
           found.append(Violation("answer_key_invalid"))
       return found


   _KEY_RULES: Mapping[QuestionKind, Callable[[Sequence[Option], Mapping[str, object]], list[Violation]]] = {
       QuestionKind.MCQ: _mcq, QuestionKind.TRUE_FALSE: _true_false, QuestionKind.NUMERIC: _numeric,
   }


   def validate_question(kind: QuestionKind, prompt_ro: str, prompt_en: str,
                         options: Sequence[Option], answer_key: Mapping[str, object]) -> list[Violation]:
       found = []
       if _blank(prompt_ro):
           found.append(Violation("prompt_missing_ro"))
       if _blank(prompt_en):
           found.append(Violation("prompt_missing_en"))
       return found + _KEY_RULES[kind](options, answer_key)


   def numeric_answer_key(raw: str) -> dict[str, str] | None:
       value = parse_numeric(raw)
       return None if value is None else {"value": canonical_decimal(value)}


   @dataclass(frozen=True)
   class ExerciseDraft:
       kind: QuestionKind
       prompt_ro: str
       prompt_en: str
       options: tuple[Option, ...]
       answer_key: Mapping[str, object]
       explanation_ro: str
       explanation_en: str


   def validate_exercise(draft: ExerciseDraft) -> list[Violation]:
       found = validate_question(draft.kind, draft.prompt_ro, draft.prompt_en, draft.options, draft.answer_key)
       if _blank(draft.explanation_ro):
           found.append(Violation("explanation_missing_ro"))
       if _blank(draft.explanation_en):
           found.append(Violation("explanation_missing_en"))
       return found


   @dataclass(frozen=True)
   class QuestionDraft:
       position: int
       kind: QuestionKind
       prompt_ro: str
       prompt_en: str
       options: tuple[Option, ...]
       answer_key: Mapping[str, object]
       points: int
       extra: Mapping[str, object] = field(default_factory=dict)
   ```

4. **Publication and chapters:**
   ```python
   # src/domain/content/publication.py
   from collections.abc import Sequence

   from domain.common.errors import Violation
   from domain.content.questions import QuestionDraft, validate_question

   QUESTIONS_PER_TEST, TOTAL_POINTS, MIN_POINTS = 10, 100, 1


   def check_publishable(questions: Sequence[QuestionDraft]) -> list[Violation]:
       """Every reason a chapter test cannot be published; empty list = publishable."""
       found: list[Violation] = []
       if len(questions) != QUESTIONS_PER_TEST:
           found.append(Violation("questions_count", {"count": len(questions)}))
       if sorted(q.position for q in questions) != list(range(1, QUESTIONS_PER_TEST + 1)):
           found.append(Violation("positions_invalid"))
       for q in sorted(questions, key=lambda item: item.position):
           if q.points < MIN_POINTS:
               found.append(Violation("points_below_minimum", {"position": q.position}))
           found += [Violation(v.code, {**v.params, "position": q.position})
                     for v in validate_question(q.kind, q.prompt_ro, q.prompt_en, q.options, q.answer_key)]
       total = sum(q.points for q in questions)
       if total != TOTAL_POINTS:
           found.append(Violation("points_total_not_100", {"total": total}))
       return found
   ```
   `chapters.py` implements AC 7 with the three constants.

5. **Ports** (the contract consumed by Stories 3.5–3.8; `at` is an aware `datetime` from `Clock`):
   ```python
   # src/domain/content/ports.py
   from collections.abc import Collection, Sequence
   from datetime import datetime
   from typing import Protocol

   from domain.content.questions import ExerciseDraft, QuestionDraft


   class ChapterRepository(Protocol):
       def subject_is_active(self, subject_id: int) -> bool: ...
       def subject_of(self, chapter_id: int) -> int | None: ...
       def numbers_taken(self, subject_id: int, excluding_chapter_id: int | None = None) -> Collection[int]: ...
       def add(self, subject_id: int, number: int, title_ro: str, title_en: str, actor_id: int, at: datetime) -> int: ...
       def update(self, chapter_id: int, number: int, title_ro: str, title_en: str, actor_id: int, at: datetime) -> None: ...


   class LessonRepository(Protocol):
       def chapter_exists(self, chapter_id: int) -> bool: ...
       def upsert(self, chapter_id: int, body_ro: str, body_en: str, actor_id: int, at: datetime) -> int: ...


   class ExerciseRepository(Protocol):
       def chapter_exists(self, chapter_id: int) -> bool: ...
       def count(self, chapter_id: int) -> int: ...
       def chapter_of(self, exercise_id: int) -> int | None: ...
       def add(self, chapter_id: int, draft: ExerciseDraft, actor_id: int, at: datetime) -> int: ...
       def update(self, exercise_id: int, draft: ExerciseDraft, actor_id: int, at: datetime) -> None: ...
       def remove(self, exercise_id: int) -> bool: ...  # renumbers remaining positions 1..n


   class ChapterTestRepository(Protocol):
       def chapter_exists(self, chapter_id: int) -> bool: ...
       def draft_or_existing(self, chapter_id: int, actor_id: int, at: datetime) -> int: ...
       def status(self, test_id: int) -> str | None: ...
       def load_questions(self, test_id: int) -> Sequence[QuestionDraft]: ...
       def replace_questions(self, test_id: int, questions: Sequence[QuestionDraft], actor_id: int, at: datetime) -> None: ...
       def mark_published(self, test_id: int, at: datetime) -> None: ...
   ```

6. **Moderation status** (`domain/moderation/status.py`) per AC 8; `application/content/__init__.py` (empty).

7. **Run gates:** `mypy --strict`, `lint-imports`, and coverage 100% for the three domain areas.

**Tests**:

```python
# tests/unit/domain/common/test_numbers.py
from decimal import Decimal

import pytest

from domain.common.numbers import canonical_decimal, parse_numeric


@pytest.mark.parametrize("raw", ["2", "2.0", "2,0", " 2.00 ", "2 ", " 2"])
def test_formatting_variants_parse_to_same_value(raw):
    assert parse_numeric(raw) == Decimal("2")


@pytest.mark.parametrize("raw", ["", "abc", "2,5,1", "2.5,1", "NaN", "Infinity", "-Infinity"])
def test_unparseable_values_return_none(raw):
    assert parse_numeric(raw) is None


@pytest.mark.parametrize(("value", "text"), [
    (Decimal("2.50"), "2.5"), (Decimal("1E+2"), "100"), (Decimal("-0.0"), "0"), (Decimal("0.001"), "0.001"),
])
def test_canonical_decimal(value, text):
    assert canonical_decimal(value) == text
```

```python
# tests/unit/domain/content/test_questions.py
import pytest

from domain.content.questions import (
    ExerciseDraft, Option, QuestionKind, numeric_answer_key, validate_exercise, validate_question)

ABC = (Option("a", "unu", "one"), Option("b", "doi", "two"), Option("c", "trei", "three"))


def codes(violations):
    return [v.code for v in violations]


def test_valid_mcq_has_no_violations():
    assert validate_question(QuestionKind.MCQ, "Cât?", "How many?", ABC, {"option_id": "b"}) == []


@pytest.mark.parametrize(("options", "expected"), [
    (ABC[:1], ["options_count"]),
    (ABC + (Option("d", "x", "x"), Option("e", "x", "x"), Option("f", "x", "x"), Option("a", "x", "x")), ["options_count"]),
    ((Option("a", "unu", ""), Option("b", "doi", "two")), ["option_text_missing"]),
    ((Option("z", "x", "x"), Option("b", "y", "y")), ["options_count"]),
])
def test_mcq_option_rules(options, expected):
    assert codes(validate_question(QuestionKind.MCQ, "p", "p", options, {"option_id": "b"})) == expected


def test_mcq_key_must_reference_an_option():
    assert codes(validate_question(QuestionKind.MCQ, "p", "p", ABC, {"option_id": "z"})) == ["answer_key_invalid"]


@pytest.mark.parametrize(("key", "expected"), [({"value": True}, []), ({"value": "true"}, ["answer_key_invalid"]), ({}, ["answer_key_invalid"])])
def test_true_false_key(key, expected):
    assert codes(validate_question(QuestionKind.TRUE_FALSE, "p", "p", (), key)) == expected


def test_true_false_rejects_options():
    assert "options_not_allowed" in codes(validate_question(QuestionKind.TRUE_FALSE, "p", "p", ABC, {"value": True}))


@pytest.mark.parametrize(("key", "expected"), [({"value": "2.5"}, []), ({"value": "abc"}, ["answer_key_invalid"]), ({"value": 3}, ["answer_key_invalid"])])
def test_numeric_key(key, expected):
    assert codes(validate_question(QuestionKind.NUMERIC, "p", "p", (), key)) == expected


def test_all_violations_are_reported_in_order():
    found = validate_question(QuestionKind.MCQ, " ", "", ABC[:1], {"option_id": "z"})

    assert codes(found) == ["prompt_missing_ro", "prompt_missing_en", "options_count", "answer_key_invalid"]


def test_numeric_answer_key_is_canonical():
    assert numeric_answer_key("2,50") == {"value": "2.5"}
    assert numeric_answer_key("two") is None


def test_exercise_requires_bilingual_explanation():
    draft = ExerciseDraft(QuestionKind.TRUE_FALSE, "p", "p", (), {"value": False}, "Pentru că…", "")

    assert codes(validate_exercise(draft)) == ["explanation_missing_en"]
```

```python
# tests/unit/domain/content/test_publication.py
from domain.content.publication import check_publishable
from domain.content.questions import QuestionDraft, QuestionKind


def q(position, points=10, key=True):
    return QuestionDraft(position, QuestionKind.TRUE_FALSE, "ro", "en", (), {"value": key}, points)


def codes(violations):
    return [(v.code, dict(v.params)) for v in violations]


def test_ten_questions_totalling_100_are_publishable():
    assert check_publishable([q(i) for i in range(1, 11)]) == []


def test_total_not_100_is_reported_with_total():
    questions = [q(i) for i in range(1, 10)] + [q(10, points=5)]

    assert codes(check_publishable(questions)) == [("points_total_not_100", {"total": 95})]


def test_every_problem_is_reported_with_position():
    questions = [q(i) for i in range(1, 10)] + [QuestionDraft(10, QuestionKind.NUMERIC, "", "en", (), {"value": "x"}, 0)]

    assert codes(check_publishable(questions)) == [
        ("points_below_minimum", {"position": 10}),
        ("prompt_missing_ro", {"position": 10}),
        ("answer_key_invalid", {"position": 10}),
        ("points_total_not_100", {"total": 90}),
    ]


def test_empty_test_reports_count_positions_and_total():
    assert [c for c, _ in codes(check_publishable([]))] == ["questions_count", "positions_invalid", "points_total_not_100"]


def test_duplicate_positions_are_invalid():
    questions = [q(i) for i in range(1, 10)] + [q(9)]

    assert "positions_invalid" in [c for c, _ in codes(check_publishable(questions))]
```

```python
# tests/unit/domain/content/test_chapters.py and tests/unit/domain/moderation/test_status.py
import pytest

from domain.content.chapters import exercise_limit_violation, validate_chapter_number
from domain.moderation.status import ModerationStatus, is_visible_to_learners


@pytest.mark.parametrize(("number", "taken", "expected"), [
    (1, set(), []), (3, {1, 2}, []), (0, set(), ["chapter_number_out_of_range"]),
    (4, set(), ["chapter_number_out_of_range"]), (2, {2}, ["chapter_number_taken"]),
])
def test_chapter_numbers(number, taken, expected):
    assert [v.code for v in validate_chapter_number(number, taken)] == expected


@pytest.mark.parametrize(("lesson", "exercises", "test", "questions", "ready"), [
    (True, 5, True, 10, True), (True, 10, True, 10, True), (False, 5, True, 10, False), (True, 4, True, 10, False),
    (True, 11, True, 10, False), (True, 5, False, 10, False), (True, 5, True, 9, False),
])
def test_chapter_readiness(lesson, exercises, test, questions, ready):
    from domain.content.chapters import chapter_is_ready

    assert chapter_is_ready(lesson, exercises, test, questions) is ready


@pytest.mark.parametrize(("count", "blocked"), [(0, False), (9, False), (10, True), (11, True)])
def test_exercise_limit(count, blocked):
    assert (exercise_limit_violation(count) is not None) is blocked


@pytest.mark.parametrize(("status", "visible"), [("ACTIVE", True), ("FLAGGED", False), ("BLOCKED", False),
                                                 ("RESUBMITTED", False), (ModerationStatus.ACTIVE, True)])
def test_only_active_is_visible(status, visible):
    assert is_visible_to_learners(status) is visible
```

Manual: none (no runtime surface). Reviewers check that the rule matrix matches the requirements and the architecture's answer-key table.

**Quality**: ruff 0; `mypy --strict` for `domain.*`; `lint-imports` kept (stdlib only); 100% statement + branch coverage for the three domain areas; no `TODO`.

**OUT**:
- ❌ Persistence models and repositories (Story 3.2 and 3.5–3.8).
- ❌ Answer *checking* and scoring of student responses (CYCLE-3, Epic 6, reusing `parse_numeric`).
- ❌ Moderation transitions/state machine (CYCLE-3, Epic 8); only the status enum + visibility rule here.
- ❌ Scoring lock after attempts (CYCLE-3).
- ❌ Any web form or message translation (Story 3.4 maps violation codes to messages).

**Evidence**: pytest output, 100% coverage report for `src/domain/common/numbers.py`, `src/domain/content`, `src/domain/moderation`, plus `mypy --strict` and `lint-imports` output, all recorded in `docs/stories-implemented/story-3.1-review.md` under "## DoD Evidence".
