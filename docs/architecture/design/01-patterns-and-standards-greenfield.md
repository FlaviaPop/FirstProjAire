# Patterns & Standards - Romanian Curriculum Learning Platform (Working Title)

**Date**: 2026-10-19
**Author**: ARCHITECT
**Status**: Approved
**Version**: 1.0
**Inputs**: `docs/requirements.md` v1.0 (Approved) · `docs/architecture/design/00-system-architecture-greenfield.md` v1.0 (Approved)

> This document says **how** DEV writes code in this project. Every story lists it as a required context file. When a story and this document disagree, stop and ask the Architect. Don't pick one quietly.
>
> Notation: **✅ DO** / **❌ DON'T**. "MUST" rules are checked in review and, where possible, by tooling (ruff, mypy, import-linter, pytest).

---

## 1. Project Structure

### 1.1 Folder layout

```
.
├── pyproject.toml                    # deps, ruff, mypy, pytest, coverage, import-linter config
├── uv.lock                           # locked dependency versions (committed)
├── .env.example                      # every env var, with safe dev defaults / placeholders
├── Dockerfile · docker-entrypoint.sh # added by Story 1.1 / DevOps
├── manage.py
├── src/
│   ├── config/                       # Django project
│   │   ├── settings/  base.py · dev.py · test.py · prod.py
│   │   ├── urls.py                   # root URLConf: i18n_patterns + includes per context
│   │   └── wsgi.py
│   ├── domain/                       # PURE PYTHON — stdlib only
│   │   ├── common/        errors.py · language.py · clock.py
│   │   ├── accounts/      roles.py · permissions.py · access_policy.py · ports.py
│   │   ├── content/       questions.py · publication.py · scoring_lock.py · ports.py
│   │   ├── moderation/    status.py · state_machine.py · ports.py
│   │   ├── assessment/    answer_checker.py · scoring.py · ports.py
│   │   └── progress/      ports.py
│   ├── application/                  # use cases; imports domain only
│   │   ├── common/        unit_of_work.py · audit.py
│   │   ├── accounts/      link_parent.py · …
│   │   ├── content/       save_lesson.py · save_exercise.py · save_test.py · publish_test.py
│   │   ├── moderation/    flag_content.py · approve_content.py · block_content.py · resubmit_content.py · clear_block.py
│   │   ├── assessment/    submit_test.py
│   │   └── progress/      record_lesson_view.py · finish_exercise.py
│   └── infrastructure/
│       ├── persistence/              # Django apps (app_label = context name)
│       │   ├── accounts/  models.py · repositories.py · queries.py · admin.py · migrations/
│       │   ├── catalogue/ …          ├── content/ …       ├── assessment/ …
│       │   ├── progress/ …           ├── notifications/ … └── audit/ …
│       │   └── common/    unit_of_work.py · managers.py
│       ├── web/
│       │   ├── common/    decorators.py · middleware.py · htmx.py · i18n.py · errors.py
│       │   ├── <context>/ views.py · urls.py · forms.py      # one package per context
│       │   ├── templatetags/ ui.py · i18n_content.py
│       │   ├── templates/ layouts/ · components/ · <context>/ · errors/
│       │   ├── static/    css/tokens.css · css/components/ · css/<context>.css · js/htmx.min.js
│       │   └── styleguide/ views.py · urls.py                  # DEBUG-only primitive catalogue
│       ├── rendering/     markdown.py
│       ├── logging/       json_formatter.py · request_id.py
│       ├── i18n/locale/   ro/LC_MESSAGES/django.po · en/LC_MESSAGES/django.po
│       └── container.py   # composition root
└── tests/
    ├── conftest.py                   # global fixtures (role users, clients, clock)
    ├── fakes/                        # in-memory port implementations
    ├── factories/                    # factory_boy factories, one module per context
    ├── unit/          domain/<context>/ · application/<context>/
    ├── integration/   web/<context>/ · persistence/<context>/
    └── e2e/           test_<role>_journey.py
```

> **Refinement of architecture §Source layout:** domain ports live **per context** (`domain/<context>/ports.py`) rather than in one `domain/ports.py`. This removes a file every story would otherwise edit (see §16 Boundary Map). There is no change in behaviour.

### 1.2 Naming conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Packages / modules | `snake_case`, singular concept | `answer_checker.py`, `state_machine.py` |
| Classes | `PascalCase`, noun | `ModerationStateMachine`, `SubmitTest` |
| Use cases | imperative verb + noun class, `execute()` method | `BlockContent.execute(cmd)` |
| Commands / DTOs | `<UseCase>Command`, `<Thing>DTO` (frozen dataclasses) | `SubmitTestCommand`, `ChildProgressDTO` |
| Ports (Protocols) | `<Thing>Repository`, `<Thing>Port` | `AttemptRepository`, `NotifierPort` |
| ORM models | `<Entity>Model` in persistence only | `TestAttemptModel` (`db_table="assessment_test_attempt"`) |
| Repository implementations | `Django<Port>` | `DjangoAttemptRepository` |
| Functions | `verb_noun`, `snake_case` | `compute_score`, `parse_numeric` |
| Booleans | `is_/has_/can_` prefix | `is_correct`, `has_attempts` |
| Constants | `UPPER_SNAKE` | `MIN_SCORE`, `ROLE_PERMISSIONS` |
| Enums | `StrEnum`, member names `UPPER_SNAKE`, values as persisted | `ModerationStatus.ACTIVE = "ACTIVE"` |
| URL names | `<context>:<action>` | `assessment:submit`, `moderation:block` |
| Templates | `<context>/<page>.html`; partials `<context>/_<partial>.html`; primitives `components/<name>.html` | `assessment/_result.html` |
| Bilingual fields | `<field>_ro`, `<field>_en` | `title_ro`, `body_en` |
| Tests | `test_<behaviour>_when_<condition>` | `test_score_is_one_when_all_answers_incorrect` |

### 1.3 Dependency management

- **Tool:** `uv`. Runtime dependencies go in `[project.dependencies]` and dev tools in `[dependency-groups].dev`. `uv.lock` is committed, and CI runs `uv sync --frozen`.
- **Version policy:** declare compatible ranges in `pyproject.toml`. The lock file pins exact versions. Adding a dependency requires a one-line justification in the story review doc. Prefer the standard library or Django built-ins.

| Package | Range | Purpose |
|---------|-------|---------|
| `django` | `>=5.2,<5.3` | framework (LTS) |
| `argon2-cffi` | `>=23.1` | Argon2id hasher |
| `django-axes` | `>=7.0` | login lockout |
| `django-csp` | `>=4.0` | CSP header |
| `markdown` | `>=3.7` | lesson Markdown |
| `nh3` | `>=0.2.18` | HTML sanitizer |
| `gunicorn` | `>=23.0` | WSGI server |
| `whitenoise` | `>=6.7` | static files |
| dev: `pytest`, `pytest-django`, `pytest-cov`, `factory-boy`, `pytest-playwright`, `ruff`, `mypy`, `django-stubs`, `import-linter` | latest at Story 1.1 | test & quality tooling |

