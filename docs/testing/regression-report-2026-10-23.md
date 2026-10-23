# Regression Test Report

**Date**: 2026-10-23
**Build**: `main` @ `f4bc6bb` (CYCLE-1 complete + review and BUG-004 remediations) vs baseline `26b4ece` (Story 1.0)
**Baseline Report**: `docs/testing/validation-report-story-1.0-2026-10-21.md` (the only validation report). The previous full-suite count from `docs/testing/regression-report-2026-10-21.md` (`26fc1c5`, 605 tests) is used as an extra comparison point.
**Tested By**: QA Agent
**Trigger**: required after the P1 fix of BUG-004 (`docs/testing/bug-triage-2026-10-23.md`)
**Environment**: local macOS, Python 3.12, Django 5.2.18, django-axes 8.3.1, django-ipware 8.0.0. Clean `.venv` rebuilt with `uv sync --frozen`; `data/` (the user's dev DB) left untouched. Manual scenarios ran on fresh scratch databases.
**BUILDID**: CYCLE-1

---

## Summary

**Overall Status**: 🟢 NO REGRESSIONS

**New Failures**: 0
**Fixed Issues**: 1 newly fixed (BUG-004, application side); BUG-001, BUG-002 and BUG-003 still hold
**Flaky Tests**: 0 (3 full runs + reversed file order + 2 e2e runs, all identical)

**Go-live condition (not a regression):** BUG-004 is fixed in the app, but PR #1's planned `AXES_PROXY_COUNT=1` still reproduces it (verified below). Production go-live needs `AXES_PROXY_COUNT=0`.

---

## Changes Since Baseline

- **Baseline `26b4ece` → `f4bc6bb`:** 65 commits. Since the previous regression run (`26fc1c5`), 42 commits touching 175 files under `src/` and `tests/` (+11,478 / −398).
- **Scope:** Stories 1.1–1.10 and 2.1–2.2 (all of CYCLE-1), code-review remediations for every story, review v2s, and today's fixes:
  - request-id trust, HSTS flags, audit retention purge (reviews 1.0, 1.1, 1.8);
  - **BUG-004**: `django-ipware`, prod reads `X-Forwarded-For`, proxy count 0.

---

## Test Suite Comparison

| Category | Baseline (Story 1.0, `26b4ece`) | Previous regression (`26fc1c5`) | Current (`f4bc6bb`) | Change vs previous |
|----------|------------------------|--------------------|-------------------|--------|
| Total tests (default run) | 30 | 605 | 1541 | +936 |
| Passed | 30 | 605 | 1541 | +936 |
| Failed | 0 | 0 | 0 | 0 |
| Skipped | 0 | 0 | 0 | 0 |
| E2E journeys (`-m e2e`) | n/a | n/a | 17 / 17 | new (Story 1.10) |
| Coverage (lines + branches) | 100% (69 stmts) | 100% (551 stmts) | **100% (1416 stmts, 200 branches)** | = |
| Domain / application floors | n/a | 100% / 100% | 100% / 100% | = |

**Baseline test survival:** 29 baseline test functions. 28 still exist and pass (30 cases with parametrization). The 1 missing one, `test_healthz_returns_503_when_data_directory_not_writable`, was **intentionally replaced** during the BUG-001 fix by `test_healthz_reports_read_only_data_directory_as_its_own_cause`, which uses a real read-only directory. This was already recorded in the previous regression report. Not a regression.

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

| Scenario | Baseline / previous | Current | Cause | Verdict |
|----------|----------|---------|-------|---------|
| TC-008 `createsuperuser` | `--email` accepted | `--email` unknown; requires `--full_name`, `--date_of_birth`; user gets role `ADMIN` | Story 1.2/1.9 user model (`REQUIRED_FIELDS = ["full_name", "date_of_birth"]`), documented in README | ✅ Intended |
| TC-021 `POST /healthz` (no CSRF) | `403 <title>Access denied</title>` | `403 <title>Acces interzis</title>`; with `Accept-Language: en`, `Access denied` | Story 1.4 i18n (`LANGUAGE_CODE = "ro"`) on the BUG-003 localized page | ✅ Intended |
| TC-025 prod `check --deploy` | `no issues (0 silenced)` | `no issues (2 silenced)` | Story 1.0 review ISS-004: HSTS `includeSubDomains`/`preload` off until the domain is final (owner decision); W005/W021 silenced only while off | ✅ Intended |
| Request id from a client | reused when valid | ignored unless `TRUST_INCOMING_REQUEST_ID` (prod default on, behind Nginx) | Story 1.1 review ISS-004 | ✅ Intended (tests re-scoped, not removed) |

---

## Fixed Issues

| ID | Test Name | Previous | Current | Notes |
|----|-----------|----------|---------|-------|
| BUG-004 | `test_client_ip_behind_proxy.py` (6) + `test_prod_security_settings.py` (3 header-order tests) | ❌ (raised and triaged today, P1) | ✅ Pass | Real server on `config.settings.prod`: another client signs in `302 /en/`, attacker `429`, real IPs in axes and audit (below) |
| BUG-001 | `test_healthz.py::test_healthz_reports_read_only_data_directory_as_its_own_cause` | ✅ (fixed `26fc1c5`) | ✅ Pass | Real server TC-020: `503`, log `healthz.data_dir_not_writable` |
| BUG-002 | `test_healthz.py::test_healthz_returns_503_not_500_when_session_cookie_present_and_db_down` | ✅ | ✅ Pass | still fixed |
| BUG-003 | `test_csrf_failure.py` (4) | ✅ | ✅ Pass | Real server TC-021: localized 403 page |

---

## Flaky Tests

| Test ID | Test Name | Pass Rate | Recommendation |
|---------|-----------|-----------|----------------|
| — | None | 100% (6 suite executions) | — |

---

## Coverage Changes

**New Code Coverage**: 100% (lines + branches), unchanged in percentage while the codebase grew from 551 to 1416 statements.

**Areas with Improved Coverage**: n/a (already 100%). New modules are at 100%: `persistence/audit/retention.py` (34/34, 4/4 branches), the `purge_audit_log` command (12/12).

**Areas with Decreased Coverage**: none. The baseline's own Story 1.0 files remain at 100%:
```
src/infrastructure/persistence/accounts/models.py   46  0  2  0  100%
src/infrastructure/web/common/decorators.py         35  0  8  0  100%
src/infrastructure/web/common/health.py             27  0  4  0  100%
src/infrastructure/web/common/middleware.py         56  0  4  0  100%
```

---

## Manual Scenario Re-run (Story 1.0 test plan, real `runserver`, fresh DB)

| Scenario | Result | Evidence |
|----------|--------|----------|
| TC-001 `uv sync --frozen` on a deleted `.venv` | ✅ | installs from the lock, including `django-ipware 8.0.0` |
| TC-015 migrate ×2 | ✅ | `Applying sessions.0001_initial... OK` / `No migrations to apply.` |
| TC-008 `createsuperuser` | ✅ (expected change) | `Superuser created successfully.`; `staff True, superuser True, role ADMIN` |
| TC-009 password never stored raw | ✅ | hash `argon2`, `raw stored: False` |
| TC-016 `GET /healthz` | ✅ | `200`, `Cache-Control: max-age=0, no-cache, no-store, must-revalidate, private`, `{"status": "ok", "db": "ok"}` |
| TC-018 `HEAD /healthz` | ✅ | `200`, body 0 bytes |
| TC-021 real `POST /healthz` | ✅ (expected change) | `403 <title>Acces interzis</title>`; EN: `Access denied` |
| TC-023 `/ro/healthz`, `/en/healthz` | ✅ | `404`, `404` |
| TC-020 read-only data dir | ✅ | `503 {"status": "unavailable", "db": "error"}`, log `healthz.data_dir_not_writable`; restored → `200` |
| TC-014 restart persistence | ✅ | `users after restart: 1` |
| TC-010 prod without secret | ✅ | `ImproperlyConfigured: Required environment variable DJANGO_SECRET_KEY is not set` |
| TC-011 prod empty hosts | ✅ | `ImproperlyConfigured: DJANGO_ALLOWED_HOSTS must list at least one host` |
| TC-025 prod valid config | ✅ (expected change) | `check --deploy`: `System check identified no issues (2 silenced).` |
| TC-030 secrets / env reads | ✅ | `.env`, `data/`, `.claude/worktrees/`, `test-results/` ignored; only `wsgi.py`'s `setdefault` outside `env.py`; no hard-coded secrets in `src/` (dev key excluded) |

### BUG-004 re-validation (real server, `config.settings.prod`, Nginx simulated)

The script sends `X-Forwarded-For` with one value and `X-Forwarded-Proto: https`.

```
===== prod, defaults (DJANGO_TRUST_X_FORWARDED_FOR unset -> true, AXES_PROXY_COUNT unset -> 0)
step 5: attacker 203.0.113.10 wrong password   -> 429
step 6: student 198.51.100.20 CORRECT password -> 302 /en/
step 7: attacker 203.0.113.10 CORRECT password -> 429
   1 axes ana '203.0.113.10' x5
   6 audit auth.login_failed '203.0.113.10' | 2 audit auth.lockout '203.0.113.10' | 1 audit auth.login '198.51.100.20'
ERROR lines: 0
===== prod, AXES_PROXY_COUNT=1 (the value PR #1 currently plans)
step 6: student 198.51.100.20 CORRECT password -> 429       <- BUG-004 behaviour returns
   1 axes ana NULL x5 | 7 audit auth.login_failed NULL | 3 audit auth.lockout NULL
ERROR lines: 0
```

---

## Recommendations

1. ✅ **No regressions.** The CYCLE-1 build sign-off is clear from a regression standpoint.
2. 🟠 **Go-live condition (DevOps, PR #1):** deploy `AXES_PROXY_COUNT=0` (not `1`), fix the `proxy_headers.inc:3` comment, document `DJANGO_TRUST_X_FORWARDED_FOR`. With `1`, BUG-004 returns, as verified above. Keep BUG-004 in the `status.md` Blockers table until then.
3. Repeat the BUG-004 scenario on staging once PR #1 is deployed. Real Nginx is the only part simulated here.
4. This report is the new regression baseline for CYCLE-2.

---

## Evidence

```
== clean environment
$ rm -rf .venv && uv sync --frozen        -> + django-ipware==8.0.0 + python-ipware==4.1.1 ... (lock honoured)
== run 1 (with coverage)
TOTAL  1416  0  200  0  100%
Required test coverage of 85% reached. Total coverage: 100.00%
1541 passed, 17 deselected in 17.83s
== run 2
1541 passed, 17 deselected in 13.00s
== run 3
1541 passed, 17 deselected in 13.01s
== reversed file order
1541 passed in 12.90s
== domain / application floors
domain       TOTAL   79  0   8  0  100%
application  TOTAL  142  0  28  0  100%
== e2e x2
17 passed, 1541 deselected in 9.49s
17 passed, 1541 deselected in 7.40s
== baseline tests (28 surviving functions) on current code
30 passed in 1.62s
== gates
194 files already formatted
All checks passed!
Success: no issues found in 119 source files
Contracts: 2 kept, 0 broken.
No changes detected
```

Baseline test inventory: derived from `git show 26b4ece:<test files>` (29 functions) and compared with `pytest --collect-only` on `f4bc6bb` (828 functions, 1558 cases including 17 e2e). Only the intentionally replaced read-only-directory test is missing.
