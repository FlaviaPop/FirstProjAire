# Story 1.0 Self-Review

**Date**: 2026-10-21
**Story**: Root Tooling Seed (CYCLE-1, wave 1, Dev 1)
**Developer**: DEV Agent
**Branch**: `feature/story-1.0-root-tooling-seed` (not committed yet)

---

## What Was Implemented

- uv project (Python 3.12, Django 5.2.18) with every runtime and dev dependency from patterns §1.3 locked in `uv.lock`
- Layered `src/` package (config · domain · application · infrastructure) and all quality gates: ruff format/check, mypy (+ django-stubs), import-linter, pytest + coverage
- Split settings (base/dev/test/prod) with environment variables read only through `config/settings/env.py`; prod refuses to start without `DJANGO_SECRET_KEY`
- SQLite per ADR-004: WAL, `IMMEDIATE` transactions, 20 s timeout, `ATOMIC_REQUESTS=False`
- Custom user model `accounts.UserModel` in migration `0001` (full name, date of birth, role, preferred language; `createsuperuser` always gives ADMIN)
- Public `GET /healthz` outside the language prefix (200 / 503)
- Every `shared_files` entry created as a minimal, working stub so wave-2 branches only modify files

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `pyproject.toml`, `uv.lock`, `.python-version` | New | Project, dependencies, ruff/mypy/pytest/coverage/import-linter config |
| `.gitignore` | Modified | Python/tooling caches, `.env`, `data/`, `staticfiles/` (outside the AIRE block) |
| `.env.example`, `README.md` | New | Every env var with placeholders; setup/run/test/config/troubleshooting docs |
| `manage.py`, `src/config/wsgi.py` | New | Entry points that put `src/` on `sys.path` |
| `src/config/settings/{env,base,dev,test,prod}.py` | New | Env helpers and the settings split |
| `src/config/urls.py` | New | `/healthz` plus an empty `i18n_patterns` block |
| `src/infrastructure/persistence/accounts/{apps,managers,models}.py`, `migrations/0001_initial.py` | New | Custom user model and manager |
| `src/infrastructure/web/common/health.py` | New | Health endpoint |
| `src/infrastructure/web/common/decorators.py` | New | `PUBLIC_URL_NAMES = {"healthz"}` |
| `src/infrastructure/container.py`, `web/templatetags/ui.py`, `web/templates/layouts/base.html`, `web/static/css/tokens.css`, `i18n/locale/{ro,en}/LC_MESSAGES/django.po` | New | Shared-file stubs |
| `src/**/__init__.py` (12 packages, including `application/accounts`) | New | Package skeleton |
| `tests/conftest.py`, `tests/factories/{__init__,accounts}.py` | New | Global fixtures module, `UserFactory` |
| `tests/unit/config/test_env.py` | New | 7 tests |
| `tests/integration/web/test_healthz.py` | New | 9 tests |
| `tests/integration/web/test_role_access_matrix.py` | New | Public-route row (seeded) |
| `tests/integration/persistence/accounts/test_user_model.py` | New | 8 tests |
| `tests/integration/persistence/accounts/test_restart_persistence.py` | New | 3 subprocess tests (restart, re-migrate, prod secret) |

## Patterns Applied

| Pattern | Where Applied | Notes |
|---------|---------------|-------|
| Project layout §1.1 / layering §3 | `src/`, import-linter contracts | Both contracts kept |
| Configuration §10 | `config/settings/env.py`, `prod.py` | No `os.environ` reads outside env.py (wsgi/manage only `setdefault` the settings module) |
| SQLite config §6.1 | `base.py` `DATABASES` | Exactly as specified |
| Migrations §6.4 | `accounts/0001_initial.py` | Only first-party migration |
| Logging §9 | `health.py` | Event names with IDs only (`healthz.db_unavailable` + exception class) |
| Testing §12 | `tests/` | AAA, behavioural names, file-based test DB |

## Testing Summary

- **Unit tests**: 7, all passing
- **Integration tests**: 21, all passing (including 3 subprocess tests)
- **Coverage**: 100.00% (target 85%)