❌ DON'T add `django-environ`, `django-rest-framework`, Celery, Redis, a JS bundler or any CDN asset. ADR-003/004 make them unnecessary.

---

## 2. Code Structure & Formatting

| Rule | Standard | Enforced by |
|------|----------|-------------|
| Formatter | `ruff format`, line length **100** | CI |
| Linter | `ruff check` with rule sets `E,F,W,I,B,UP,SIM,N,S,DJ,PT,RUF,C90` · max complexity 8 | CI, 0 warnings |
| Import order | stdlib → third-party → first-party (`config`, `domain`, `application`, `infrastructure`) via ruff `I` | CI |
| Imports | absolute only; ❌ no `from x import *` | ruff |
| Type hints | required on all public functions. `mypy --strict` for `src/domain` and `src/application`; `django-stubs` for infrastructure | CI |
| Function size | ≤ 30 lines, ≤ 4 parameters (DI constructors are exempt) | review, ruff `C90` |
| File size | target ≤ 300 lines; **hard limit 400**. Split by responsibility before reaching it. | review |
| Class organisation | constants → `__init__` → public methods → private helpers (`_name`) | review |
| Comments | explain **why**, not what; no commented-out code; no `TODO`/`FIXME` | review, `ruff FIX` |

✅ DO keep one public concept per module (`scoring.py` holds scoring).
❌ DON'T create `utils.py` / `helpers.py` grab-bags. Name the module after its responsibility.

---

## 3. Layering Rules (Clean Architecture)

| Layer | May import | MUST NOT import |
|-------|-----------|-----------------|
| `domain` | stdlib only | `django`, `application`, `infrastructure`, any third-party package |
| `application` | `domain`, stdlib | `django`, `infrastructure` |
| `infrastructure` | everything | — |
| `config` | `infrastructure` (settings/urls) | `domain` logic directly |

Enforced by **import-linter** in `pyproject.toml`:

```toml
[tool.importlinter]
root_packages = ["domain", "application", "infrastructure", "config"]

[[tool.importlinter.contracts]]
name = "Layers point inward"
type = "layers"
layers = ["config", "infrastructure", "application", "domain"]

[[tool.importlinter.contracts]]
name = "Domain is framework-free"
type = "forbidden"
source_modules = ["domain", "application"]
forbidden_modules = ["django", "markdown", "nh3"]
```

✅ DO route every **write** through a use case: view → use case → ports.
✅ DO let read-only pages call a **query service** in `infrastructure/persistence/<ctx>/queries.py` (CQRS-lite, ADR-005).
❌ DON'T call `Model.objects.create/update/delete` from a view, form, template tag or signal.
❌ DON'T put business rules in views, forms, models or templates. They belong in `domain`.

---

## 4. Domain Pattern

Entities and value objects are **frozen dataclasses** or `StrEnum`s. Rules are pure functions or small stateless classes. Domain errors carry a stable `code` that the web layer translates.

```python
# src/domain/common/errors.py
class DomainError(Exception):
    """Base for all expected business errors. `code` is a stable i18n message key."""

    code = "domain_error"

    def __init__(self, detail: str = "") -> None:
        super().__init__(detail or self.code)
        self.detail = detail


class NotFound(DomainError):
    code = "not_found"


class PolicyViolation(DomainError):
    """A business rule rejected the input. `violations` lists every broken rule."""

    code = "policy_violation"

    def __init__(self, violations: list[str]) -> None:
        super().__init__("; ".join(violations))
        self.violations = violations


class ConflictError(DomainError):
    code = "conflict"
```

```python
# src/domain/accounts/permissions.py
from enum import StrEnum
from types import MappingProxyType

from domain.accounts.roles import Role


class Permission(StrEnum):
    LESSONS_VIEW = "lessons:view"
    EXERCISES_COMPLETE = "exercises:complete"
    TESTS_SUBMIT = "tests:submit"
    SCORES_VIEW_OWN = "scores:view-own"
    CONTENT_CREATE = "content:create"
    CONTENT_EDIT = "content:edit"
    TESTS_CONFIGURE = "tests:configure"
    SCORES_VIEW_ALL = "scores:view-all"
    CONTENT_RESUBMIT = "content:resubmit"
    CHILD_PROGRESS_VIEW = "child-progress:view"
    CHILD_SCORES_VIEW = "child-scores:view"
    ACCOUNTS_MANAGE = "accounts:manage"
    PARENTS_LINK = "parents:link"
    CONTENT_REVIEW = "content:review"
    CONTENT_BLOCK = "content:block"
    CONTENT_UNBLOCK = "content:unblock"


P = Permission
# Canonical copy of the Roles & Permissions Matrix in docs/requirements.md — keep verbatim.
ROLE_PERMISSIONS = MappingProxyType({
    Role.STUDENT: frozenset({P.LESSONS_VIEW, P.EXERCISES_COMPLETE, P.TESTS_SUBMIT, P.SCORES_VIEW_OWN}),
    Role.TEACHER: frozenset({P.CONTENT_CREATE, P.CONTENT_EDIT, P.TESTS_CONFIGURE,
                             P.SCORES_VIEW_ALL, P.CONTENT_RESUBMIT}),
    Role.PARENT: frozenset({P.CHILD_PROGRESS_VIEW, P.CHILD_SCORES_VIEW}),
    Role.ADMIN: frozenset({P.ACCOUNTS_MANAGE, P.PARENTS_LINK, P.CONTENT_REVIEW, P.CONTENT_BLOCK,
                           P.CONTENT_UNBLOCK, P.SCORES_VIEW_ALL}),
})


def has_permission(role: Role, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS[role]
```

```python
# src/domain/assessment/answer_checker.py
from decimal import Decimal, InvalidOperation

_SPACES = (" ", " ", " ")


def parse_numeric(raw: str) -> Decimal | None:
    """Parse a learner's numeric answer; '2', '2.0', '2,0' and ' 2.00 ' are all Decimal('2').

    Returns None for anything unparseable — the caller scores it as incorrect.
    """
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
```

```python
# src/domain/assessment/scoring.py
from collections.abc import Sequence
from dataclasses import dataclass

MIN_SCORE = 1  # Requirement: an all-incorrect test reports 1, never 0.


@dataclass(frozen=True)
class QuestionResult:
    question_id: int
    points: int
    is_correct: bool


@dataclass(frozen=True)
class TestScore:
    earned_points: int
    score: int


def compute_score(results: Sequence[QuestionResult]) -> TestScore:
    earned = sum(result.points for result in results if result.is_correct)
    return TestScore(earned_points=earned, score=max(MIN_SCORE, earned))
```

