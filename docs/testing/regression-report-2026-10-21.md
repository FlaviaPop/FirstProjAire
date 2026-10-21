# Regression Test Report

**Date**: 2026-10-21
**Build**: `feature/wave-2-dev-1` @ `26fc1c5` (Stories 1.0, 1.1, 1.2, 1.3, 1.5, 1.8, 2.1 + review/triage remediations) vs `26b4ece` (Story 1.0 only)
**Baseline**: `docs/testing/validation-report-story-1.0-2026-10-21.md`
**Tested By**: QA Agent
**Environment**: local macOS, uv 0.13.1, Python 3.12.15, Django 5.2.18; `.venv` and `data/` deleted and rebuilt with `uv sync --frozen` before the run

---

## Summary

**Overall Status**: 🟢 NO REGRESSIONS

**New Failures**: 0
**Fixed Issues**: 1 baseline bug (BUG-001), plus BUG-002 and BUG-003 found and fixed since the baseline
**Flaky Tests**: 0 (4 full runs, including one in reverse file order)

Everything Story 1.0 delivered still works on the integrated code: all surviving baseline tests pass, all 15 re-run manual scenarios pass, and every quality gate is green. Three behaviours differ from the baseline, and all are intended changes from later stories or bug fixes (see Expected Changes).

---

## Test Suite Comparison

| Category | Previous Build (`26b4ece`) | Current Build (`26fc1c5`) | Change |
|----------|----------------|---------------|--------|
| Total Tests | 30 | 605 | +575 (stories 1.1–1.3, 1.5, 1.8, 2.1 + remediation tests) |
| Passed | 30 | 605 | +575 |
| Failed | 0 | 0 | 0 |
| Skipped | 0 | 0 | 0 |
| Coverage (lines + branches) | 100% (69 stmts, 4 branches) | 100% (551 stmts, 56 branches) | 0 pp |
| Domain coverage | n/a (empty) | 100% | — |
| Application coverage | n/a (empty) | 100% | — |
| Gates (ruff, mypy, import-linter, makemigrations) | all clean | all clean | — |

### Baseline tests on the current build

- **Baseline inventory**: 29 test functions (30 cases) at `26b4ece`
- **Still present**: 28 functions, now **30 cases, all passing** (`30 passed, 8 deselected`). `test_public_routes_are_reachable_anonymously` has one more case because `PUBLIC_URL_NAMES` now also contains `accounts:login` (Story 1.2).
- **Removed (expected)**: `test_healthz_returns_503_when_data_directory_not_writable`. It was intentionally replaced during the BUG-001 fix by `test_healthz_reports_read_only_data_directory_as_its_own_cause`, which uses a real read-only directory instead of patching `os.access`. Not a regression.

---

## New Failures (Regressions)

| Test ID | Test Name | Category | Previous | Current | Severity | Investigation |
|---------|-----------|----------|----------|---------|----------|---------------|
| — | None | — | — | — | — | — |

---

## Regression Details

None.

---

## Expected Changes (classified, not regressions)

| Baseline scenario | Baseline result | Current result | Cause | Classification |
|-------------------|-----------------|----------------|-------|----------------|
| TC-009 password storage | hash prefix `pbkdf2_sha256` | hash prefix `argon2` | Story 1.2 configures Argon2id first in `PASSWORD_HASHERS` (architecture: `password_hash "Argon2id"`) | ✅ Intended improvement |
| TC-021 real `POST /healthz` | `403` (Django default page) | `403` with `<title>Access denied</title>` | BUG-003 fix (`CSRF_FAILURE_VIEW`) | ✅ Intended (status unchanged, page improved) |
| TC-020 read-only data dir | `503`, logged `healthz.db_unavailable` (BUG-001) | `503`, logged `healthz.data_dir_not_writable` | BUG-001 fix | ✅ Fixed |
| TC-027 shared files | 23 owned by 1.0 | 24 present (adds `common/errors.py`, created by Story 1.1 as planned) | dependency graph | ✅ As planned |

---

## Fixed Issues

| Test ID | Test Name | Previous | Current | Notes |
|---------|-----------|----------|---------|-------|
| BUG-001 | `/healthz` logs wrong cause for read-only dir | ❌ open (🟢 P3) | ✅ fixed | `test_healthz.py::test_healthz_reports_read_only_data_directory_as_its_own_cause`; real server logs `healthz.data_dir_not_writable` |
| BUG-002* | `/healthz` 500 with session cookie | (not reachable at baseline: no login existed) | ✅ fixed | `test_healthz.py::test_healthz_returns_503_not_500_when_session_cookie_present_and_db_down` |
| BUG-003* | CSRF failure page | (Django default page at baseline) | ✅ fixed | `tests/integration/web/common/test_csrf_failure.py` (3) |