**Test output** (`uv run pytest --cov=src --cov-branch --cov-fail-under=85`, verbatim, re-captured 2026-10-21 before the review remediation. Only the per-file 100% coverage rows and environment header lines are omitted):
```
============================= test session starts ==============================
django: version: 5.2.18, settings: config.settings.test (from ini)
testpaths: tests
collected 28 items

tests/integration/persistence/accounts/test_user_model.py ........       [ 28%]
tests/integration/web/test_healthz.py .........                          [ 60%]
tests/integration/web/test_role_access_matrix.py .                       [ 64%]
tests/integration/persistence/accounts/test_restart_persistence.py ...   [ 75%]
tests/unit/config/test_env.py .......                                    [100%]

================================ tests coverage ================================
TOTAL                                                    69      0      4      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
============================== 28 passed in 0.99s ==============================
```

## DoD Evidence

### Quality gates (Step 9), run 2026-10-21

```
$ uv run ruff format --check .
35 files already formatted
$ uv run ruff check .
All checks passed!
$ uv run mypy
Success: no issues found in 37 source files
$ PYTHONPATH=src uv run lint-imports
Layers point inward KEPT
Domain is framework-free KEPT
Contracts: 2 kept, 0 broken.
$ uv run python manage.py makemigrations --check --dry-run
No changes detected
$ uv run pytest --cov=src --cov-branch --cov-fail-under=85
28 passed — Total coverage: 100.00%
```

### Manual checks (fresh `.venv` and empty `data/`)

```
$ uv sync --frozen                     → installed from uv.lock
$ manage.py migrate                    → ... Applying sessions.0001_initial... OK
$ manage.py migrate (again)            → No migrations to apply.
$ createsuperuser --noinput --username admin   → Superuser created successfully.
  role/is_staff/is_superuser/hash prefix → ADMIN True True pbkdf2_
$ curl -i localhost:8765/healthz
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: max-age=0, no-cache, no-store, must-revalidate, private
{"status": "ok", "db": "ok"}
$ curl -X POST /healthz                → 403 (CSRF; see Deviations)
$ curl /ro/healthz                     → 404
$ chmod -w data && curl -i /healthz    → HTTP/1.1 503 Service Unavailable
                                         {"status": "unavailable", "db": "error"}
--- server stopped, started again
users after restart: 1
{"status": "ok", "db": "ok"}
$ DJANGO_SETTINGS_MODULE=config.settings.prod manage.py check   (no DJANGO_SECRET_KEY)
django.core.exceptions.ImproperlyConfigured: Required environment variable DJANGO_SECRET_KEY is not set
$ render_to_string('layouts/base.html') → valid document, <html lang="ro">, tokens.css linked
```

### Gate 1 — Spec Echo