```python
# src/domain/moderation/state_machine.py
from enum import StrEnum

from domain.common.errors import ConflictError
from domain.moderation.status import ModerationStatus as S


class ModerationAction(StrEnum):
    FLAG = "FLAG"
    APPROVE = "APPROVE"
    BLOCK = "BLOCK"
    RESUBMIT = "RESUBMIT"
    CLEAR = "CLEAR"


class InvalidModerationTransition(ConflictError):
    code = "invalid_moderation_transition"


A = ModerationAction
_TRANSITIONS: dict[tuple[S, A], S] = {
    (S.ACTIVE, A.FLAG): S.FLAGGED,
    (S.FLAGGED, A.APPROVE): S.ACTIVE,
    (S.ACTIVE, A.BLOCK): S.BLOCKED,
    (S.FLAGGED, A.BLOCK): S.BLOCKED,
    (S.RESUBMITTED, A.BLOCK): S.BLOCKED,
    (S.BLOCKED, A.RESUBMIT): S.RESUBMITTED,
    (S.RESUBMITTED, A.CLEAR): S.ACTIVE,
}


def next_status(current: S, action: A) -> S:
    try:
        return _TRANSITIONS[(current, action)]
    except KeyError:
        raise InvalidModerationTransition(f"{action} not allowed from {current}") from None


def is_visible_to_learners(status: S) -> bool:
    return status == S.ACTIVE  # `==`, not `is`: values loaded from the DB may be plain str
```

✅ DO express rules as data and lookup tables (above) rather than chains of `if`s.
❌ DON'T do this in a view:

```python
# ❌ business rule + persistence + magic strings in the web layer
if lesson.moderation_status in ("ACTIVE", "FLAGGED"):
    lesson.moderation_status = "BLOCKED"
    lesson.save()
```

---

## 5. Application (Use Case) Pattern

- One class per use case, with dependencies injected through `__init__` as **ports** (Protocols) and a single `execute(command)` method.
- Wrap all writes in the `UnitOfWork`, so each use case is one transaction.
- Return a DTO or domain value. Never return an ORM object.

```python
# src/application/common/unit_of_work.py
from typing import Protocol, Self


class UnitOfWork(Protocol):
    def __enter__(self) -> Self: ...
    def __exit__(self, *exc_info: object) -> bool | None: ...
```

```python
# src/application/assessment/submit_test.py
from collections.abc import Mapping
from dataclasses import dataclass

from application.common.audit import AuditPort
from application.common.unit_of_work import UnitOfWork
from domain.assessment.answer_checker import is_correct
from domain.assessment.ports import AttemptRepository, LearnerTestRepository
from domain.assessment.scoring import QuestionResult, TestScore, compute_score
from domain.common.clock import Clock
from domain.common.errors import ConflictError


class AlreadySubmitted(ConflictError):
    code = "test_already_submitted"


@dataclass(frozen=True)
class SubmitTestCommand:
    student_id: int
    test_id: int
    responses: Mapping[int, str]  # question_id -> raw response; missing = incorrect


class SubmitTest:
    def __init__(self, tests: LearnerTestRepository, attempts: AttemptRepository,
                 uow: UnitOfWork, clock: Clock, audit: AuditPort) -> None:
        self._tests, self._attempts, self._uow = tests, attempts, uow
        self._clock, self._audit = clock, audit

    def execute(self, cmd: SubmitTestCommand) -> TestScore:
        with self._uow:
            test = self._tests.get_visible(cmd.test_id)  # raises NotFound if hidden/unpublished
            if self._attempts.exists(cmd.student_id, cmd.test_id):
                raise AlreadySubmitted()
            results = [
                QuestionResult(q.id, q.points,
                               is_correct(q.kind, q.answer_key, cmd.responses.get(q.id, "")))
                for q in test.questions
            ]
            score = compute_score(results)
            self._attempts.add(cmd.student_id, cmd.test_id, results, score, self._clock.now())
            self._audit.record("test.submitted", actor_id=cmd.student_id,
                               target=("test", cmd.test_id), metadata={"score": score.score})
        return score
```

```python
# src/infrastructure/container.py — composition root (the only place that picks implementations)
from application.assessment.submit_test import SubmitTest
from infrastructure.persistence.assessment.repositories import (
    DjangoAttemptRepository, DjangoLearnerTestRepository)
from infrastructure.persistence.audit.repositories import DjangoAuditPort
from infrastructure.persistence.common.unit_of_work import DjangoUnitOfWork
from infrastructure.system_clock import SystemClock


def submit_test() -> SubmitTest:
    return SubmitTest(DjangoLearnerTestRepository(), DjangoAttemptRepository(),
                      DjangoUnitOfWork(), SystemClock(), DjangoAuditPort())
```

❌ DON'T instantiate repositories inside a use case (`self._repo = DjangoAttemptRepository()`), because it can't then be tested with fakes.
❌ DON'T call `datetime.now()` / `timezone.now()` in domain or application code. Inject `Clock`.
❌ DON'T use module-level singletons or global state. Build objects in `container.py`.

---

## 6. Database Access Pattern

### 6.1 Connection & SQLite configuration (`config/settings/base.py`)

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": env_path("DATABASE_PATH", default=BASE_DIR / "data" / "db.sqlite3"),
        "OPTIONS": {
            "transaction_mode": "IMMEDIATE",   # take the write lock at BEGIN, avoiding upgrade deadlocks
            "timeout": 20,                     # seconds to wait for the lock
            "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;",
        },
    }
}
ATOMIC_REQUESTS = False  # transactions are owned by use cases (UnitOfWork), not by requests
```

### 6.2 Models

- Models live **only** in `infrastructure/persistence/<ctx>/models.py`, are named `<Entity>Model`, and have an explicit `db_table`.
- Integrity rules from the architecture's "Integrity rules" table are declared as `Meta.constraints` (`UniqueConstraint`, `CheckConstraint`) **in addition to** the domain checks.
- Moderated models use the shared `ModeratedModel` abstract base and its queryset.

```python
# src/infrastructure/persistence/common/managers.py
from django.db import models

from domain.moderation.status import ModerationStatus


class ModeratedQuerySet(models.QuerySet):
    def visible_to_learners(self) -> "ModeratedQuerySet":
        """The ONLY sanctioned filter for Student/Parent-facing content."""
        return self.filter(moderation_status=ModerationStatus.ACTIVE)


class ModeratedModel(models.Model):
    moderation_status = models.CharField(
        max_length=12, choices=[(s.value, s.value) for s in ModerationStatus],
        default=ModerationStatus.ACTIVE)
    moderation_reason = models.TextField(blank=True)
    moderation_updated_at = models.DateTimeField(null=True, blank=True)

    objects = ModeratedQuerySet.as_manager()

    class Meta:
        abstract = True
