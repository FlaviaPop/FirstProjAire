# Validation Report - Story 1.0: Root Tooling Seed

**Date**: 2026-10-21
**Tested By**: QA Agent
**Scope**: Story 1.0, Root Tooling Seed (Epic 1 · QA Group 1, story-1.0 part only)
**Test Plan Used**: `docs/testing/test-plan-story-1.0.md`
**Environment**: Dev (local macOS, uv 0.13.1, Python 3.12.15, Django 5.2.18); clean `.venv` and `data/` before execution
**Code Under Test**: commit `26b4ece` on `feature/story-1.0-root-tooling-seed` (working tree clean)

---

## Executive Summary

**Overall Status**: 🟢 PASS

**Summary**: All 31 test-plan scenarios were executed against commit `26b4ece`. 30 automated tests pass (7 unit, 23 integration) at 100% line and branch coverage, stable across 4 consecutive runs. Every quality gate passes, and all 15 acceptance criteria plus the 5 in-scope requirements have passing evidence. One 🟢 Low issue was found: with a read-only data directory the health check correctly returns 503, but it logs the wrong cause.

**Recommendation**:
- [ ] ✅ READY FOR RELEASE
- [x] ⚠️ READY WITH MINOR ISSUES (documented below). Ready to merge to `main` for wave 2. BUG-001 doesn't block.
- [ ] ❌ NOT READY - CRITICAL ISSUES MUST BE FIXED
- [ ] 🚫 BLOCKED

---

## Requirements Coverage

| Requirement ID | Description | Test Status | Evidence | Notes |
|----------------|-------------|-------------|----------|-------|
| REQ-TC-PY | Python application | ✅ Pass | TC-001, TC-002 | Python 3.12.15 |
| REQ-NFR-PERSIST | Account data survives restarts; persistent DB | ✅ Pass | TC-013 (automated), TC-014 (manual: `users after restart: 1`) | File-based SQLite |
| REQ-USER-DATA | Store user name and date of birth | ✅ Pass | TC-005, TC-006; manual `QA Admin 1990-01-01` | - |
| REQ-AUTH-ADMIN | Username/password accounts; first admin; passwords not readable | ✅ Pass | TC-007, TC-008, TC-009 (`raw password stored: False`, `pbkdf2_sha256`) | Argon2id arrives with Story 1.2 (out of scope) |
| REQ-LANG | `preferred_language` stored, `ro` default | ✅ Pass | TC-006; manual shows `ro` | UI switching is Story 1.4 |
| AC1 | `uv sync --frozen`; Python 3.12 pinned | ✅ Pass | TC-001 exit 0; TC-002 | - |
| AC2 | All dependencies with §1.3 ranges | ✅ Pass | TC-003 (8 runtime + 9 dev; forbidden: none) | - |
| AC3 | `src/` layout resolved by all tools | ✅ Pass | TC-004; TC-026 | - |
| AC4 | `AUTH_USER_MODEL` in `0001`, no other first-party migration | ✅ Pass | TC-005; TC-029 (only `accounts/0001_initial.py`) | - |
| AC5 | Profile fields; no first/last name; `get_full_name()` | ✅ Pass | TC-005, TC-006 | - |
| AC6 | Superuser always ADMIN; passwords hashed | ✅ Pass | TC-007 – TC-009 | - |
| AC7 | WAL, IMMEDIATE, timeout 20, `ATOMIC_REQUESTS=False` | ✅ Pass | TC-012 | - |
| AC8 | Settings split; prod secret required; env only via `env.py` | ✅ Pass | TC-010, TC-011, TC-024, TC-025, TC-030 | - |
| AC9 | `/healthz` contract (amended 2026-10-21) | ✅ Pass | TC-016 – TC-023 | See BUG-001 (log wording only) |
| AC10 | All `shared_files` stubs exist and work | ✅ Pass | TC-027 (23/23), TC-028 | - |
| AC11 | Quality commands pass | ✅ Pass | TC-026 | - |
| AC12 | import-linter contracts kept | ✅ Pass | TC-026 (2 kept, 0 broken) | - |
| AC13 | Restart persistence (file DB) | ✅ Pass | TC-013, TC-014 | - |
| AC14 | `.env`/`data/` ignored; `.env.example` placeholders | ✅ Pass | TC-030, TC-031 | - |
| AC15 | `makemigrations --check` clean | ✅ Pass | TC-029 | - |

**Coverage Summary**:
- Total Requirements: 20 (15 AC + 5 requirements.md rows)
- Fully Covered: 20
- Partially Covered: 0
- Not Covered: 0
- Coverage %: 100%

---

## Test Execution Summary

### Unit Tests
- Total: 7 | Passed: 7 (100%) | Failed: 0 | Skipped: 0
- Evidence: `uv run pytest tests/unit -v` → `7 passed in 0.07s`