| # | Requirement | Proof |
|---|-------------|-------|
| AC1 | `uv sync --frozen` from committed lock; `.python-version` 3.12; `requires-python >=3.12,<3.13` | `.python-version:1`; `pyproject.toml:5`; manual `uv sync --frozen` on a deleted `.venv` |
| AC2 | All runtime + dev deps with §1.3 ranges | `pyproject.toml:6-28` |
| AC3 | `src/` has the 4 packages; manage/wsgi/pytest/mypy resolve `src/` | `manage.py:10`, `src/config/wsgi.py:7`, `pyproject.toml` `pythonpath`/`mypy_path`; all gates green |
| AC4 | `AUTH_USER_MODEL="accounts.UserModel"`, created in `0001`, no other first-party migration | `src/config/settings/base.py` `AUTH_USER_MODEL`; `ls migrations` → only `0001_initial.py`; `test_auth_user_model_is_custom_accounts_model` |
| AC5 | role/full_name(≤150)/date_of_birth/preferred_language(`ro` default); no first/last name; `get_full_name()` | `src/infrastructure/persistence/accounts/models.py:18-37`; `test_role_and_language_choices_are_the_canonical_values`, `test_first_and_last_name_columns_are_removed`, `test_create_user_stores_profile_fields_and_hashes_password` |
| AC6 | `create_superuser` → ADMIN/staff/superuser; `create_user` hashes the password | `managers.py:9-19`; `test_create_superuser_is_always_admin_role`, `test_createsuperuser_command_creates_admin_role`, password assertions; manual `pbkdf2_` prefix |
| AC7 | SQLite IMMEDIATE, timeout 20, WAL + synchronous NORMAL, `ATOMIC_REQUESTS=False` | `base.py` `DATABASES`; `test_sqlite_runs_in_wal_mode_with_immediate_transactions` (PRAGMA returns `wal`) |
| AC8 | base/dev/test/prod split; MD5 hasher in test only; prod requires secret + security flags; env read only via env.py | `src/config/settings/*.py`; `test_prod_settings_refuse_to_start_without_secret_key`; `os.environ` grep (Gate 2) |
| AC9 | `/healthz` 200/503 JSON, no-store, outside i18n, GET/HEAD only, in `PUBLIC_URL_NAMES` | `health.py`, `urls.py:8-10`, `decorators.py:8`; 9 tests in `test_healthz.py`; manual curl. **Non-GET in production returns 403, not 405 (accepted deviation, see below)** |
| AC10 | Every `shared_files` entry exists | existence check: 23/23 ✓ (list in Files Changed) |
| AC11 | Quality commands pass | Quality gates output above |
| AC12 | import-linter contracts with `include_external_packages=true`, kept | `pyproject.toml` `[tool.importlinter]`; `Contracts: 2 kept, 0 broken` |
| AC13 | Restart persistence against a file DB | `test_users_survive_a_process_restart` (separate processes); manual server stop/start → `users after restart: 1` |
| AC14 | `.env` and `data/` ignored; `.env.example` placeholders only | `git check-ignore -v .env data/` → `.gitignore:28`, `.gitignore:29`; `.env.example` |
| AC15 | `makemigrations --check --dry-run` clean | `No changes detected` |
| Step 1 | uv init, pin, pyproject, lock | `pyproject.toml`, `uv.lock`, `.python-version` |
| Step 2 | Package skeleton incl. `application/accounts` | 12 `__init__.py` files |
| Step 3 | env helpers per §10 | `src/config/settings/env.py`; 7 unit tests |
| Step 4 | Settings content (apps, templates, i18n, static, TZ, logging) | `base.py`; `infrastructure.web` in `INSTALLED_APPS`; `LANGUAGE_CODE="ro"`, `TIME_ZONE="Europe/Bucharest"` |
| Step 5 | User model, manager, apps label `accounts`, makemigrations | `apps.py:5`, `models.py`, `managers.py`, `0001_initial.py` |
| Step 6 | Health endpoint and root URLConf | `health.py`, `urls.py` |
| Step 7 | Shared stubs (decorators, container, ui, base.html, tokens, .po, .gitignore, .env.example, README) | files listed; README has the 8 §14 sections |
| Step 8 | conftest + `UserFactory` | `tests/conftest.py`, `tests/factories/accounts.py`; `test_user_factory_builds_a_valid_student` |
| Step 9 | Gates run and recorded | this document |
| Ref: design tokens (`08-visual-foundation.md`) | Full token set | `tokens.css`: 14 colours, 6 pill pairs, spacing, type scale, weights, line heights, radius, elevation 0–3, touch, content widths, gutter, nav height |
| Ref: architecture USER entity | username, hashed password, role, full_name, date_of_birth, preferred_language, is_active, date_joined, last_login | inherited from `AbstractUser` + new fields; Argon2id itself is Story 1.2 (out of scope) |
| Ref: patterns §9 logging | No PII; event names | `health.py` logs `healthz.db_unavailable` with the exception class only, and `healthz.data_dir_not_writable` |

AC rows: 15 of 15.

### Gate 2 — Negative-Space Check