```

```python
# src/infrastructure/persistence/assessment/models.py (excerpt)
class TestAttemptModel(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    test = models.ForeignKey("content.ChapterTestModel", on_delete=models.CASCADE)
    earned_points = models.PositiveSmallIntegerField()
    score = models.PositiveSmallIntegerField()
    submitted_at = models.DateTimeField()

    class Meta:
        db_table = "assessment_test_attempt"
        constraints = [
            models.UniqueConstraint(fields=["student", "test"], name="uniq_attempt_per_student_test"),
            models.CheckConstraint(condition=models.Q(score__gte=1, score__lte=100),
                                   name="attempt_score_1_100"),
            models.CheckConstraint(condition=models.Q(earned_points__lte=100),
                                   name="attempt_earned_0_100"),
        ]
```

### 6.3 Repositories (writes) and query services (reads)

```python
# src/infrastructure/persistence/assessment/repositories.py (excerpt)
from django.db import IntegrityError

from application.assessment.submit_test import AlreadySubmitted


class DjangoAttemptRepository:
    def exists(self, student_id: int, test_id: int) -> bool:
        return TestAttemptModel.objects.filter(student_id=student_id, test_id=test_id).exists()

    def add(self, student_id, test_id, results, score, submitted_at) -> None:
        try:
            attempt = TestAttemptModel.objects.create(
                student_id=student_id, test_id=test_id, earned_points=score.earned_points,
                score=score.score, submitted_at=submitted_at)
        except IntegrityError as exc:  # concurrent double-submit hit the UNIQUE constraint
            raise AlreadySubmitted() from exc
        AttemptAnswerModel.objects.bulk_create(
            AttemptAnswerModel(attempt=attempt, question_id=r.question_id,
                               is_correct=r.is_correct,
                               points_awarded=r.points if r.is_correct else 0)
            for r in results)
```

```python
# src/infrastructure/persistence/progress/queries.py (excerpt) — scoped read model
def child_progress(parent_id: int, student_id: int) -> ChildProgressDTO:
    if not ParentChildLinkModel.objects.filter(parent_id=parent_id, student_id=student_id).exists():
        raise NotFound("child not linked")  # 404 — never reveal that the child exists
    return _build_progress(student_id)
```

```python
# src/infrastructure/persistence/common/unit_of_work.py
from django.db import transaction


class DjangoUnitOfWork:
    def __enter__(self) -> "DjangoUnitOfWork":
        self._atomic = transaction.atomic()
        self._atomic.__enter__()
        return self

    def __exit__(self, *exc_info: object) -> bool | None:
        return self._atomic.__exit__(*exc_info)
```

| ✅ DO | ❌ DON'T |
|------|---------|
| `Lesson.objects.visible_to_learners()` for every Student/Parent query | hand-write `filter(moderation_status="ACTIVE")` in views or queries |
| scope by the viewer **inside** the query (`filter(student_id=viewer.id)`) | fetch by id and check ownership afterwards in Python |
| `select_related` / `prefetch_related` in query services that render lists | rely on N+1 lazy loads in templates |
| `bulk_create` for attempt answers | create 10 rows in a loop with separate saves |
| map `IntegrityError` to a domain error inside the repository | let `IntegrityError` reach the view |
| ORM only | raw SQL / `.extra()` / string-built SQL (if ever unavoidable: parameterised + Architect approval) |
| return DTOs/dataclasses from repositories and queries | return querysets to the application layer |

### 6.4 Migrations

- One migration directory per persistence app. `AUTH_USER_MODEL = "accounts.UserModel"` must be in `accounts` migration `0001` (Story 1.1). It cannot be changed later.
- Seed data (grades K–8, subjects, grade-2 active flags) goes in a **data migration** (`RunPython` with a reverse function). ❌ No fixtures loaded by hand.
- Migrations must work on an empty DB **and** be reversible. CI runs `makemigrations --check --dry-run`.
- ❌ Never edit a migration that has been merged. Add a new one.

---

## 7. Web Layer Pattern (Views, Forms, HTMX)

### 7.1 Thin views

A view does exactly four things: **authorise → parse/validate → call a use case or query → render/redirect.** Target ≤ 20 lines.

```python
# src/infrastructure/web/assessment/views.py
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from application.assessment.submit_test import SubmitTestCommand
from domain.accounts.permissions import Permission
from infrastructure import container
from infrastructure.web.common.decorators import require_permission
from infrastructure.web.assessment.forms import parse_test_responses


@require_POST
@require_permission(Permission.TESTS_SUBMIT)
def submit_test(request, test_id: int):
    command = SubmitTestCommand(student_id=request.user.pk, test_id=test_id,
                                responses=parse_test_responses(request.POST))
    container.submit_test().execute(command)  # domain errors -> DomainErrorMiddleware
    return redirect("assessment:result", test_id=test_id)
```

❌ DON'T:

```python
@login_required                     # ❌ role not checked
def submit_test(request, test_id):
    test = ChapterTestModel.objects.get(pk=test_id)       # ❌ no visibility scope; DoesNotExist -> 500
    score = sum(q.points for q in test.questions.all()
                if request.POST.get(f"q_{q.id}") == q.answer_key["option_id"])  # ❌ rule in view; numeric/TF wrong
    TestAttemptModel.objects.create(student=request.user, test=test, score=score)  # ❌ score 0 possible
    return render(request, "result.html", {"score": score})                      # ❌ POST without redirect
```

### 7.2 Authorization decorator (mandatory on every non-public view)

```python
# src/infrastructure/web/common/decorators.py
from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from domain.accounts.permissions import Permission, has_permission
from domain.accounts.roles import Role


def require_permission(*permissions: Permission):
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            role = Role(request.user.role)
            if not all(has_permission(role, p) for p in permissions):
                raise PermissionDenied  # -> 403 template
            return view(request, *args, **kwargs)

        wrapper.required_permissions = permissions  # read by the URL-coverage test (§12.4)
        return wrapper

    return decorator
```

- **Role check = 403, record scope = 404.** Out-of-scope records raise `NotFound` from the scoped query/repository and are never checked after loading.
- Public views (login, setlang, healthz, error pages) are listed in `PUBLIC_URL_NAMES` in `infrastructure/web/common/decorators.py`. Every other URL must carry `required_permissions`. A test enforces this.

### 7.3 Forms and request validation

- Use Django `Form`/`ModelForm` only for **input shape** (types, required, length). Business rules (e.g. Σ points = 100) are raised by the domain as `PolicyViolation` and shown through `form.add_error(None, …)`.
- Bilingual content forms use `BilingualFieldsMixin`, which makes every `*_ro` and `*_en` field required.
- ❌ DON'T use `fields = "__all__"`. List fields explicitly.

### 7.4 HTMX

- Detect HTMX requests with `infrastructure/web/common/htmx.py::is_htmx(request)` (`HX-Request` header). HTMX requests get the partial `_<name>.html`; non-HTMX get the full page (progressive enhancement).
- The CSRF token goes to HTMX through `<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>` in `layouts/base.html`.
- ❌ No inline `<script>` and no `hx-on:*` attributes with JS. CSP forbids inline scripts. Use `static/js/` modules if JS is ever unavoidable.
- `htmx.min.js` is vendored in `static/js/` (version recorded in the file header). ❌ No CDN.

### 7.5 Response conventions

| Situation | Full-page request | HTMX request |
|-----------|-------------------|--------------|
| Successful POST | `302` redirect (POST-redirect-GET) | `200` partial, or `HX-Redirect` header |
| Form/input invalid | `400` re-render with errors | `422` partial with errors |
| `PolicyViolation` | `422` re-render with a violations list | `422` partial |
| `ConflictError` | `409` page with localized message | `409` partial (`components/alert.html`) |
| `NotFound` | `404` page | `404` partial |
| `PermissionDenied` | `403` page | `403` partial |

---

## 8. Error Handling Pattern

1. Expected business failures are **`DomainError` subclasses** with a stable `code` (§4).
2. They are mapped to HTTP **in exactly one place**, `DomainErrorMiddleware`.
3. Unexpected exceptions are never caught in business code. They become a 500 page carrying the request id and are logged with the stack trace.

```python
# src/infrastructure/web/common/middleware.py (excerpt)
from domain.common.errors import ConflictError, DomainError, NotFound, PolicyViolation
from infrastructure.web.common.errors import render_error

_STATUS_BY_ERROR: tuple[tuple[type[DomainError], int], ...] = (
    (NotFound, 404),
    (PolicyViolation, 422),
    (ConflictError, 409),
    (DomainError, 400),  # fallback — keep last
)


class DomainErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, DomainError):
            return None  # let Django's 500 handling + logging take over
        status = next(code for err, code in _STATUS_BY_ERROR if isinstance(exception, err))
        logger.info("domain_error", extra={"code": exception.code, "status": status})
        return render_error(request, exception, status)  # localized message from exception.code
