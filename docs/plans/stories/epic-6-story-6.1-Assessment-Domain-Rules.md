### Story 6.1: Assessment Domain Rules

**BUILDID**: CYCLE-3 | **GitHub**: LOCAL | **AzureDevOps**: LOCAL | **Epic**: 6 - Chapter Tests & Scoring | **ID**: 6.1 | **Date**: 2026-10-19
**File**: `docs/plans/stories/epic-6-story-6.1-Assessment-Domain-Rules.md`
**Build Ref**: `docs/plans/builds/cycle-3/cycle-plan.md` — CYCLE-3 (Workshop Day 1: answer checking + scoring at 100% domain coverage; scoring lock)
**Wave**: 10
**Requires**: [3.9, 4.4]
**Enables**: [6.3, 6.5]
**Files Touched**:
  - src/domain/assessment/**
  - src/domain/content/scoring_lock.py
  - src/application/assessment/__init__.py
  - tests/unit/domain/assessment/**
  - tests/unit/domain/content/test_scoring_lock.py
**Roles Ref**: docs/requirements.md#roles--permissions-matrix — single-actor — no role variation (pure scoring and locking rules; callers enforce roles)
**QA Candidate**: No — pure domain library with no route, verified by unit tests at 100% coverage. Its behaviour is user-observable through Stories 6.3–6.5, where QA checks scores and the lock.

---

#### 👤 User Reference

**Description**:
This story writes the exact scoring rules from the requirements as checkable code.

**Marking each answer** (by question type):
- **Multiple choice:** correct only if the chosen option is the right one.
- **True/false:** correct only if the student picked the right value.
- **Number:** compared by value, so "2", "2.0", "2,0" and " 2.00 " all match a correct answer of 2. Text that isn't a number is simply marked wrong, never an error.
- **Unanswered:** an unanswered question is wrong.

**The score:** the sum of the points of the correctly answered questions. Because the teacher's points always total 100, the score is between 0 and 100, except that a test with nothing right is reported as **1, not 0**, exactly as the requirements say.

**The scoring lock:** once any student has taken a test, its marking must never change, or students would be scored differently. After the first attempt, teachers can't change:
- which answers are correct
- the points
- the question types
- the set of questions (adding or removing)

They can still fix typos in the question wording or option texts. This story defines that rule; Story 6.5 applies it in the test editor.

**Acceptance Criteria** (plain-English):
- Multiple-choice answers are correct only when the chosen option matches the correct one.
- True/false answers are correct only when they match the correct value.
- Number answers are compared by value; formatting differences (comma or dot, trailing zeros, spaces) don't matter; non-numbers are wrong.
- Unanswered questions are wrong.
- The score is the total of points for correct answers; all-wrong gives 1, all-right gives 100.
- After the first attempt, changes to correct answers, points, question types or the set of questions are refused, naming each question concerned; wording changes are allowed.

**User Flow**:
Actor: system — no role variation.

**Flow Diagram** (rule matrix):

| Kind | Answer key | Response | `is_correct` |
|------|-----------|----------|--------------|
| MCQ | `{"option_id": "b"}` | `"b"` | True |
| MCQ | `{"option_id": "b"}` | `"a"` / `""` / `"z"` | False |
| TRUE_FALSE | `{"value": true}` | `"true"` | True |
| TRUE_FALSE | `{"value": true}` | `"false"` / `""` / `"yes"` | False |
| NUMERIC | `{"value": "2"}` | `"2"`, `"2.0"`, `"2,0"`, `" 2.00 "` | True |
| NUMERIC | `{"value": "2.5"}` | `"2,50"` | True |
| NUMERIC | `{"value": "2"}` | `"doi"` / `""` / `"NaN"` | False |

| Scoring input | `earned_points` | `score` |
|---------------|-----------------|---------|
| all 10 wrong (10 pts each) | 0 | **1** |
| 40 + 25 correct | 65 | 65 |
| all correct | 100 | 100 |

| Lock comparison (after first attempt) | Result |
|---------------------------------------|--------|
| prompt or option text changed | allowed |
| `answer_key` changed at position n | `scoring_locked` {position: n} |
| `points` changed at position n | `scoring_locked` {position: n} |
| `kind` changed at position n | `scoring_locked` {position: n} |
| option ids changed (added/removed option) at position n | `scoring_locked` {position: n} |
| question added/removed (positions differ) | `scoring_locked_question_set` |

---

#### 🤖 AI Agent Reference

**Must Read**:
- `docs/requirements.md` — Feature "Chapter tests"
- `docs/architecture/design/00-system-architecture-greenfield.md` — Key Domain Logic (AnswerChecker / TestScorer), Integrity rules ("Scoring lock"), ADR-009
- `docs/architecture/design/01-patterns-and-standards-greenfield.md` — §4 (scoring reference code, Strategy lookup table §15), §12.2 tests
- `docs/plans/stories/epic-3-story-3.1-Content-Domain-Rules.md` — `parse_numeric` (in `domain/common/numbers.py`), `QuestionKind`, `QuestionDraft`

**Description**:
1. **`domain/assessment/answer_checker.py`:** `is_correct(kind, answer_key, response_raw) -> bool` via a lookup table of three checkers. NUMERIC uses `domain.common.numbers.parse_numeric` on both sides.
2. **`domain/assessment/scoring.py`:** `QuestionResult`, `TestScore`, `MIN_SCORE = 1`, `compute_score(results)` (patterns §4 reference code).
3. **`domain/assessment/errors.py`:** `AlreadySubmitted(ConflictError)` with code `test_already_submitted`, raised by the use case and repository in 6.3.
4. **`domain/assessment/ports.py`:**
   - `TestQuestionKey(id, position, kind, answer_key, points)` and `VisibleTest(test_id, chapter_id, questions)`
   - Protocols `LearnerTestRepository.get_visible(test_id) -> VisibleTest | None` and `AttemptRepository` (`exists`, `add`)
5. **`domain/content/scoring_lock.py`:** `scoring_changes(stored, submitted) -> list[Violation]` comparing `QuestionDraft` sequences.
6. **`application/assessment/__init__.py`:** empty package for 6.3.

**Acceptance Criteria**:
1. `is_correct` implements the rule matrix exactly. It never raises for any string response (malformed key → False). It's covered at 100% branches.
2. `compute_score` returns `TestScore(earned_points, score=max(MIN_SCORE, earned))`. The function doesn't enforce Σ = 100 (publication already guarantees it).
3. `AlreadySubmitted.code == "test_already_submitted"` and it subclasses `ConflictError` (→ 409 via Story 1.1's middleware).
4. `scoring_changes(stored, submitted)`:
   - returns `[]` when only prompts or option *texts* differ
   - per position, a `Violation("scoring_locked", {"position": n})` when `kind`, `answer_key`, `points` or the option-id tuple differ
   - `Violation("scoring_locked_question_set")` when the position sets differ (and per-position checks are skipped for positions not in both)
   - order: question-set violation first, then positions ascending
5. Ports as in Step 4. `TestQuestionKey` has no prompt fields; scoring never needs text.
6. Pure stdlib + `domain.*` (import-linter kept); `mypy --strict`; 100% coverage of `domain/assessment/**` and `scoring_lock.py`.

**RBAC Enforcement**:
No role-differentiated access — single actor.
- Pure rules. Student identity and permissions are enforced by `SubmitTest` callers (6.3/6.4); the lock is applied by the teacher-only editor (6.5).

**System responses + error cases** (function contract):

| Trigger | Response | Side-effect |
|---------|----------|-------------|
| `is_correct(NUMERIC, {"value":"2"}, "2,0")` | `True` | none |
| Same call repeated (idempotent) | `True` | none |
| `is_correct(NUMERIC, {"value":"2"}, "doi")` | `False` | none |
| `is_correct(NUMERIC, {}, "2")` (malformed key) | `False` | none |
| `is_correct(TRUE_FALSE, {"value": False}, "false")` | `True` | none |
| `compute_score([])` | `TestScore(0, 1)` | none |
| `compute_score` all correct (Σ 100) | `TestScore(100, 100)` | none |
| `scoring_changes(q, q_with_new_prompt)` | `[]` | none |
| `scoring_changes(q, q_with_points_changed_at_4)` | `[scoring_locked{position:4}]` | none |
| `scoring_changes(10 questions, 9 questions)` | `[scoring_locked_question_set]` | none |

**Prerequisites**:
- CYCLE-2 complete (Stories 3.9, 4.4), with `parse_numeric`, `QuestionKind` and `QuestionDraft` from Story 3.1.

**Context**: `docs/architecture/design/01-patterns-and-standards-greenfield.md`, `src/domain/common/numbers.py`, `src/domain/content/questions.py`, `src/domain/common/errors.py`

**Patterns**: Domain pattern (§4), Strategy lookup table (§15), Unit tests + 100% domain coverage (§12.2, §12.6) — see `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Steps**:

1. **Tests first** (parametrised over both matrices).

2. **Answer checker:**
   ```python
   # src/domain/assessment/answer_checker.py
   from collections.abc import Callable, Mapping

   from domain.common.numbers import parse_numeric
   from domain.content.questions import QuestionKind

   Checker = Callable[[Mapping[str, object], str], bool]


   def _choice(key: Mapping[str, object], response: str) -> bool:
       return bool(response) and response == key.get("option_id")


   def _true_false(key: Mapping[str, object], response: str) -> bool:
       value = key.get("value")
       return isinstance(value, bool) and response in {"true", "false"} and (response == "true") == value


   def _numeric(key: Mapping[str, object], response: str) -> bool:
       expected = key.get("value")
       if not isinstance(expected, str):
           return False
       given, wanted = parse_numeric(response), parse_numeric(expected)
       return given is not None and wanted is not None and given == wanted


   _CHECKERS: Mapping[QuestionKind, Checker] = {
       QuestionKind.MCQ: _choice, QuestionKind.TRUE_FALSE: _true_false, QuestionKind.NUMERIC: _numeric,
   }


   def is_correct(kind: QuestionKind, answer_key: Mapping[str, object], response_raw: str) -> bool:
       """Missing or malformed answers are simply incorrect — never an error after submission."""
       return _CHECKERS[kind](answer_key, (response_raw or "").strip())
   ```

3. **Scoring** (`scoring.py`) exactly as patterns §4. **Errors** (`errors.py`): `AlreadySubmitted`.

4. **Ports:**
   ```python
   # src/domain/assessment/ports.py
   from collections.abc import Mapping, Sequence
   from dataclasses import dataclass
   from datetime import datetime
   from typing import Protocol

   from domain.assessment.scoring import QuestionResult, TestScore
   from domain.content.questions import QuestionKind


   @dataclass(frozen=True)
   class TestQuestionKey:
       id: int
       position: int
       kind: QuestionKind
       answer_key: Mapping[str, object]
       points: int


   @dataclass(frozen=True)
   class VisibleTest:
       test_id: int
       chapter_id: int
       questions: tuple[TestQuestionKey, ...]


   class LearnerTestRepository(Protocol):
       def get_visible(self, test_id: int) -> VisibleTest | None: ...  # PUBLISHED + ACTIVE, active subject


   class AttemptRepository(Protocol):
       def exists(self, student_id: int, test_id: int) -> bool: ...
       def add(self, student_id: int, test_id: int, results: Sequence[QuestionResult],
               responses: Mapping[int, str], score: TestScore, at: datetime) -> int: ...  # raises AlreadySubmitted
   ```

5. **Scoring lock:**
   ```python
   # src/domain/content/scoring_lock.py
   from collections.abc import Sequence

   from domain.common.errors import Violation
   from domain.content.questions import QuestionDraft


   def _scoring_signature(q: QuestionDraft) -> tuple[object, ...]:
       return q.kind, tuple(sorted(q.answer_key.items())), q.points, tuple(o.id for o in q.options)


   def scoring_changes(stored: Sequence[QuestionDraft], submitted: Sequence[QuestionDraft]) -> list[Violation]:
       """After the first attempt only wording may change (architecture: Scoring lock)."""
       before = {q.position: q for q in stored}
       after = {q.position: q for q in submitted}
       found = [] if set(before) == set(after) else [Violation("scoring_locked_question_set")]
       found += [Violation("scoring_locked", {"position": p}) for p in sorted(set(before) & set(after))
                 if _scoring_signature(before[p]) != _scoring_signature(after[p])]
       return found
   ```

6. **Run gates** (`mypy --strict`, import-linter, coverage 100%).

**Tests**:

```python
# tests/unit/domain/assessment/test_answer_checker.py
import pytest

from domain.assessment.answer_checker import is_correct
from domain.content.questions import QuestionKind as K


@pytest.mark.parametrize(("kind", "key", "response", "expected"), [
    (K.MCQ, {"option_id": "b"}, "b", True), (K.MCQ, {"option_id": "b"}, "a", False),
    (K.MCQ, {"option_id": "b"}, "", False), (K.MCQ, {}, "", False),
    (K.TRUE_FALSE, {"value": True}, "true", True), (K.TRUE_FALSE, {"value": True}, "false", False),
    (K.TRUE_FALSE, {"value": False}, "false", True), (K.TRUE_FALSE, {"value": True}, "yes", False),
    (K.TRUE_FALSE, {"value": "true"}, "true", False),
    (K.NUMERIC, {"value": "2"}, "2", True), (K.NUMERIC, {"value": "2"}, "2.0", True),
    (K.NUMERIC, {"value": "2"}, "2,0", True), (K.NUMERIC, {"value": "2"}, " 2.00 ", True),
    (K.NUMERIC, {"value": "2.5"}, "2,50", True), (K.NUMERIC, {"value": "2"}, "doi", False),
    (K.NUMERIC, {"value": "2"}, "", False), (K.NUMERIC, {"value": "2"}, "NaN", False),
    (K.NUMERIC, {}, "2", False), (K.NUMERIC, {"value": "x"}, "x", False),
])
def test_is_correct(kind, key, response, expected):
    assert is_correct(kind, key, response) is expected
```

```python
# tests/unit/domain/assessment/test_scoring.py
from domain.assessment.scoring import QuestionResult, compute_score


def test_all_incorrect_scores_one_not_zero():
    score = compute_score([QuestionResult(i, 10, False) for i in range(10)])

    assert (score.earned_points, score.score) == (0, 1)


def test_score_is_sum_of_correct_weights():
    results = [QuestionResult(1, 40, True), QuestionResult(2, 35, False), QuestionResult(3, 25, True)]

    assert compute_score(results).score == 65


def test_perfect_test_scores_100():
    assert compute_score([QuestionResult(i, 10, True) for i in range(10)]).score == 100


def test_empty_results_score_one():
    assert compute_score([]).score == 1
```

```python
# tests/unit/domain/content/test_scoring_lock.py
from dataclasses import replace

from domain.content.questions import Option, QuestionDraft, QuestionKind
from domain.content.scoring_lock import scoring_changes

BASE = [QuestionDraft(p, QuestionKind.MCQ, "ro", "en", (Option("a", "1", "1"), Option("b", "2", "2")),
                      {"option_id": "b"}, 10) for p in range(1, 11)]


def codes(found):
    return [(v.code, dict(v.params)) for v in found]


def test_wording_changes_are_allowed():
    edited = [replace(q, prompt_en="Fixed typo", options=(Option("a", "unu", "one"), Option("b", "doi", "two")))
              for q in BASE]

    assert scoring_changes(BASE, edited) == []


def test_points_key_kind_and_option_ids_are_locked_per_position():
    edited = list(BASE)
    edited[3] = replace(BASE[3], points=15)
    edited[5] = replace(BASE[5], answer_key={"option_id": "a"})
    edited[6] = replace(BASE[6], kind=QuestionKind.TRUE_FALSE)
    edited[7] = replace(BASE[7], options=BASE[7].options + (Option("c", "3", "3"),))

    assert codes(scoring_changes(BASE, edited)) == [
        ("scoring_locked", {"position": 4}), ("scoring_locked", {"position": 6}),
        ("scoring_locked", {"position": 7}), ("scoring_locked", {"position": 8})]


def test_question_set_change_is_locked():
    assert codes(scoring_changes(BASE, BASE[:9])) == [("scoring_locked_question_set", {})]
```

Manual: none (no runtime surface).

**Quality**: ruff 0; `mypy --strict`; lint-imports kept; 100% coverage for `domain/assessment/**` and `domain/content/scoring_lock.py`; no `TODO`.

**OUT**:
- ❌ Persisting attempts (6.2) and the submission use case (6.3).
- ❌ Student/teacher UI (6.4, 6.5).
- ❌ Partial credit, negative marking or per-question feedback to students (not required: final score only).

**Evidence**: pytest output, 100% coverage report for the listed domain modules, and `mypy --strict` + lint-imports output, all recorded in `docs/stories-implemented/story-6.1-review.md` under "## DoD Evidence".
