# Code Review - Story 1.0: Root Tooling Seed

> ## 🛠️ Remediation Status: 🟡 Partially Remediated (5/7)
> - **Remediated**: 2026-10-21 by DEV Agent
> - **Fixed**: 5 issue(s) — 🔴 0 / 🟠 0 / 🟡 2 / 🟢 3
> - **Deferred (with user consent)**: 2 (ISS-004 → DevOps, ISS-005 → Story 1.1). See the Remediation Section
> - **Tests**: 30/30 passing | **Coverage**: 100% | **Linter**: clean
> - **Scenario**: Code Review

**Date**: 2026-10-21
**Reviewed By**: REVIEWER Agent
**Review Number**: 1
**Review Mode**: INITIAL_REVIEW
**Status**: ⚠️ APPROVED WITH COMMENTS

---

## Review Metadata

**Previous Review**: None
**Previous Status**: N/A
**Files Changed Since Last Review**: All (first review)
**Severity Threshold Applied**: All (🔴 🟠 🟡 🟢)
**Branch**: `feature/story-1.0-root-tooling-seed` (uncommitted working tree, 2026-10-21)

---

## Review Summary

**Components Reviewed**: `pyproject.toml`, `manage.py`, `src/config/**` (env, base/dev/test/prod settings, urls, wsgi), `src/infrastructure/persistence/accounts/**` (apps, managers, models, migration 0001), `src/infrastructure/web/common/{health,decorators}.py`, `src/infrastructure/container.py`, `src/infrastructure/web/templatetags/ui.py`, `layouts/base.html`, `tokens.css`, both `django.po`, `.gitignore`, `.env.example`, `README.md`, all of `tests/`, `docs/stories-implemented/story-1.0-review.md`
**Lines of Code**: ~640 Python (src + tests, excluding migrations), plus config, templates and CSS
**Tests Reviewed**: Yes (28: 7 unit, 21 integration)
**Coverage**: 100% (lines + branches), re-run and verified by the reviewer

**Overall Assessment**: A clean, small seed that matches the story and patterns §1, §3, §6.1, §6.4 and §10 closely. Every quality gate re-runs green, the layer contracts hold, and the tests check behaviour (real subprocess restart, real WAL pragma, CSRF-enforced client) rather than inflating coverage. There are no blockers or high issues. The comments cover an evidence-accuracy slip in the self-review, the user-accepted 403 deviation not yet reflected in the story contract, and some small hardening and test-tooling items.

### Evidence verification (re-run by reviewer)

```
$ uv run ruff format --check .        → 35 files already formatted
$ uv run ruff check .                 → All checks passed!
$ uv run mypy                         → Success: no issues found in 37 source files
$ PYTHONPATH=src uv run lint-imports  → Contracts: 2 kept, 0 broken.
$ manage.py makemigrations --check --dry-run → No changes detected
$ uv run pytest --cov=src --cov-branch --cov-fail-under=85
  TOTAL 69 0 4 0 100% · Required test coverage of 85% reached. Total coverage: 100.00%
  28 passed in 0.99s
$ pytest --collect-only per file: restart_persistence 3 · user_model 8 · healthz 9 · role_access_matrix 1 · test_env 7
$ DJANGO_SETTINGS_MODULE=config.settings.prod manage.py check --deploy  (with secret + hosts set)
  security.W005 SECURE_HSTS_INCLUDE_SUBDOMAINS not set · security.W021 SECURE_HSTS_PRELOAD not set
```

---

## Checklist Results

### Correctness
- [x] ✅ Code does what the story specifies (AC 1–8, 10–15)
- [x] ⚠️ AC 9: production `POST /healthz` returns 403, not 405. The user accepted this, but the story contract hasn't been updated (ISS-002)
- [x] ✅ Edge cases handled (DB error, read-only dir, HEAD, language prefix, repeated migrate)
- [x] ✅ Error conditions handled. `DatabaseError` is caught, logged at ERROR with the class name only, and mapped to 503
- [x] ✅ No race conditions or resource leaks (cursor used as a context manager)