```

| ✅ DO | ❌ DON'T |
|------|---------|
| `raise AlreadySubmitted()` from the use case | `return None` / `return False` to signal failure |
| `raise ... from exc` when translating exceptions | `except Exception: pass` (swallowing) |
| keep user messages in gettext catalogues keyed by `code` | put English strings in exceptions shown to users |
| let unexpected errors propagate | wrap every view in `try/except Exception` |

---

## 9. Logging Pattern

- Standard `logging`, with `logger = logging.getLogger(__name__)` per module. A JSON formatter writes to stdout (`infrastructure/logging/json_formatter.py`, stdlib-based).
- `RequestIdMiddleware` sets `request.id` (or reuses an incoming `X-Request-ID`) and adds `request_id`, `user_id` and `role` to every log record through a logging filter.

| Level | Use for |
|-------|---------|
| `DEBUG` | local diagnostics only; off in prod |
| `INFO` | business events (`test.submitted`, `content.blocked`), domain errors handled as 4xx |
| `WARNING` | suspicious but handled (lockout triggered, `database is locked` retried) |
| `ERROR` | unexpected exceptions (500), failed health check |

```python
# ✅ DO — event name + structured context, IDs only
logger.info("content.blocked", extra={"content_type": "lesson", "content_id": lesson_id,
                                      "actor_id": admin_id})

# ❌ DON'T — PII, free text, f-strings
logger.info(f"Admin {user.full_name} blocked lesson for {student.username}, born {student.date_of_birth}")
```

**Never log:** passwords or hashes, session/CSRF tokens, `SECRET_KEY`, full names, dates of birth, test/exercise answers, block reasons (those go to `AUDIT_LOG`, not to logs), request bodies.

**Logs vs audit:** operational logs are ephemeral diagnostics. `AUDIT_LOG` (written through `AuditPort` inside the use-case transaction) is the business record of who did what. Every audited action listed in the architecture's Security Design MUST call `AuditPort.record`.

---

## 10. Configuration Pattern

- Settings modules: `config/settings/base.py` (shared), `dev.py`, `test.py`, `prod.py`. `DJANGO_SETTINGS_MODULE` selects one.
- Environment variables are read **only** in settings, through a small helper. There are no `os.environ` reads anywhere else.

```python
# src/config/settings/env.py
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

_MISSING = object()


def env_str(name: str, default: object = _MISSING) -> str:
    value = os.environ.get(name)
    if value is None:
        if default is _MISSING:
            raise ImproperlyConfigured(f"Required environment variable {name} is not set")
        return str(default)
    return value


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in env_str(name, default).split(",") if item.strip()]


def env_path(name: str, default: Path) -> Path:
    return Path(env_str(name, str(default)))
```

| Variable | Required in prod | Dev default | Notes |
|----------|------------------|-------------|-------|
| `DJANGO_SETTINGS_MODULE` | yes | `config.settings.dev` | |
| `DJANGO_SECRET_KEY` | **yes** (no default in prod) | dev-only placeholder in `dev.py` | secret |
| `DJANGO_ALLOWED_HOSTS` | yes | `localhost,127.0.0.1` | comma list |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | yes | empty | `https://…` origins |
| `DATABASE_PATH` | yes | `./data/db.sqlite3` | on a persistent volume in prod (ADR-004) |
| `LOG_LEVEL` | no | `INFO` (`DEBUG` in dev) | |

- `prod.py` sets `DEBUG=False`, `SECURE_SSL_REDIRECT=True`, `SECURE_HSTS_SECONDS=31536000`, `SESSION_COOKIE_SECURE=CSRF_COOKIE_SECURE=True`, `SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO","https")`.
- Fixed policy values (session age 8 h, axes 5 failures / 15 min, Argon2 first in `PASSWORD_HASHERS`, password min length 8) are **constants in `base.py`**, not env vars. They are product decisions, not deployment knobs.
- `.env.example` lists every variable with a placeholder. ❌ Never commit `.env` or real secrets (gitignored; secret scan in CI).

---

## 11. Templates, UI & Internationalization

### 11.1 Template structure

- `layouts/base.html` contains the header (generic avatar, language switcher, notification badge for teachers), the flash messages, the `{% block content %}` and the HTMX script.
- Pages extend `layouts/base.html`. Partials are named `_name.html`. Primitives live in `components/`.
- ❌ No inline `style=""`, `<style>` or `<script>`. Styles go in `static/css/`.

### 11.2 UI Primitive Catalogue (MANDATORY context for every UI story)

**Definition:** a **primitive** has **no business logic** and is **reusable by two or more features**. A primitive **MUST** live in the shared library below. **Creating a primitive inside a feature folder (`templates/<context>/`) is a violation**, not an alternative. Feature-specific components (e.g. the catalogue grade tile, the test-editor question row) stay in their feature folder.

Shared library: templates in `src/infrastructure/web/templates/components/`, inclusion tags in `src/infrastructure/web/templatetags/ui.py`, styles in `src/infrastructure/web/static/css/components/<name>.css`, all built on tokens in `static/css/tokens.css`.

