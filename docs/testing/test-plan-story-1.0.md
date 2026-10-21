# Test Plan - Story 1.0: Root Tooling Seed

**Date**: 2026-10-21
**Author**: QA Agent
**Story file**: `docs/plans/stories/epic-1-story-1.0-Root-Tooling-Seed.md`
**Build**: CYCLE-1, wave 1 · branch `feature/story-1.0-root-tooling-seed`
**QA group**: Epic 1 · Group 1 (1.0 + 1.1 + 1.8). This plan covers only the 1.0 part. The 404/500 pages, request id and audit checks belong to 1.1 and 1.8.
**Next workflow**: `aire-qa-validate` (story 1.0)

---

## Scope

**Coverage**: Story 1.0, Root Tooling Seed

**In Scope**:
- Project install and start-up from the lock file on Python 3.12
- User account storage: full name, date of birth, role, preferred language, hashed password, first admin via `createsuperuser`
- SQLite configuration (WAL, `IMMEDIATE`, timeout 20 s) and data persistence across restarts
- `GET /healthz` behaviour (200, 503, HEAD, non-GET, no language prefix, no session, no-store)
- Settings safety: prod requires `DJANGO_SECRET_KEY` and a non-empty `DJANGO_ALLOWED_HOSTS`; no secrets committed
- Quality gates: ruff format/check, mypy, import-linter, `makemigrations --check`, pytest coverage ≥85%
- Existence of every `shared_files` stub, and that the stubs are usable (template renders, tag library loads)