### Pattern Adherence
- [x] ✅ Layering §3: config → infrastructure only, domain/application empty and framework-free
- [x] ✅ Configuration §10: `os.environ` read only in `env.py` (`manage.py`/`wsgi.py` only `setdefault` the settings module)
- [x] ✅ SQLite §6.1 exactly; `ATOMIC_REQUESTS=False`
- [x] ✅ Naming §1.2: `UserModel`, explicit `db_table="accounts_user"`, app label `accounts`
- [x] ✅ Logging §9: event names, no PII
- [x] ⚠️ `LOG_LEVEL` dev default is `INFO`; the §10 table says `DEBUG` in dev (ISS-005)
- [x] ✅ Function sizes all well under 30 lines; largest file 107 lines

### Testing
- [x] ✅ Unit tests exist (`test_env.py`, 7) and are meaningful
- [x] ✅ Integration tests cover persistence, health, the access matrix and process restart
- [x] ✅ Happy, edge and error paths covered; AAA and behavioural names
- [x] ✅ Coverage 100% (≥85%)
- [x] ⚠️ Subprocess helper hides stderr on failure (ISS-006); `slow` marker registered outside `pyproject.toml` with no `--strict-markers` (ISS-007)

### Documentation
- [x] ✅ README has all 8 §14 sections with exact commands
- [x] ✅ No TODO/FIXME, no commented-out code
- [x] ✅ Comments explain why (ADR-004, IMMEDIATE, file-based test DB)
- [x] ⚠️ Self-review evidence states the wrong healthz test count and an output block that doesn't match the real run (ISS-001)

### Security
- [x] ✅ No real secrets. Only the documented dev and test placeholders, each `noqa: S105`; `.env`/`data/` git-ignored
- [x] ✅ `/healthz` is public by design, in `PUBLIC_URL_NAMES`, returns no personal data and sets no session
- [x] ✅ No `csrf_exempt`; CSRF protection kept intact (which is what causes ISS-002)
- [x] ✅ Passwords hashed (`check_password` asserted; manual `pbkdf2_` prefix; Argon2 is Story 1.2)
- [x] ✅ Prod refuses to start without `DJANGO_SECRET_KEY`; SSL redirect, HSTS 1 year, secure cookies set
- [x] ⚠️ `check --deploy` HSTS subdomain/preload warnings (ISS-004); empty `DJANGO_ALLOWED_HOSTS` accepted silently (ISS-003)
- [x] ✅ No SQL built from input (one constant `SELECT 1`)

### Performance
- [x] ✅ N/A for a seed. Health check is a single constant query

### SOLID / Anti-Monolith
- [x] ✅ SRP: env helpers, settings, user model, manager and health view each have one job
- [x] ✅ OCP/LSP: `UserManager.create_superuser` keeps the parent signature and contract and only forces the role
- [x] ✅ DIP: `container.py` composition root seeded; no singletons
- [x] ✅ No circular dependencies; import-linter green

---

## Issues Found

### ISS-001: Self-review evidence doesn't match the actual test run 🟡 Medium

**Category**: Documentation
**File**: `docs/stories-implemented/story-1.0-review.md:37`, `:63`, `:130`
**Pattern Reference**: `SPEC/rulebooks/aire-implementation-rulebook.md` — Evidence Requirements ("Test command output (copy/paste)") and Sign-off rule

**Issue**:
The review doc lists `test_healthz.py` as **10 tests** (line 37 and the AC 9 row at line 130), and its "Test output" block (line 63) shows 10 dots for that file. The real collection has **9** tests in `test_healthz.py`. The total of 28 is correct. The block is a reconstruction rather than pasted output, which the rulebook forbids for evidence.