| Primitive | Template / tag | Purpose / variants |
|-----------|----------------|--------------------|
| Button | `components/button.html` · `{% ui_button %}` | `primary`, `secondary`, `danger`, `link`; `type`, `disabled`, optional `hx-*` passthrough |
| Status pill | `components/status_pill.html` · `{% ui_status_pill status %}` | moderation states (ACTIVE/FLAGGED/BLOCKED/RESUBMITTED), test DRAFT/PUBLISHED; colour + text (never colour alone) |
| Badge | `components/badge.html` | counts (unread notifications), small labels |
| Alert | `components/alert.html` · `{% ui_alert level %}` | `info`, `success`, `warning`, `error`; used by flash messages and HTMX error partials |
| Form field | `components/form_field.html` · `{% ui_field form.field %}` | label, input, help, errors; RO/EN paired-field layout variant |
| Card | `components/card.html` | container with title/body/footer slots |
| Avatar | `components/avatar.html` | the generic user icon (no uploads, per requirements) |
| Icon | `components/icon.html` · `{% ui_icon "name" %}` | inline SVG sprite from `static/icons/sprite.svg` |
| Progress meter | `components/progress_meter.html` · `{% ui_progress done total %}` | "6/8" with bar; accessible text |
| Score display | `components/score.html` · `{% ui_score value %}` | final 1–100 score display |
| Empty state | `components/empty_state.html` | "nothing here yet" message + optional action |
| Confirm dialog | `components/confirm_dialog.html` | native `<dialog>`; used for test submit with unanswered questions, block/clear actions |
| Page header | `components/page_header.html` | title + breadcrumb + actions slot |
| Data table | `components/table.html` | simple accessible table with header/empty state |
| Language switcher | `components/language_switcher.html` | RO/EN toggle posting to `/i18n/setlang/` |
| Disabled tile | `components/disabled_tile.html` | non-interactive item (no link, `aria-disabled`), used for inactive grades/subjects and hidden items |

**Visual verification:** Storybook needs a JS toolchain, which ADR-003 avoids. Use a **DEBUG-only `/_styleguide/` page** (`infrastructure/web/styleguide/`) that renders every primitive and variant in both RO and EN. Each new or changed primitive must appear there. That's the equivalent of Storybook for this stack. The route is only registered when `DEBUG=True`.

```django
{# ✅ DO — reuse the primitive #}
{% load ui %}
{% ui_status_pill lesson.moderation_status %}

{# ❌ DON'T — re-implement a pill inside a feature template #}
<span class="pill pill--red">{{ lesson.moderation_status }}</span>
```

### 11.3 Internationalization

- **UI text:** every user-visible string uses `{% translate %}` / `{% blocktranslate %}` in templates and `gettext_lazy as _` in Python (forms, messages). Message ids are **English**, and `ro` is a full translation. Catalogues live in `infrastructure/i18n/locale/`.
- **Content text:** read through the `localized` tag/helper. Never pick `_ro`/`_en` by hand.

```python
# src/infrastructure/web/common/i18n.py
from django.utils.translation import get_language

CONTENT_LANGUAGES = ("ro", "en")


def content_language() -> str:
    lang = (get_language() or "ro")[:2]
    return lang if lang in CONTENT_LANGUAGES else "ro"


def localized(obj: object, field: str) -> str:
    return getattr(obj, f"{field}_{content_language()}")
```

```django
{% load i18n_content %}
<h1>{% localized chapter "title" %}</h1>          {# ✅ #}
<h1>{{ chapter.title_ro }}</h1>                     {# ❌ hard-codes the language #}
```

- **Markdown:** render teacher Markdown **only** through `infrastructure/rendering/markdown.py::render_markdown(text) -> SafeString` (Markdown → nh3 allowlist). Use it in templates as `{% render_markdown lesson "body" %}`.
- ❌ `|safe` and `mark_safe` are forbidden everywhere except inside `render_markdown`. CI greps for them.

### 11.4 Accessibility baseline (grade-2 users)

Labels on every input; status never shown by colour alone; focus outline kept; minimum 16 px body text; buttons are `<button>`, links are `<a>`; `lang` attribute set to the active language. The optional `aire-ui-ux-design` workflow may raise this bar.

---

## 12. Testing Patterns

### 12.1 Organisation & naming

| Suite | Location | Scope | DB |
|-------|----------|-------|----|
| Unit — domain | `tests/unit/domain/<ctx>/` | pure rules | none (no `django_db` mark) |
| Unit — application | `tests/unit/application/<ctx>/` | use cases with **fakes** from `tests/fakes/` | none |
| Integration — persistence | `tests/integration/persistence/<ctx>/` | repositories, queries, constraints, migrations | SQLite (pytest-django) |
| Integration — web | `tests/integration/web/<ctx>/` | views via Django test client: auth, 403/404, forms, HTMX partials, i18n | SQLite |
| E2E | `tests/e2e/test_<role>_journey.py` | browser journeys per role (Playwright + `live_server`) | SQLite |

- Test files mirror source files: `src/domain/assessment/scoring.py` → `tests/unit/domain/assessment/test_scoring.py`.
- Names describe behaviour: `test_<behaviour>_when_<condition>`.
- Structure is always **Arrange / Act / Assert**, separated by blank lines. One behaviour per test.
- Tests are written **first** (TDD, implementation rulebook).

### 12.2 Unit tests

```python
# tests/unit/domain/assessment/test_scoring.py
import pytest

from domain.assessment.answer_checker import parse_numeric
from domain.assessment.scoring import QuestionResult, compute_score


def test_score_is_one_when_all_answers_incorrect():
    results = [QuestionResult(question_id=i, points=10, is_correct=False) for i in range(10)]

    score = compute_score(results)

    assert (score.earned_points, score.score) == (0, 1)


def test_score_equals_sum_of_correct_weights():
    results = [QuestionResult(1, 40, True), QuestionResult(2, 35, False), QuestionResult(3, 25, True)]

    assert compute_score(results).score == 65


@pytest.mark.parametrize("raw", ["2", "2.0", "2,0", " 2.00 ", "2 "])
def test_numeric_answers_equal_when_only_formatting_differs(raw):
    assert parse_numeric(raw) == parse_numeric("2")


@pytest.mark.parametrize("raw", ["", "abc", "2,5,1", "NaN", "Infinity"])
def test_unparseable_numeric_answer_returns_none(raw):
    assert parse_numeric(raw) is None
```

```python
# tests/unit/application/assessment/test_submit_test.py
def test_second_submission_is_rejected(fake_tests, fake_attempts, fake_uow, fixed_clock, fake_audit):
    use_case = SubmitTest(fake_tests, fake_attempts, fake_uow, fixed_clock, fake_audit)
    fake_tests.add_visible(make_test(test_id=7, points=[10] * 10))
    use_case.execute(SubmitTestCommand(student_id=1, test_id=7, responses={}))

    with pytest.raises(AlreadySubmitted):
        use_case.execute(SubmitTestCommand(student_id=1, test_id=7, responses={}))

    assert fake_attempts.count() == 1
```

**Mocking strategy:**
- ✅ Hand-written **fakes** (in-memory implementations of ports) in `tests/fakes/`, shared by all application tests.
- ✅ `FixedClock` for time.
- ❌ DON'T mock domain functions or the class under test. ❌ DON'T `patch()` internals; if you need to, the dependency should be injected.
- `unittest.mock` is allowed only for genuinely external boundaries. There are none at runtime today.

### 12.3 Integration tests