\* Found after the baseline (`bug-triage-2026-10-21-2.md`) and fixed in `26fc1c5`.

---

## Flaky Tests

| Test ID | Test Name | Pass Rate | Recommendation |
|---------|-----------|-----------|----------------|
| — | None | 605/605 in 4/4 runs | — |

Order dependence was specifically checked: one full run used reverse file order (`605 passed`). The language-leak fix (`tests/conftest.py::_reset_active_language`) removed the only known order dependence.

---

## Coverage Changes

**New Code Coverage**: 100% (+0 pp from previous)

**Areas with Improved Coverage**:
- `src/domain/*`: empty → 100% (Story 1.3 roles/permissions/policy; Story 1.1 errors/clock/language)
- `src/application/*`: empty → 100% (Story 1.8 audit ports + use case)

**Areas with Decreased Coverage**:
- None. Story 1.0's own files (`health.py`, `decorators.py`, `persistence/accounts/*`) remain at 100% statements and branches.

---

## Manual Scenario Re-run (Story 1.0 test plan, real `runserver`, fresh DB)

| Scenario | Result | Evidence |
|----------|--------|----------|
| TC-001 `uv sync --frozen` on a deleted `.venv` | ✅ | installs from lock |
| TC-015 migrate ×2 | ✅ | `Applying sessions.0001_initial... OK` / `No migrations to apply.` |
| TC-008 `createsuperuser` | ✅ | `ADMIN True True` |
| TC-009 password never stored raw | ✅ | `raw stored: False`, hash `argon2` (expected change) |
| TC-016 `GET /healthz` | ✅ | `200`, `no-store`, `{"status": "ok", "db": "ok"}` |
| TC-018 `HEAD /healthz` | ✅ | `200 body=0` |
| TC-021 real `POST /healthz` | ✅ | `403 <title>Access denied</title>` (expected change) |
| TC-023 `/ro/healthz`, `/en/healthz` | ✅ | `404`, `404` |
| TC-020 read-only data dir | ✅ | `503`, `healthz.data_dir_not_writable` (BUG-001 fixed) |
| TC-014 restart persistence | ✅ | `users after restart: 1`, health `ok` |
| TC-010 prod without secret | ✅ | `ImproperlyConfigured: Required environment variable DJANGO_SECRET_KEY is not set` |
| TC-011 prod empty hosts | ✅ | `ImproperlyConfigured: DJANGO_ALLOWED_HOSTS must list at least one host` |
| TC-025 prod valid config | ✅ | `System check identified no issues (0 silenced).` |
| TC-027 shared files | ✅ | 24 present, none missing |
| TC-030 secrets / env reads | ✅ | `.env`, `data/`, `.claude/worktrees/` ignored; only `wsgi.py`'s `setdefault` outside `env.py` |

---

## Recommendations

1. ✅ No action required for regressions. The release path for the wave-2 integration branch is clear from a regression standpoint.
2. This report is the new regression baseline for `feature/wave-2-dev-1`. For the next comparison (after Story 1.4), consider an **Epic 1 test plan + validation** (`aire-qa-test-plan` epic 1 → `aire-qa-validate`), so the baseline covers stories 1.1–1.8 explicitly and not only Story 1.0.
3. Still-open, non-regression items: Story 1.0 ISS-004 (HSTS → DevOps), Story 1.3 ISS-004 (DEBUG-only URL walk → Story 1.6), `/en/…` URLs needing `LocaleMiddleware` (Story 1.4).

---

## Evidence

```
== clean environment
$ rm -rf .venv data && uv sync --frozen
== run 1 (with coverage)
TOTAL                                                     551      0     56      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
605 passed in 6.57s
== run 2
605 passed in 5.12s
== run 3
605 passed in 5.05s
== random order (reverse)
605 passed in 5.12s
== baseline tests (28 surviving functions) on current code
30 passed, 8 deselected in 1.16s
== gates
114 files already formatted
All checks passed!
Success: no issues found in 86 source files
Contracts: 2 kept, 0 broken.
No changes detected
domain       TOTAL  79 0 8 0 100%
application  TOTAL  30 0 0 0 100%
== coverage of Story 1.0 files
src/infrastructure/persistence/accounts/models.py        23      0      0      0   100%
src/infrastructure/web/common/decorators.py              35      0      8      0   100%
src/infrastructure/web/common/health.py                  27      0      4      0   100%
TOTAL                                                   108      0     14      0   100%
```
Baseline test inventory: derived from `git show 26b4ece:<test files>` (29 functions) and compared with `pytest --collect-only` on `26fc1c5` (339 functions); only the intentionally replaced read-only-dir test is missing.