**Suggested Fix**:
Replace the "Test output" block with the verbatim output of `uv run pytest --cov=src --cov-branch --cov-fail-under=85` and change "10 tests" to "9 tests" in both places.

**Why This Matters**: DoD evidence is what reviewers and QA trust instead of re-running everything. A wrong number, even a harmless one, undermines the whole evidence section.

**Resolution** (2026-10-21, DEV):
- Fix: replaced the reconstructed block with verbatim `pytest` output (28 collected, healthz 9 dots) and corrected "10 tests" to "9 tests" in the Files Changed table and the AC 9 row
- Commit / change ref: `docs/stories-implemented/story-1.0-review.md` (Files Changed row for `test_healthz.py`, Testing Summary block, Gate 1 AC 9 row)
- Test evidence: documentation-only, so no test applies; `grep -n "10 tests" …review.md` → no matches
- Status: ✅ Resolved

---

### ISS-002: Accepted 403 deviation isn't reflected in the story or plan contract 🟡 Medium

**Category**: Documentation / Correctness (contract)
**File**: `docs/plans/stories/epic-1-story-1.0-Root-Tooling-Seed.md:136`, `:157`; `tests/integration/web/test_healthz.py` (CSRF test)
**Pattern Reference**: Implementation rulebook Gate 3 (Contract Consistency); patterns §13 (`csrf_exempt` forbidden)

**Issue**:
AC 9 and the system-response table still say non-GET/HEAD → `405`. The real behaviour is `403` from `CsrfViewMiddleware`, accepted by the user on 2026-10-21 and recorded only in the self-review's Deviations section. QA Group 1 re-checks `/healthz` with Story 1.1 and will test against the story text, so it will raise a false defect.

**Suggested Fix** (story or plan owner, not DEV code):
```markdown
9. … non-GET/HEAD → rejected with no side effects: `403` in a real request (CSRF middleware runs
   first; `csrf_exempt` is forbidden by patterns §13) and `405` from the view's own guard. …
| `POST /healthz` (or any non-GET/HEAD) | `403 Forbidden` (CSRF) — view-level guard returns `405` | none |
```

**Why This Matters**: The code is correct and secure. The contract that downstream QA reads is now wrong.

**Resolution** (2026-10-21, DEV, story-file edit approved by the user in the remediation plan):
- Fix: AC 9 and the system-response table now state `403` (CSRF first) in real requests and `405` from the view's guard, citing patterns §13 and the 2026-10-21 owner decision
- Commit / change ref: `docs/plans/stories/epic-1-story-1.0-Root-Tooling-Seed.md:136`, `:157`; no other plan or architecture doc states a healthz 405 (grep checked)
- Test evidence: behaviour already pinned by `test_healthz_view_rejects_post` (405) and `test_healthz_post_is_rejected_by_csrf_before_reaching_the_view` (403), both green
- Status: ✅ Resolved

---

### ISS-003: `env_list` for a required prod variable accepts an empty value 🟢 Low

**Category**: Security / Configuration
**File**: `src/config/settings/prod.py:6`

**Issue**:
`env_list("DJANGO_ALLOWED_HOSTS")` raises when the variable is missing. But if it's set to `""` (a common templating mistake), it returns `[]`. With `DEBUG=False`, every request then gets 400 with no clear start-up error.

**Suggested Fix**:
```python
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must list at least one host")
```
Alternatively, add a `required_nonempty` helper in `env.py` with a unit test.