- `pytest-django` with the SQLite test DB. Each test runs in a rolled-back transaction (the `db` fixture), so no manual cleanup is needed. Use `transactional_db` only for tests that verify transaction or constraint behaviour (e.g. the double-submit race).
- Data comes from **factory_boy** factories in `tests/factories/<ctx>.py`. ❌ No JSON fixtures.
- Role fixtures in `tests/conftest.py`: `student`, `other_student`, `teacher`, `parent` (linked to `student`), `unlinked_parent`, `admin_user`, plus logged-in clients `student_client`, `teacher_client`, `parent_client`, `admin_client`.
- No external services exist. If one is added, wrap it in an adapter port and fake it.

```python
# tests/integration/web/progress/test_child_progress_view.py
import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_parent_gets_404_for_unlinked_child(parent_client, other_student):
    url = reverse("progress:child", kwargs={"student_id": other_student.pk})

    response = parent_client.get(url)

    assert response.status_code == 404


def test_student_gets_403_on_teacher_dashboard(student_client):
    response = student_client.get(reverse("content:teacher_dashboard"))

    assert response.status_code == 403


def test_blocked_lesson_is_hidden_from_student(student_client, lesson_factory):
    lesson = lesson_factory(moderation_status="BLOCKED")

    response = student_client.get(reverse("content:lesson", kwargs={"chapter_id": lesson.chapter_id}))

    assert response.status_code == 404
```

### 12.4 Mandatory cross-cutting tests (created in Epic 1, extended by every story)

| Test | Guarantees |
|------|-----------|
| `test_permission_matrix_matches_requirements` | `ROLE_PERMISSIONS` equals the matrix in `docs/requirements.md` (the expected table is written in the test) |
| `test_every_url_is_protected_or_public` | walks the URL resolver; every pattern either has `required_permissions` or is in `PUBLIC_URL_NAMES` |
| `test_role_access_matrix` | parametrised: (role × protected URL) → expected 200/302/403 |
| `test_no_unsafe_html_outside_renderer` | greps `src/` for `mark_safe`/`|safe` outside `rendering/markdown.py` |
| `test_layers_contract` | runs `lint-imports` (import-linter) |
| `test_translations_complete` | no empty `msgstr` in the `ro` catalogue; every content form requires both languages |
| `test_moderation_transitions_table` | every (status, action) pair: allowed → expected status; otherwise `InvalidModerationTransition` |

### 12.5 E2E tests (Playwright)

- One journey file per role, covering the FC-2 workflows: Student (catalogue → lesson → finish exercise → submit test → see score; second attempt blocked), Teacher (edit lesson, configure test to 100, publish, receive block notice, resubmit), Parent (sees linked child only), Admin (create accounts, link parent, flag → block → clear).
- Locate elements by role/label (`page.get_by_role`, `get_by_label`). ❌ No CSS-class selectors.
- Run with `pytest -m e2e` against `live_server`. Set `DJANGO_ALLOW_ASYNC_UNSAFE=true` in the e2e conftest only.

### 12.6 Coverage

| Scope | Minimum | Enforcement |
|-------|---------|-------------|
| Overall (`src/`) | **≥ 85 %** lines + branches | `pytest --cov=src --cov-branch --cov-fail-under=85` |
| `src/domain/` | **100 %** | `coverage report --include="src/domain/*" --fail-under=100` |
| `src/application/` | ≥ 95 % | `coverage report --include="src/application/*" --fail-under=95` |

- **Omit:** `*/migrations/*`, `src/config/settings/*`, `src/config/wsgi.py`, `manage.py`, `src/infrastructure/web/styleguide/*`.
- **Always test:** scoring, numeric parsing, moderation transitions, permission checks, scoping (404/403), publication policy, scoring lock, notification fan-out, i18n field requirements.
- ❌ DON'T write assertion-free tests to inflate coverage. ❌ DON'T use `# pragma: no cover` without a comment explaining why.

---

## 13. Security Coding Rules

| Rule | ✅ DO | ❌ DON'T |
|------|------|---------|
| Authorisation | `@require_permission(...)` + scoped query | rely on hiding links in templates |
| CSRF | `{% csrf_token %}` in forms; HTMX header in base layout | `@csrf_exempt` (forbidden) |
| Output | autoescape; `render_markdown` for content | `|safe`, `mark_safe`, `format_html` with user input |
| SQL | ORM, parameterised | f-string SQL, `.extra()`, `RawSQL` with user input |
| Passwords | Django auth APIs (`set_password`, validators) | storing or logging raw passwords |
| Redirects | `url_has_allowed_host_and_scheme` for `next` | redirect to an unchecked user-supplied URL |
| Uploads | none in MVP (ADR-010) | add file fields without an Architect decision |
| Secrets | env vars via `config/settings/env.py` | literals in code, tests or the Dockerfile |
| Third parties | local static assets | CDN scripts/fonts, analytics, trackers |

---

## 14. Documentation Standards

- **Docstrings:** required for public classes, functions and use cases in `domain` and `application`. Use Google style (summary line; `Args`, `Returns`, `Raises` where non-obvious). Views get a one-line docstring naming the route and permission.
- **Comments** explain *why*, e.g. `# Requirement: all-incorrect reports 1, never 0`. Link a requirement or ADR id when a rule comes from one.
- **README.md** sections: Overview · Prerequisites (Python 3.12, uv) · Setup (`uv sync`, `.env`, `migrate`, `createsuperuser` via the admin bootstrap command) · Running · Testing (unit/integration/e2e, coverage) · Project structure (link to this doc) · Configuration (env table) · Troubleshooting.
- **HTTP routes:** the route catalogue in `00-system-architecture-greenfield.md` is the API documentation. A story that adds or changes a route updates that table in the same change.
- **Story review docs:** `docs/stories-implemented/story-N.M-review.md` with the DoD evidence (implementation rulebook).

---

## 15. Design Pattern Usage (from `aire-design-patterns.md`)

| Pattern | Where used | Why |
|---------|-----------|-----|
| Repository | write ports in `domain/<ctx>/ports.py`, Django implementations in persistence | keeps domain/application free of the ORM (ADR-005) |
| Strategy (lookup table) | `AnswerChecker` per `QuestionKind`: `{MCQ: check_choice, TRUE_FALSE: check_bool, NUMERIC: check_numeric}` | adding a question type doesn't modify the existing checkers |
| State machine (table-driven) | `ModerationStateMachine` | all transitions in one auditable table |
| Unit of Work | `DjangoUnitOfWork` | one transaction per use case |
| Decorator | `@require_permission` | cross-cutting authorisation |
| Adapter | `DjangoAuditPort`, `DjangoNotifier` | infrastructure implements application ports |
| Observer / event bus | **not used** | only one side effect per event (notify + audit inside the use case). Revisit if the side effects multiply. |
| Singleton | **forbidden** | use the composition root |

---

## 16. File / Module Boundary Map (input for `docs/plans/dependency-graph.yml`)