### Integration Tests
- Total: 23 | Passed: 23 (100%) | Failed: 0 | Skipped: 0
- Evidence: `uv run pytest tests/integration -v` → `23 passed in 1.04s`

### Full Suite + Coverage
- Total: 30 | Passed: 30 | Coverage: **100.00%** (69 statements, 4 branches, 0 missed)
- Stability: 4 consecutive full runs, all `30 passed`. No flaky tests

### E2E Tests
- Not applicable. No UI in this story (Playwright journeys start in Story 1.10)

### Manual Scenarios
- 15 manual / inspection scenarios executed (TC-001 – TC-004, TC-008, TC-009, TC-014 – TC-016, TC-018, TC-020, TC-021, TC-023, TC-024, TC-026 – TC-031): all pass. TC-020 passes with a log-wording note (BUG-001)

---

## Quality Gate Status

| Quality Gate | Target | Actual | Status | Notes |
|--------------|--------|--------|--------|-------|
| Unit Test Coverage | ≥85% | 100% | ✅ | lines + branches |
| Integration Tests | 100% pass | 100% (23/23) | ✅ | - |
| Critical Bugs | 0 | 0 | ✅ | - |
| High Bugs | 0 | 0 | ✅ | - |
| Lint / Format | 0 issues | 0 | ✅ | ruff format + check |
| Types | 0 errors | 0 | ✅ | mypy, 37 files |
| Architecture | 2/2 contracts | 2 kept, 0 broken | ✅ | import-linter |
| Migrations | clean | No changes detected | ✅ | - |
| Security Scan | No critical/high | No secrets; env reads contained; prod refuses missing secret / empty hosts | ✅ | Manual scan. `check --deploy` HSTS W005/W021 are known review item ISS-004 (deferred to DevOps) |
| Performance | No target defined | n/a | — | requirements.md: TBD |

**Overall Quality Gate**: ✅ PASSED

---

## Functional Testing Results

### Happy Path Scenarios
- [x] ✅ TC-001 Fresh install from lock (`uv sync --frozen`, exit 0) - PASS
- [x] ✅ TC-015 `migrate` on empty DB, then "No migrations to apply." - PASS
- [x] ✅ TC-008 `createsuperuser` → `ADMIN True True QA Admin 1990-01-01 ro` - PASS
- [x] ✅ TC-016 `GET /healthz` → `200`, `{"status": "ok", "db": "ok"}`, `Cache-Control: … no-store …` - PASS
- [x] ✅ TC-014 Stop/start server → `users after restart: 1`, health 200 - PASS
- [x] ✅ TC-025 Prod settings with secret + host → `System check identified no issues` - PASS

### Edge Cases
- [x] ✅ TC-018 `HEAD /healthz` → 200, 0 body bytes - PASS
- [x] ✅ TC-017 Repeated GET → identical body, no session cookie (automated) - PASS
- [x] ✅ TC-023 `/ro/healthz`, `/en/healthz` → 404 - PASS
- [x] ✅ TC-007 `create_superuser(role="STUDENT")` → forced to ADMIN (automated) - PASS

### Error Handling
- [x] ✅ TC-019 `DatabaseError` on `SELECT 1` → 503 generic body, ERROR log (automated) - PASS
- [x] ⚠️ TC-020 Read-only data dir → `503 {"status": "unavailable", "db": "error"}` ✅, restored dir → 200 ✅; log event was `healthz.db_unavailable`, not `healthz.data_dir_not_writable` - PASS with note (BUG-001)
- [x] ✅ TC-021 Real `POST /healthz` → 403 (CSRF), no side effects - PASS (per amended AC 9)
- [x] ✅ TC-022 View guard `POST` → 405 (automated) - PASS
- [x] ✅ TC-010 Prod without `DJANGO_SECRET_KEY` → `ImproperlyConfigured: Required environment variable DJANGO_SECRET_KEY is not set` - PASS
- [x] ✅ TC-011 Prod with `DJANGO_ALLOWED_HOSTS=" , "` → `ImproperlyConfigured: DJANGO_ALLOWED_HOSTS must list at least one host` - PASS

### Integration Points
- [x] ✅ SQLite file DB: WAL / IMMEDIATE / timeout 20 (TC-012) - PASS
- [x] ✅ Template engine + static: `base.html` renders `lang="ro"` and links `css/tokens.css`; `{% load ui %}` loads (TC-028) - PASS
- [x] ✅ gettext catalogues: both `.po` headers have `Language` and a UTF-8 `Content-Type` (TC-028). Compilation is not possible until gettext is installed (Story 1.4) - PASS (header check only)

---

## Issues Found