**Resolution** (2026-10-21, DEV):
- Fix: `prod.py` raises `ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must list at least one host")` when the parsed list is empty (the report's first suggestion; one caller only, so no new helper)
- Commit / change ref: `src/config/settings/prod.py:9-11`
- Test evidence: `test_prod_settings_refuse_to_start_with_empty_allowed_hosts` failed before the fix and passes after; `test_prod_settings_start_with_secret_key_and_hosts` proves a valid config still starts
- Status: ✅ Resolved

---

### ISS-004: `check --deploy` HSTS warnings (W005, W021) 🟢 Low

**Category**: Security
**File**: `src/config/settings/prod.py:10`

**Issue**:
`SECURE_HSTS_INCLUDE_SUBDOMAINS` and `SECURE_HSTS_PRELOAD` aren't set. The patterns §10 list doesn't require them, and whether they're safe depends on the production domain, which isn't decided yet (hosting is a DevOps decision).

**Suggested Fix**: Raise it in `aire-devops-discover`. Once the domain is known, either set both to `True` or silence W005/W021 in `prod.py` with a comment giving the reason.

**Deferral** (2026-10-21, DEV): deferred with user consent to `aire-devops-discover`, because the production domain isn't decided yet. Still open.

---

### ISS-005: Dev log level default differs from patterns §10 🟢 Low

**Category**: Pattern
**File**: `src/config/settings/base.py:80`
**Pattern Reference**: patterns §10 table: `LOG_LEVEL` dev default "`INFO` (`DEBUG` in dev)"

**Suggested Fix** (in `dev.py`):
```python
LOGGING["root"]["level"] = env_str("LOG_LEVEL", "DEBUG")
```
This can wait until Story 1.1 replaces `LOGGING` with the JSON formatter. Include it there.

**Deferral** (2026-10-21, DEV): deferred with user consent to Story 1.1, which rewrites `LOGGING`. Still open.

---

### ISS-006: Subprocess helper hides stderr when a step fails 🟢 Low

**Category**: Testing / Maintainability
**File**: `tests/integration/persistence/accounts/test_restart_persistence.py:30-38`

**Issue**:
`check=True` raises `CalledProcessError`, and pytest shows only the return code. Django's traceback in `stderr` is captured but never displayed, which makes a failing migration hard to diagnose in CI.

**Suggested Fix**:
```python
result = subprocess.run([...], capture_output=True, text=True, check=False)
assert result.returncode == 0, result.stderr
return result.stdout.strip()
```

**Resolution** (2026-10-21, DEV):
- Fix: one `_run_manage` helper with `check=False`. `_manage_dev` asserts `returncode == 0` with `result.stderr` as the message. The three copied `subprocess.run` blocks are folded into `_run_manage` / `_prod_check`
- Commit / change ref: `tests/integration/persistence/accounts/test_restart_persistence.py:24-46`
- Test evidence: test-tooling change only (no production behaviour to reproduce); all 5 `slow` tests green
- Status: ✅ Resolved

---

### ISS-007: `slow` marker registered outside `pyproject.toml`; markers not strict 🟢 Low

**Category**: Testing
**File**: `tests/conftest.py:10-11`, `pyproject.toml:65`

**Issue**:
The `e2e` marker is declared in `pyproject.toml`, but `slow` is added through a `pytest_configure` hook. That splits marker declarations across two places, and `tests/conftest.py` is a shared file several wave-2 stories will edit. Without `--strict-markers`, a typo like `@pytest.mark.e2ee` would silently run in the default suite.

**Suggested Fix**:
```toml
addopts = "--import-mode=importlib --strict-markers -m 'not e2e'"
markers = [
  "e2e: browser end-to-end tests (run with -m e2e)",
  "slow: spawns manage.py subprocesses",
]
```
Then delete the hook from `conftest.py`.

**Resolution** (2026-10-21, DEV):
- Fix: `slow` declared next to `e2e` in `pyproject.toml`, `--strict-markers` added to `addopts`, `pytest_configure` hook removed from `tests/conftest.py`
- Commit / change ref: `pyproject.toml` `[tool.pytest.ini_options]`; `tests/conftest.py`
- Test evidence: a scratch test using `@pytest.mark.e2ee` now errors with `'e2ee' not found in markers configuration option`; `pytest -m slow` → `5 passed, 25 deselected`
- Status: ✅ Resolved

---

## Issue Summary

| # | ID | Severity | Category | File | Status |
|---|-----|----------|----------|------|--------|
| 1 | ISS-001 | 🟡 Medium | Documentation | `docs/stories-implemented/story-1.0-review.md:37,63,130` | Should Fix |
| 2 | ISS-002 | 🟡 Medium | Documentation / Contract | `docs/plans/stories/epic-1-story-1.0-Root-Tooling-Seed.md:136,157` | Should Fix (story owner) |
| 3 | ISS-003 | 🟢 Low | Security / Config | `src/config/settings/prod.py:6` | Optional |
| 4 | ISS-004 | 🟢 Low | Security | `src/config/settings/prod.py:10` | Defer to DevOps |
| 5 | ISS-005 | 🟢 Low | Pattern | `src/config/settings/base.py:80` | Optional (fold into 1.1) |
| 6 | ISS-006 | 🟢 Low | Testing | `tests/integration/persistence/accounts/test_restart_persistence.py:30-38` | Optional |
| 7 | ISS-007 | 🟢 Low | Testing | `tests/conftest.py:10-11` | Optional |

**Summary**:
- Blockers: 0
- High: 0
- Medium: 2
- Low: 5

---

## What Was Done Well

1. ✅ The quality gates are real and strict from day one: ruff with security and complexity rules, strict mypy for domain/application, and two import-linter contracts. All are green, and I re-ran them.
2. ✅ Restart persistence is tested with genuinely separate processes against a file database, not simulated in one process.
3. ✅ The CSRF/405 conflict was found by testing against a real server. It was solved without weakening CSRF, and both behaviours are pinned by tests.
4. ✅ The file-based test DB means the WAL and `IMMEDIATE` assertions exercise the production configuration.
5. ✅ The health check fails safely: 503 with a generic body, exception class only in logs, no stack trace and no session.
6. ✅ All 23 `shared_files` exist as working stubs, so wave-2 branches can start without create/create conflicts.

---

## Approval Status

**Decision**: ⚠️ APPROVED WITH COMMENTS

**Reason**: No blockers or high issues. Two Medium documentation and contract items should be fixed before QA Group 1 runs. The Low items are optional, and ISS-004 and ISS-005 have natural homes in DevOps and Story 1.1.

**Next Steps**:
1. `aire-dev-remediate` for ISS-001 (correct the evidence) and optionally ISS-003, ISS-006 and ISS-007
2. Story/plan owner updates AC 9 and the response table (ISS-002)
3. Commit and merge to `main` so wave 2 can branch from it

---

## Sign-Off

**Reviewer**: REVIEWER Agent
**Date**: 2026-10-21
**Signature**: Approved with comments

---

# 🛠️ Remediation — 2026-10-21

**Developer**: DEV Agent
**Severity Scope**: 🟡 Medium + 🟢 Low (no 🔴/🟠 in this report); scope confirmed by the user
**Scenario**: Code Review
**Stories Affected**: 1.0

## Issues Remediated

| ID | Severity | Story | File:Line | Summary | Resolution | Test Added |
|------|----------|-------|-----------|---------|------------|------------|
| ISS-001 | 🟡 Medium | 1.0 | `docs/stories-implemented/story-1.0-review.md` | Evidence didn't match the run | Verbatim output pasted; 10 → 9 corrected | n/a (docs) |
| ISS-002 | 🟡 Medium | 1.0 | `docs/plans/stories/epic-1-story-1.0-Root-Tooling-Seed.md:136,157` | AC 9 still said 405 | AC + response table describe 403 (CSRF) / 405 (view guard) | already covered by 2 healthz tests ✅ |
| ISS-003 | 🟢 Low | 1.0 | `src/config/settings/prod.py:9-11` | Empty `DJANGO_ALLOWED_HOSTS` accepted | `ImproperlyConfigured` on empty list | `test_prod_settings_refuse_to_start_with_empty_allowed_hosts` ✅ (red → green), `test_prod_settings_start_with_secret_key_and_hosts` ✅ |
| ISS-006 | 🟢 Low | 1.0 | `tests/integration/persistence/accounts/test_restart_persistence.py:24-46` | stderr hidden on failure | Single helper, `check=False`, assert with stderr | n/a (test tooling) |
| ISS-007 | 🟢 Low | 1.0 | `pyproject.toml`, `tests/conftest.py` | Marker split, not strict | `slow` in pyproject, `--strict-markers`, hook removed | scratch typo-marker run errors ✅ |

## Issues Deferred (with user consent)

| ID | Severity | Story | Reason |
|----|----------|-------|--------|
| ISS-004 | 🟢 Low | 1.0 | HSTS subdomains/preload depend on the production domain. Goes to `aire-devops-discover` |
| ISS-005 | 🟢 Low | 1.0 | Dev log level. Story 1.1 rewrites `LOGGING` (JSON formatter) and should apply `DEBUG` in dev there |

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `src/config/settings/prod.py` | Modified | Fail fast on empty `ALLOWED_HOSTS` |
| `tests/integration/persistence/accounts/test_restart_persistence.py` | Modified | Shared `_run_manage` helper that shows stderr; 2 new prod start-up tests |
| `pyproject.toml` | Modified | `slow` marker declared; `--strict-markers` |
| `tests/conftest.py` | Modified | `pytest_configure` hook removed |
| `docs/stories-implemented/story-1.0-review.md` | Modified | Verbatim test output; corrected counts |
| `docs/plans/stories/epic-1-story-1.0-Root-Tooling-Seed.md` | Modified | AC 9 and response table aligned with the accepted 403 |

## Patterns Applied

| Pattern | Where Applied | Notes |
|---------|---------------|-------|
| Configuration §10 (fail fast on bad env) | `prod.py` | Same `ImproperlyConfigured` style as the missing-secret check |
| Testing §12 (AAA, behavioural names) | new prod tests | Positive control added so the negative tests can't pass for the wrong reason |
| Evidence requirements (implementation rulebook) | self-review | Output pasted verbatim, not reconstructed |

## Testing Summary

- **Targeted tests added**: 2 (`…_empty_allowed_hosts` red → green, `…_start_with_secret_key_and_hosts`)
- **Full suite**: 30/30 passing (7 unit, 23 integration)
- **Coverage**: 100% (target ≥85%)
- **Gates**: ruff format/check clean · mypy 0 issues · import-linter 2/2 kept · `makemigrations --check` no changes

**Test Output** (verbatim; per-file 100% rows and environment header lines omitted):
```
============================= test session starts ==============================
django: version: 5.2.18, settings: config.settings.test (from ini)
testpaths: tests
collected 30 items

tests/integration/persistence/accounts/test_user_model.py ........       [ 26%]
tests/integration/web/test_healthz.py .........                          [ 56%]
tests/integration/web/test_role_access_matrix.py .                       [ 60%]
tests/integration/persistence/accounts/test_restart_persistence.py ..... [ 76%]
                                                                         [ 76%]
tests/unit/config/test_env.py .......                                    [100%]

================================ tests coverage ================================

TOTAL                                                    69      0      4      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
============================== 30 passed in 1.14s ==============================
```

## Deviations from Report Suggestions

- ISS-003: used the inline check, not a new `env.py` helper, because there is a single caller. A helper can come later if a second required list appears.
- ISS-006: went beyond the suggestion by merging all three copied `subprocess.run` blocks into the same helper, so the stderr behaviour applies everywhere.

## Lessons Learned

1. Negative start-up tests need a positive control. Otherwise any crash (wrong path, import error) makes them pass.
2. Evidence blocks must be pasted, never retyped. The 10-vs-9 slip came from writing the block by hand.

## Next Steps

- [ ] Re-request code review (`aire-review-code`). Optional here, since no 🔴 was fixed
- [ ] Commit `feature/story-1.0-root-tooling-seed` and merge to `main` before wave 2