| Concern | Owning files / globs |
|---------|----------------------|
| **accounts** (users, roles, permissions, parent links, login, language pref) | `src/domain/accounts/**`, `src/application/accounts/**`, `src/infrastructure/persistence/accounts/**`, `src/infrastructure/web/accounts/**`, `src/infrastructure/web/templates/accounts/**`, `tests/**/accounts/**`, `tests/factories/accounts.py` |
| **catalogue** (grades, subjects, seed) | `src/infrastructure/persistence/catalogue/**`, `src/infrastructure/web/catalogue/**`, `src/infrastructure/web/templates/catalogue/**`, `tests/**/catalogue/**`, `tests/factories/catalogue.py` |
| **content** (chapters, lessons, exercises, tests, publication, scoring lock, teacher dashboard) | `src/domain/content/**`, `src/application/content/**`, `src/infrastructure/persistence/content/**`, `src/infrastructure/web/content/**`, `src/infrastructure/web/templates/content/**`, `src/infrastructure/rendering/**`, `tests/**/content/**`, `tests/factories/content.py` |
| **moderation** (state machine, queue, actions) | `src/domain/moderation/**`, `src/application/moderation/**`, `src/infrastructure/web/moderation/**`, `src/infrastructure/web/templates/moderation/**`, `tests/**/moderation/**` |
| **assessment** (answer checking, scoring, submission, results) | `src/domain/assessment/**`, `src/application/assessment/**`, `src/infrastructure/persistence/assessment/**`, `src/infrastructure/web/assessment/**`, `src/infrastructure/web/templates/assessment/**`, `tests/**/assessment/**`, `tests/factories/assessment.py` |
| **progress** (lesson views, exercise completion, progress pages for student/parent, scores lists) | `src/domain/progress/**`, `src/application/progress/**`, `src/infrastructure/persistence/progress/**`, `src/infrastructure/web/progress/**`, `src/infrastructure/web/templates/progress/**`, `tests/**/progress/**`, `tests/factories/progress.py` |
| **notifications** | `src/infrastructure/persistence/notifications/**`, `src/infrastructure/web/notifications/**`, `src/infrastructure/web/templates/notifications/**`, `tests/**/notifications/**` |
| **audit** | `src/application/common/audit.py`, `src/infrastructure/persistence/audit/**`, `tests/**/audit/**` |
| **reporting** (pilot readiness/completion dashboard) | `src/infrastructure/persistence/reporting/queries.py`, `src/infrastructure/web/reporting/**`, `src/infrastructure/web/templates/reporting/**`, `tests/**/reporting/**` |
| **UI primitives** | `src/infrastructure/web/templates/components/**`, `src/infrastructure/web/templatetags/ui.py`, `src/infrastructure/web/static/css/components/**`, `src/infrastructure/web/static/icons/**`, `src/infrastructure/web/styleguide/**` |
| **platform / cross-cutting** (errors, middleware, logging, i18n helpers, UoW, managers) | `src/domain/common/**`, `src/application/common/unit_of_work.py`, `src/infrastructure/web/common/**`, `src/infrastructure/persistence/common/**`, `src/infrastructure/logging/**`, `src/infrastructure/web/templatetags/i18n_content.py`, `src/infrastructure/system_clock.py` |

### `shared_files` (touched by more than one concern; serialise or assign to an integrator)

| File | Why it is shared |
|------|------------------|
| `pyproject.toml`, `uv.lock` | dependencies + tool config |
| `src/config/settings/base.py` (+ `dev.py`, `test.py`, `prod.py`) | `INSTALLED_APPS`, middleware, auth settings |
| `src/config/urls.py` | root URLConf includes each context's `urls.py` |
| `src/infrastructure/container.py` | composition root wires every use case |
| `src/infrastructure/web/templates/layouts/base.html` | global header/nav, per-role menu entries |
| `src/infrastructure/web/static/css/tokens.css` | design tokens |
| `src/infrastructure/i18n/locale/ro/LC_MESSAGES/django.po`, `…/en/…/django.po` | `makemessages` regenerates the whole catalogue |
| `src/infrastructure/web/common/decorators.py` (`PUBLIC_URL_NAMES`) | public-route registry |
| `tests/conftest.py` | global role fixtures |
| `tests/integration/web/test_role_access_matrix.py` | each new route adds rows |
| `docs/architecture/design/00-system-architecture-greenfield.md` (route catalogue) | route documentation |
| `.env.example`, `README.md` | config/setup docs |
| `Dockerfile`, `.github/workflows/**` | DevOps-owned, touched by Story 1.1 and DevOps |

**Why the shared files are unavoidable:** Django needs one settings module and one root URLConf. The composition root and base layout are single by design (dependency injection and consistent navigation). gettext catalogues are generated per language, not per module. **Mitigation:** add each context's settings, URLs and container entries as **one appended block per context** (alphabetical), and run `makemessages` + `compilemessages` only at the story's end, in the integrator step.

**Migrations:** each concern owns `src/infrastructure/persistence/<ctx>/migrations/**`. Cross-concern FKs (e.g. `assessment` → `content`, `accounts`) create migration dependencies, so the plan must order `accounts` → `catalogue` → `content` → `assessment`/`progress`/`notifications`/`audit`.

---

## 17. Quality Checklist (every story, before review)

**Structure & style**
- [ ] Files are in the locations from §1 / §16; no new `utils.py`; files ≤ 400 lines, functions ≤ 30 lines
- [ ] `ruff format --check` and `ruff check` → 0 issues; `mypy` → 0 errors; `lint-imports` → all contracts kept
- [ ] No `TODO`/`FIXME`, no commented-out code, no `print()`

**Architecture**
- [ ] Writes go through a use case with `UnitOfWork`; views are thin
- [ ] Domain/application import no Django or third-party code
- [ ] New dependencies are justified in the review doc

**Security & privacy**
- [ ] Every new view has `@require_permission` (or is in `PUBLIC_URL_NAMES` with justification); the role-access matrix test is extended
- [ ] Learner-facing queries use `visible_to_learners()` and viewer scoping; out-of-scope → 404
- [ ] No `|safe`/`mark_safe` outside the renderer; no `csrf_exempt`; no PII or secrets in logs
- [ ] Audit entries written for audited actions

**i18n & UI**
- [ ] All UI strings translated (RO + EN); content forms require both languages
- [ ] Shared primitives reused or added to `components/` and the `/_styleguide/` page
- [ ] Accessibility baseline (§11.4) met

**Tests & evidence**
- [ ] Tests written first; AAA; behavioural names
- [ ] Coverage: overall ≥ 85 %, domain 100 %, application ≥ 95 %; all suites green (unit, integration, e2e)
- [ ] `makemigrations --check` clean; migrations reversible
- [ ] Route catalogue / README / `.env.example` updated if affected
- [ ] DoD evidence (Gates 1–3) pasted into `docs/stories-implemented/story-N.M-review.md`

---

## Approval

| Role | Name | Date | Status |
|------|------|------|--------|
| Stakeholder | User/project owner | 2026-10-19 | Approved |
| Technical Lead | TBD | — | Pending |