| ID | Severity | Category | Description | Reproduction Steps | Status |
|----|----------|----------|-------------|-------------------|--------|
| BUG-001 | 🟢 Low | Observability | With a read-only data directory, `/healthz` correctly returns 503, but logs `healthz.db_unavailable` instead of `healthz.data_dir_not_writable`. In WAL mode a new SQLite connection must create the `-wal`/`-shm` files, so `SELECT 1` already fails and the directory branch (`health.py:22-24`) isn't reached. An operator would look for a database fault rather than a permissions problem. The automated test passes only because it patches `os.access` after a successful query. | 1. `rm -rf data && uv run python manage.py migrate` 2. `uv run python manage.py runserver 8766 --noreload` 3. `chmod -w data` 4. `curl -i localhost:8766/healthz` → 503 ✅ 5. server log line: `healthz.db_unavailable` ❌ (expected `healthz.data_dir_not_writable`) 6. `chmod u+w data` | Open |

**Observation (not a bug)**: the console log shows only the event name. The `error` class passed in `extra` isn't printed by the plain handler. That's expected until Story 1.1 adds the JSON formatter. Verify it in QA Group 1.

---

## Test Evidence

### Test Logs

```
== Unit tests
============================== 7 passed in 0.07s ===============================
== Integration tests
============================== 23 passed in 1.04s ==============================
== Full suite + coverage
collected 30 items
TOTAL                                                    69      0      4      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
============================== 30 passed in 1.09s ==============================
== Flakiness: 3 more full runs
30 passed in 1.05s
30 passed in 0.98s
30 passed in 0.96s
== TC-026 gates
35 files already formatted
All checks passed!
Success: no issues found in 37 source files
Contracts: 2 kept, 0 broken.
== TC-029
No changes detected
src/infrastructure/persistence/accounts/migrations/0001_initial.py
== TC-027
26 shared_files listed; 23 owned by 1.0 (3 belong to stories 1.1/3.4/7.1); missing: none
```

```
== TC-016
HTTP/1.1 200 OK
Cache-Control: max-age=0, no-cache, no-store, must-revalidate, private
{"status": "ok", "db": "ok"}
== TC-018 HEAD
HTTP/1.1 200 OK
HEAD body bytes: 0
== TC-021 POST
403
== TC-023
/ro/healthz -> 404
/en/healthz -> 404
== TC-020 read-only data dir
HTTP/1.1 503 Service Unavailable
{"status": "unavailable", "db": "error"}
(after chmod u+w) {"status": "ok", "db": "ok"}
server log: healthz.db_unavailable   ← BUG-001
== TC-014 restart
users after restart: 1
{"status": "ok", "db": "ok"}
== TC-009
raw password stored: False | hash prefix: pbkdf2_sha256
== TC-010 / TC-011 / TC-025
ImproperlyConfigured: Required environment variable DJANGO_SECRET_KEY is not set
ImproperlyConfigured: DJANGO_ALLOWED_HOSTS must list at least one host
System check identified no issues (0 silenced).
```

### Coverage Reports
- Overall: 100.00% (`--cov=src --cov-branch`); domain/application packages are empty in this story, so their 100%/95% gates apply from wave 2

### Execution notes
- The first TC-027 attempt used a `sed` pattern (`\s`) that macOS `sed` doesn't support, which falsely reported all files missing. It was re-run with a Python parser: 23/23 present. This was a fault in the QA tooling, not the product.
- TC-008 used `createsuperuser --noinput` with `DJANGO_SUPERUSER_*` variables, because the agent can't type into the interactive prompt. The interactive prompt's field list (username, full name, date of birth) follows from `REQUIRED_FIELDS`, and the command path is covered by `test_createsuperuser_command_creates_admin_role`.

---

## Recommendations

### Must Fix Before Release (Blockers)
- None

### Should Fix Before Release
- None

### Can Fix After Release
1. BUG-001: report the read-only directory as its own cause. For example, check `os.access(db_dir, os.W_OK)` **before** opening the cursor, or add the exception text class (`OperationalError: attempt to write a readonly database`) to the event. Add an integration test that makes the directory read-only for real, instead of patching `os.access`. It fits naturally into Story 1.1, which reworks logging.

### Process
- This report is the baseline for future `aire-qa-regression` runs on Story 1.0 / Epic 1.
- Merge `feature/story-1.0-root-tooling-seed` to `main` so wave 2 (1.1–1.5, 1.8, 2.1) can branch from it.

---

## Sign-Off

**AIREQA Agent**
**Date**: 2026-10-21
**Status**: APPROVED (CONDITIONAL on BUG-001 being tracked; non-blocking)
**Notes**: Validated at commit `26b4ece`. Re-validate `/healthz` logging in QA Group 1 once Story 1.1 lands.