**Out of Scope** (owned by later stories, per the story's OUT list):
- Login/logout, Argon2, lockout, sessions (1.2) · RBAC and `@require_permission` (1.3) · language switching and compiled translations (1.4; GNU gettext isn't installed yet) · UI primitives/styleguide (1.5/1.6) · layout/top bar (1.7) · JSON logging, request id, 404/500 pages (1.1) · audit log (1.8) · Django admin (1.9) · Docker/CI (DevOps) · catalogue/content models
- Known open review items: ISS-004 (HSTS subdomains/preload → DevOps) and ISS-005 (dev log level → 1.1). Not tested here.

---

## Requirements Traceability

| Requirement ID | Source | Description | Test Scenarios |
|----------------|--------|-------------|----------------|
| REQ-TC-PY | requirements.md · Technical Constraints | Python application | TC-001, TC-002 |
| REQ-NFR-PERSIST | requirements.md · NFR Persistence; Technical Constraints · Data storage | Account data survives application restarts; persistent (not in-memory) database | TC-013, TC-014, TC-015 |
| REQ-USER-DATA | requirements.md · Roles & Permissions AC "Store user name and date of birth" | User name and date of birth stored | TC-005, TC-006 |
| REQ-AUTH-ADMIN | requirements.md · "Admin-managed username/password accounts" | Username/password accounts; passwords never stored readable; first admin creatable | TC-007, TC-008, TC-009 |
| REQ-LANG | requirements.md · NFR Language | Romanian and English. In this story only `preferred_language` (`ro` default, `en`) is stored | TC-006 |
| AC1 | Story 1.0 | `uv sync --frozen` from lock; Python 3.12 pinned; `requires-python >=3.12,<3.13` | TC-001, TC-002 |
| AC2 | Story 1.0 | All runtime and dev dependencies declared with patterns §1.3 ranges | TC-003 |
| AC3 | Story 1.0 | `src/` layout; manage/wsgi/pytest/mypy resolve `src/` | TC-004, TC-026 |
| AC4 | Story 1.0 | `AUTH_USER_MODEL = accounts.UserModel` in migration `0001`; no other first-party migration | TC-005, TC-029 |
| AC5 | Story 1.0 | role / full_name (≤150) / date_of_birth / preferred_language; no first/last name; `get_full_name()` | TC-005, TC-006 |
| AC6 | Story 1.0 | `create_superuser` → ADMIN + staff + superuser; `create_user` hashes the password | TC-007, TC-008, TC-009 |
| AC7 | Story 1.0 | SQLite IMMEDIATE, timeout 20, WAL + synchronous NORMAL, `ATOMIC_REQUESTS=False` | TC-012 |
| AC8 | Story 1.0 | Settings split; prod requires secret + security flags; env read only via `env.py` | TC-010, TC-011, TC-024, TC-025, TC-030 |
| AC9 | Story 1.0 (amended 2026-10-21) | `/healthz` 200/503, no-store, GET/HEAD only (real POST → 403 CSRF; view guard → 405), not language-prefixed, in `PUBLIC_URL_NAMES` | TC-016 – TC-023 |
| AC10 | Story 1.0 | Every `shared_files` entry exists as a working stub | TC-027, TC-028 |
| AC11 | Story 1.0 | Quality commands pass | TC-026 |
| AC12 | Story 1.0 | import-linter contracts configured and kept | TC-026 |
| AC13 | Story 1.0 | Restart persistence against a file-based DB | TC-013, TC-014 |
| AC14 | Story 1.0 | `.env`/`data/` ignored; `.env.example` placeholders only | TC-030, TC-031 |
| AC15 | Story 1.0 | `makemigrations --check --dry-run` clean | TC-029 |

Every AC (15/15) and every requirement from `requirements.md` in scope maps to at least one scenario.

---

## Test Categories

### Unit Tests (automated: `tests/unit/config/test_env.py`, 7 tests)
- `env_str` / `env_list` / `env_path`: required, default, override, empty-item stripping

### Integration Tests (automated, 23 tests)
- `tests/integration/persistence/accounts/test_user_model.py` (8): model, manager, `createsuperuser` command, choices, columns, factory, SQLite pragmas
- `tests/integration/web/test_healthz.py` (9): 200, idempotent/no cookie, HEAD, 503 ×2 with ERROR logs, POST 405 (view) / 403 (CSRF), no `/ro` `/en` prefix
- `tests/integration/web/test_role_access_matrix.py` (1): every `PUBLIC_URL_NAMES` route reachable anonymously
- `tests/integration/persistence/accounts/test_restart_persistence.py` (5, marker `slow`): separate-process restart, re-migrate, prod start-up refusals and positive control

### Manual / Exploratory (QA-executed against a running server)
- Fresh clone/install, migrate, `createsuperuser`, `runserver`, `curl` probes, read-only data dir, stop/start persistence, prod `check`

### E2E Tests
- Not applicable. No UI exists yet. The Playwright journeys start in 1.10.

---

## Test Scenarios

| ID | Category | Scenario | Expected Result | Priority |
|----|----------|----------|-----------------|----------|
| TC-001 | Manual | Delete `.venv`; run `uv sync --frozen` | Installs from `uv.lock` without resolving; exit 0 | High |
| TC-002 | Manual | Inspect `.python-version`, `pyproject.toml`; run `uv run python --version` | `3.12`; `requires-python = ">=3.12,<3.13"`; Python 3.12.x | High |
| TC-003 | Manual (inspection) | Compare `pyproject.toml` dependencies with patterns §1.3 | All 8 runtime + 9 dev packages present with the listed ranges; none of the forbidden packages | Medium |
| TC-004 | Manual (inspection) | List `src/` | `config`, `domain`, `application`, `infrastructure` packages exist | Medium |
| TC-005 | Integration | `test_auth_user_model_is_custom_accounts_model`, `test_first_and_last_name_columns_are_removed` | Custom model, table `accounts_user`; profile columns present; no `first_name`/`last_name` | High |
| TC-006 | Integration | `test_create_user_stores_profile_fields_and_hashes_password`, `test_role_and_language_choices_are_the_canonical_values` | Name, DOB, role stored; language defaults to `ro`; choices exactly STUDENT/TEACHER/PARENT/ADMIN and ro/en; `full_name` max 150 | High |
| TC-007 | Integration | `create_superuser(..., role="STUDENT")` | Role forced to ADMIN; `is_staff` and `is_superuser` True | High |
| TC-008 | Integration + Manual | `createsuperuser` command (non-interactive in tests; interactive prompts by hand) | Prompts for username, full name, date of birth, password; user saved as ADMIN | High |
| TC-009 | Integration + Manual | Inspect stored password after `create_user` / `createsuperuser` | Stored value ≠ raw password; `check_password` True; hash has an algorithm prefix | Critical |
| TC-010 | Integration | Prod settings without `DJANGO_SECRET_KEY` (`manage.py check`) | Non-zero exit; `ImproperlyConfigured: Required environment variable DJANGO_SECRET_KEY is not set` | Critical |
| TC-011 | Integration | Prod settings with `DJANGO_ALLOWED_HOSTS=" , "` | Non-zero exit; "DJANGO_ALLOWED_HOSTS must list at least one host" | High |
| TC-012 | Integration | `PRAGMA journal_mode`; inspect DB options | `wal`; `transaction_mode=IMMEDIATE`; `timeout=20`; `ATOMIC_REQUESTS=False` | High |
| TC-013 | Integration | Migrate → create user → count, each in a separate process on one file DB | Count = 1; DB file exists | Critical |
| TC-014 | Manual | `runserver`, create admin, stop server, start again, count users, `curl /healthz` | Count still 1; health 200 | Critical |
| TC-015 | Integration + Manual | Run `migrate` twice | Second run: "No migrations to apply." | Medium |
| TC-016 | Integration + Manual | `GET /healthz` with DB reachable | `200`, body `{"status": "ok", "db": "ok"}`, `Cache-Control` contains `no-store` | Critical |
| TC-017 | Integration | Two consecutive `GET /healthz` | Identical bodies; no `sessionid` cookie | Medium |
| TC-018 | Integration | `HEAD /healthz` | `200`, empty body | Medium |
| TC-019 | Integration | `GET /healthz` when `SELECT 1` raises `DatabaseError` | `503 {"status": "unavailable", "db": "error"}`; error text not in body; ERROR log `healthz.db_unavailable` | Critical |
| TC-020 | Integration + Manual | `GET /healthz` when the data directory is read-only (`chmod -w data/`; restore afterwards) | `503` with the unavailable body; ERROR log `healthz.data_dir_not_writable` | High |
| TC-021 | Integration + Manual | `POST /healthz` through a real request (curl / CSRF-enforcing client) | `403` (CSRF), no side effects | High |
| TC-022 | Integration | `POST /healthz` with CSRF checks off (view guard) | `405 Method Not Allowed` | Medium |
| TC-023 | Integration + Manual | `GET /ro/healthz`, `GET /en/healthz` | `404` both | Medium |
| TC-024 | Manual (inspection) | Read `prod.py` | `DEBUG=False`, `SECURE_SSL_REDIRECT`, HSTS 31536000, secure session/CSRF cookies, proxy SSL header | High |
| TC-025 | Integration | Prod settings with a secret key and a host (positive control) | `manage.py check` exits 0 | High |
| TC-026 | Manual (commands) | Run the 5 gate commands plus pytest with coverage | ruff format/check 0 issues; mypy 0 errors; import-linter 2 kept / 0 broken; coverage ≥85% and all tests pass | Critical |
| TC-027 | Manual (inspection) | Check every `shared_files` path from `docs/plans/dependency-graph.yml` that 1.0 owns | All 23 exist | High |
| TC-028 | Manual | Render `layouts/base.html`; `{% load ui %}`; validate both `.po` headers | Valid HTML with `lang="ro"` and the `tokens.css` link; tag library loads; `.po` headers have `Language`, UTF-8 charset | Medium |
| TC-029 | Manual (commands) | `makemigrations --check --dry-run`; list first-party migrations | "No changes detected"; only `accounts/0001_initial.py` | High |
| TC-030 | Manual (security) | `git check-ignore -v .env data/`; grep `src/` for `os.environ` outside `env.py`; scan for real secrets | Both ignored; no stray env reads; only documented dev/test placeholder keys | Critical |
| TC-031 | Manual (inspection) | Read `.env.example` | All 6 §10 variables with placeholders; no real values | Medium |

---

## Test Data Requirements

- **Valid users**: student `ana` / `pilot-pass-123` / "Ana Pop" / 2018-03-02; admin `root` / `x-strong-pass-9` / "Admin One" / 1990-01-01; `UserFactory` defaults (STUDENT, `ro`, DOB 2018-05-01)
- **Invalid / adversarial**: `create_superuser` called with `role="STUDENT"` (must be overridden); `DJANGO_ALLOWED_HOSTS=" , "`; missing `DJANGO_SECRET_KEY`; `POST` to a GET-only endpoint; language-prefixed health URL
- **Edge**: `env_list` input `" a.ro, ,b.ro "`; `full_name` at the 150-character limit (via model metadata); a read-only data directory; simulated `DatabaseError`
- Passwords in this plan are test-only values. Never reuse them anywhere real.

---

## Environment Requirements

- **Local QA machine**: macOS, uv 0.13.1, Python 3.12.15 (uv-managed), repository on `feature/story-1.0-root-tooling-seed`
- **Clean state before manual runs**: delete `.venv/` and `data/`, then `uv sync --frozen`
- **Settings**: `config.settings.test` for pytest (file-based `data/test.sqlite3`); `config.settings.dev` for manual server runs (`data/db.sqlite3`); `config.settings.prod` for start-up refusal checks (with `DATABASE_PATH` pointing to a temp file)
- **Server**: `uv run python manage.py runserver 8765 --noreload`; probes with `curl`
- **Not needed**: browsers/Playwright, GNU gettext, Docker

---

## Quality Gates

| Gate | Target | Required |
|------|--------|----------|
| Unit + integration tests | 100% passing (currently 30) | Yes |
| Coverage (`--cov=src --cov-branch`) | ≥85% overall | Yes |
| Lint / format | `ruff format --check` and `ruff check` 0 issues | Yes |
| Types | `mypy` 0 errors | Yes |
| Architecture | import-linter 2/2 contracts kept | Yes |
| Migrations | `makemigrations --check --dry-run` clean | Yes |
| Critical / High bugs | 0 open | Yes |
| Secrets | none committed; `.env`/`data/` ignored | Yes |
| Requirements traceability | 15/15 AC + 5 requirement rows have passing evidence | Yes |
| Performance | No numeric target in `requirements.md` (TBD). Not gated | No |

---

## Schedule

- Test planning: 2026-10-21 (this document)
- Test implementation: done. Automated tests delivered with Story 1.0 and its remediation (30 tests)
- Test execution: next, via `aire-qa-validate` (story 1.0)
- Results reporting: `docs/testing/validation-report-story-1.0-[YYYY-MM-DD].md`. This becomes the baseline for `aire-qa-regression`