| Rule | Check | Result |
|------|-------|--------|
| No TODO/FIXME, `csrf_exempt`, `mark_safe` or `print` in code | `grep -rnE "TODO\|FIXME\|csrf_exempt\|mark_safe\|print\(" src tests` | one hit: a `print` inside the shell command string the restart test sends to a subprocess; none in `src/` |
| Env read only via `env.py` | `grep -rn "os\.environ" src` excluding env.py/wsgi | none |
| No secrets committed | `.env`/`data/` git-ignored; only placeholder/dev/test keys, each with `noqa: S105` | ✓ |
| Domain/application framework-free | import-linter "Domain is framework-free" | KEPT |
| No other first-party migration | `ls src/infrastructure/persistence/accounts/migrations` | `0001_initial.py` only |
| `/healthz` not under `/ro`, `/en` | `test_healthz_is_not_language_prefixed[/ro,/en]` | 404 |
| Healthz sets no session and leaks no error text | `test_healthz_is_idempotent_and_sets_no_session_cookie`; `"disk I/O error" not in body` assertion | ✓ |
| Out of scope not built (login, Role enum, LocaleMiddleware, UI primitives, JSON logging, admin, Docker/CI, catalogue) | `ls src/domain` → `__init__.py` only; no `LocaleMiddleware` in `MIDDLEWARE`; no Dockerfile/.github | ✓ |
| No forbidden deps (§1.3) | `pyproject.toml` has no django-environ/DRF/Celery/Redis | ✓ |

### Gate 3 — Contract Consistency

| Producer | Consumer | Consistent? |
|----------|----------|-------------|
| `PUBLIC_URL_NAMES = {"healthz"}` | `urls.py` name `healthz`; `test_role_access_matrix` reverses each name → 200 | ✓ |
| `ROLE_CHOICES` values | Story 1.3 `Role` enum (asserted there); factory `role="STUDENT"`; manager `"ADMIN"` | ✓ |
| `REQUIRED_FIELDS` (full_name, date_of_birth) | `createsuperuser` prompts/options; test passes them | ✓ |
| `.env.example` variables | §10 table, README Configuration table, `env_*` calls in settings | ✓ all 6 present in all three |
| Healthz table in the story (200/HEAD/503×2/405/404) | tests + manual curl | ✓ except POST in production → 403 (documented deviation) |
| `tokens.css` | `08-visual-foundation.md` YAML | ✓ |

## Challenges Encountered

| Challenge | Resolution | Time Spent |
|-----------|------------|------------|
| `__all__` in `base.py` limited the star import, so dev settings lost `INSTALLED_APPS` | Removed it; `dev.py`/`prod.py` import the env helpers explicitly (also fixes mypy) | 5 min |
| ruff 0.17 formats Python blocks inside Markdown and rewrote 45 story/docs files | Reverted them with git and excluded `docs`, `SPEC`, `.claude` in `[tool.ruff]` | 5 min |
| WAL assertion is impossible with SQLite's in-memory test DB | `test.py` uses a file-based test DB (`data/test.sqlite3`) | — |
| `shell -c` in Django 5.2 prints an auto-import banner | Pass `--no-imports` in the restart test | 2 min |

## Deviations from Plan

- **AC 9: a production `POST /healthz` returns 403, not 405.** Django's CSRF middleware rejects the request before the view's `@require_safe` runs. The only way to get 405 would be `@csrf_exempt`, which patterns §13 forbids. Decided with the user on 2026-10-21: accept 403. The request is still rejected with no side effects. Both behaviours are tested (`test_healthz_view_rejects_post` → 405 without CSRF, `test_healthz_post_is_rejected_by_csrf_before_reaching_the_view` → 403).
- **`tokens.css`** adds the pill colours, line heights, content widths, gutter and nav height from `08-visual-foundation.md` that the story's snippet omitted (AC 10 requires the full token set).
- **Extra tests** beyond the story's list: HEAD, error logging, factory validity, `createsuperuser` command, canonical choices, re-migrate, prod secret.
- **`ruff` excludes `docs/`, `SPEC/` and `.claude/`.**
- **The `.po` files** are header-only and couldn't be compiled because GNU gettext isn't installed. Their syntax is checked in Story 1.4.

## Lessons Learned

1. Check HTTP method contracts against a real server: the test client disables CSRF, which hides the 403.
2. New ruff versions lint and format Markdown. Pin the source scope in `pyproject.toml` from day one.

## Next Steps

- [ ] Commit on `feature/story-1.0-root-tooling-seed` and merge to `main`. Wave-2 branches (1.1–1.5, 1.8, 2.1) start from that commit.
- [ ] Ready for code review (`aire-review-code`)
- [ ] Story 1.4 must install GNU gettext
