# Bug Triage Report

> ## 🛠️ Remediation Status: ✅ Resolved
> - **Remediated**: 2026-10-23 by DEV Agent
> - **Fixed**: 1 bug(s) — P0:0 / P1:1 / P2:0 / P3:0 (BUG-004, application side; BUG-001–003 were already verified fixed)
> - **Deferred (with user consent)**: 0
> - **Tests**: 1541/1541 passing (+17 e2e) | **Coverage**: 100% | **Linter**: clean
> - **Scenario**: QA Triage
> - **Go-live condition**: PR #1 must deploy `AXES_PROXY_COUNT=0` (it says `1`). DevOps hand-off below.

**Date**: 2026-10-23
**Triaged By**: QA Agent
**Source Report(s)** (user choice "both" + the raised defect):
- `docs/testing/validation-report-story-1.0-2026-10-21.md`: BUG-001
- `docs/testing/regression-report-2026-10-21.md`: 0 regressions; BUG-001, BUG-002 and BUG-003 listed as fixed; three still-open non-regression items
- **BUG-004**, raised today via `aire-raise-defect` (local tracking) and recorded in this file. **Re-reproduced by QA** with three control runs before classification (evidence below).

**Code Under Test**: `main` @ `ee862ec` (CYCLE-1 complete; 1532/1532 tests + 17/17 e2e passing, coverage 100%)
**Environment**: local macOS, `runserver` with `config.settings.dev`, fresh SQLite DB per run, real CSRF tokens. Nginx is simulated by sending `X-Forwarded-For` the way PR #1's `proxy_headers.inc` sets it (`X-Forwarded-For $remote_addr`, overwrite, one value).
**BUILDID**: CYCLE-1

---

## Summary

**Total Bugs**: 4 (1 open, 3 verified fixed)
**Critical**: 0 🔴
**High**: 1 🟠 (BUG-004, open)
**Medium**: 0 🟡 open (BUG-002 and BUG-003 were Medium; both verified fixed)
**Low**: 0 🟢 open (BUG-001 was Low; verified fixed)

**Release Blockers**: 1. BUG-004 blocks **production go-live behind the reverse proxy**. It doesn't block the CYCLE-1 build sign-off (local demo, direct access).

---

## Release Blocking Bugs

| ID | Severity | Summary | Impact | Recommendation |
|----|----------|---------|--------|----------------|
| BUG-004 | 🟠 High | Behind the reverse proxy, lockouts key on the proxy's IP (or on NULL): any client can lock any username out | Every user of a deployed environment; lockouts become per-username, so anyone can lock out a known account for 15 min, repeatedly; client IPs lost from the audit log and admin lockout screen | MUST FIX before go-live (P1) |

---

## Priority Classification

### P0 - Must Fix Now (Release Blockers)
- None

### P1 - Should Fix Before Release
- BUG-004: lockout and audit client IP behind the reverse proxy (blocks go-live)

### P2 - Can Fix After Release
- None open (BUG-002 and BUG-003 were fixed in `26fc1c5`; re-verified below)

### P3 - Nice to Have
- None open (BUG-001 was fixed in `26fc1c5`; re-verified below)

---

## Bug Details

### BUG-004: [Login lockout] Behind the reverse proxy, lockouts key on the proxy's IP: any client can lock any username out 🟠
**Severity**: High (raised as "Major"; confirmed by triage)
**Priority**: P1
**Category**: Security (availability: account lockout DoS; integrity of audit IP)
**Affected Users**: every account (Student, Teacher, Parent, Admin) on any environment behind Nginx (staging, prod). Local dev and direct access aren't affected.
**Workaround**: partial only. An Admin can clear a lockout in the admin (Story 1.9), and a lockout expires after 15 minutes, but an attacker can repeat it at will. The Nginx login rate limit (PR #1, 5/min per IP) slows but doesn't stop it: 5 attempts are enough.
**Recommendation**: BLOCK GO-LIVE. Fix before `aire-devops-deploy` to production.
**Assigned To**: DEV (application settings and dependency), with a DevOps hand-off for the deployment value.
**Target**: before production go-live (and before staging is used for UAT with real accounts)

#### Environment
**Build:** `main` @ `71d1ee5` (raised), re-reproduced at `ee862ec` | **Env:** local, `config.settings.dev`; the lockout settings live in `base.py`, so every environment behaves the same | **OS:** macOS (Darwin 25.6) | **Client:** HTTP script (urllib), Nginx simulated via `X-Forwarded-For` | **URL:** `/en/accounts/login/`

#### Preconditions
- The app runs behind one reverse proxy, so every request reaches Django from the proxy's address (here 127.0.0.1), with the real client in `X-Forwarded-For`.
- An active Student account `ana` with password `pilot-pass-123`.

#### Steps to Reproduce
1. Start the app with `AXES_PROXY_COUNT=1` (the value planned for staging/prod in PR #1).
2. As client **203.0.113.10** (`X-Forwarded-For: 203.0.113.10`), submit the sign-in form for `ana` with a wrong password 5 times.
3. As a different client, **198.51.100.20** (`X-Forwarded-For: 198.51.100.20`), submit the sign-in form for `ana` with the **correct** password.
4. Inspect `axes_accessattempt` and `audit_log`.

#### Expected Result
- Lockouts are **per username + client IP** (architecture; Story 1.2 `AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]`).
- Step 2 locks out only `ana` @ 203.0.113.10.
- Step 3 succeeds: 302 to `/en/`.
- The rows record 203.0.113.10 and 198.51.100.20.

#### Actual Result (QA re-reproduction plus controls)

| Run | `django-ipware` | axes reads `X-Forwarded-For` | `AXES_PROXY_COUNT` | Step 6 (student, correct password) | IP recorded (axes + audit) |
|-----|-----------------|------------------------------|--------------------|-------------------------------------|----------------------------|
| A: as built | ❌ not installed | ❌ (axes falls back to `REMOTE_ADDR`) | 1 | **429**: locked out | `127.0.0.1` (the proxy) for everyone |
| B: control | ✅ (`uv run --with`, not installed in the project) | ❌ (axes default `("REMOTE_ADDR",)`) | 1 | **429** | `NULL` for everyone |
| C: control | ✅ | ❌ | 0 | **429** | `127.0.0.1` |
| D: control | ✅ | ✅ `("HTTP_X_FORWARDED_FOR", "REMOTE_ADDR")` | **1** | **429** | `NULL` |
| E: control | ✅ | ✅ | **0** | ✅ **302 → `/en/`** | `203.0.113.10` (5 failures + lockout), `198.51.100.20` (login) |

```
A  step 5: attacker 203.0.113.10 wrong password -> 429
   step 6: student 198.51.100.20 CORRECT password -> 429
   axes: ana@127.0.0.1 x5 | audit: auth.login_failed@127.0.0.1 ... auth.lockout@127.0.0.1
E  step 5: attacker 203.0.113.10 wrong password -> 429
   step 6: student 198.51.100.20 CORRECT password -> 302 /en/
   axes|ana|'203.0.113.10'|5
   audit auth.login_failed '203.0.113.10' x5, auth.lockout '203.0.113.10', auth.login '198.51.100.20'
```

Direct `ipware.ip.get_client_ip` probe (django-ipware 8.0.0, python-ipware 4.1.1), `REMOTE_ADDR=127.0.0.1`:
```
XFF='203.0.113.10'           proxy_count=None -> ('203.0.113.10', False)
XFF='203.0.113.10'           proxy_count=0    -> ('203.0.113.10', False)
XFF='203.0.113.10'           proxy_count=1    -> (None, False)
XFF='203.0.113.10, 10.0.0.2' proxy_count=1    -> ('203.0.113.10', False)
```

#### Root cause (three parts, all required; confirmed by runs A–E)
1. **`django-ipware` is not installed.** django-axes 8.3.1 imports `ipware.ip` and silently falls back to `REMOTE_ADDR` without it (`axes/helpers.py:206-225`). The `status.md` hand-off named `python-ipware`; axes needs `django-ipware`, which brings `python-ipware` with it.
2. **Axes never looks at `X-Forwarded-For` by default.** `AXES_IPWARE_META_PRECEDENCE_ORDER` defaults to `("REMOTE_ADDR",)` (`axes/conf.py:199-206`), and the project doesn't set it.
3. **The planned `AXES_PROXY_COUNT=1` doesn't match the Nginx header style.** ipware's `proxy_count` counts proxies listed *inside* `X-Forwarded-For`. PR #1's Nginx **overwrites** the header with one value (`$remote_addr`), so the matching value is `0` (or unset). With `1`, ipware returns `None` and every attempt is keyed on NULL. This value appears in PR #1 (`proxy_headers.inc:3` comment, `pipeline-secrets.md:75` `AXES_PROXY_COUNT=1`, `deployment-plan` step 2) and in `discovery-report.md:136`.

#### Constraints for the fix (triage notes, not a design decision)
- Reading `X-Forwarded-For` is safe **only behind a proxy that overwrites it**. In dev, or with direct access, a client could forge it, so the header order must be environment-specific: prod and staging only, the same pattern as `TRUST_INCOMING_REQUEST_ID`.
- The tests must emulate the exact Nginx header (one value, overwritten) and cover both the "different client isn't locked out" case and the audit IP. Tests that only patch the helper wouldn't catch causes 2 and 3.
- **DevOps hand-off:** the deployment value of `AXES_PROXY_COUNT` (and the comments in PR #1) must match whatever the fix settles on.

#### Affected Story / Component
- **Story 1.2** Login & Session Security: `src/config/settings/base.py:156` (`AXES_IPWARE_PROXY_COUNT`), dependency list `pyproject.toml`.
- **Story 1.8** Audit Log: `src/infrastructure/persistence/audit/receivers.py:27` (same helper).
- **PR #1** (DevOps): `AXES_PROXY_COUNT=1` in env, docs and comments.

**Dependencies**: the fix must land together with the PR #1 value change. Neither alone fixes production.

---
Raised via AIRE `aire-raise-defect` by QA. Drafted with AI (Claude Opus 5.5). Triaged via `aire-qa-triage`.

**Resolution** (2026-10-23, DEV):
- **Fix:** all three causes.
  1. **Dependency:** `django-ipware>=7.0` added (8.0.0, which brings python-ipware 4.1.1).
  2. **Header order:** `base.py` sets `AXES_IPWARE_META_PRECEDENCE_ORDER = ("REMOTE_ADDR",)` explicitly, so without a proxy a forged header is ignored. `prod.py` reads `X-Forwarded-For` first when `DJANGO_TRUST_X_FORWARDED_FOR` is on (default `true`, because Nginx overwrites the header).
  3. **Proxy count:** `AXES_PROXY_COUNT` stays env-driven with default `0`. Why `0` and not `1` is documented in `base.py` and `.env.example`, and pinned by a test.
- **Commit / change ref:**
  - `pyproject.toml:15`, `uv.lock`
  - `src/config/settings/base.py:162-168`
  - `src/config/settings/prod.py:32-35`
  - `.env.example`
- **Test evidence:**
  - `tests/integration/web/accounts/test_client_ip_behind_proxy.py` (6 tests, Nginx-faithful single-value header):
    - ipware importable by axes;
    - a different client isn't locked out;
    - the attacker stays locked;
    - attempts and audit rows record the real clients;
    - a forged header is ignored without the proxy;
    - proxy count 1 loses the address.
  - `tests/integration/config/test_prod_security_settings.py` (+3): prod reads the header by default with count 0, the switch turns it off, dev never reads it.
  - Real server with `config.settings.prod` (below). All green.
- **DevOps hand-off (required for go-live):** in PR #1, set `AXES_PROXY_COUNT=0` (not `1`) in `docs/deployment/pipeline-secrets.md:75` and in `deployment-plan` step 2, fix the comment in `nginx/conf.d/proxy_headers.inc:3`, and add `DJANGO_TRUST_X_FORWARDED_FOR` to the documented env (default `true`). Also update `docs/deployment/discovery-report.md:136`.
- Status: ✅ Resolved

---

### Previously reported bugs: re-verified on `ee862ec`

| ID | Original severity / priority | Source | Status | Evidence (re-run today) |
|----|------------------------------|--------|--------|-------------------------|
| BUG-001 | 🟢 Low / P3 | validation report 2026-10-21 | ✅ Fixed (`26fc1c5`) | `PASSED test_healthz.py::test_healthz_reports_read_only_data_directory_as_its_own_cause` (real read-only directory) |
| BUG-002 | 🟡 Medium / P2 | triage 2026-10-21-2 (listed in regression report) | ✅ Fixed (`26fc1c5`) | `PASSED test_healthz.py::test_healthz_returns_503_not_500_when_session_cookie_present_and_db_down` |
| BUG-003 | 🟡 Medium / P2 | triage 2026-10-21-2 (listed in regression report) | ✅ Fixed (`26fc1c5`) | `PASSED test_csrf_failure.py` ×4 (RO "Acces interzis", EN "Access denied", HTMX partial, view configured) |

Still-open, non-regression items listed in the regression report (`:130`) and re-checked:

| Item | Status today |
|------|--------------|
| Story 1.0 ISS-004 (HSTS → DevOps) | ✅ Resolved 2026-10-23 (env-driven, default off); review v2 approved |
| Story 1.3 ISS-004 (DEBUG-only URL walk → Story 1.6) | ✅ Resolved (`story-1.3-code-review-v1.md`: Fully Remediated 5/5) |
| `/en/…` URLs needing `LocaleMiddleware` (Story 1.4) | ✅ Delivered: the e2e journeys run on `/en/…` URLs (17/17) |

```
uv run pytest --cov=src --cov-branch --cov-fail-under=85 -> 1532 passed, 17 deselected | Total coverage: 100.00%
uv run pytest -m e2e                                     -> 17 passed, 1532 deselected in 8.04s
```

---

## Release Decision

**Recommendation**:
- [ ] ✅ APPROVE RELEASE (no blockers)
- [ ] ❌ BLOCK RELEASE (P0 bugs exist)
- [x] ⚠️ CONDITIONAL RELEASE (with documented issues)

**Rationale**: no P0 or Critical bugs, and every earlier bug is verified fixed.
- **CYCLE-1 build sign-off (local demo, direct access): may proceed.** BUG-004 can't occur without a reverse proxy.
- **Production (and UAT staging) go-live is blocked** until BUG-004 is fixed **and** PR #1's `AXES_PROXY_COUNT` matches the fix. Until then, any visitor can lock out any known account.

---

## Tracker

**Tracking**: Local. Nothing pushed (Phase 5.5 skipped: no GitHub or Azure DevOps tracking configured).

### Triage Summary

- **Total bugs**: 4 (1 open: BUG-004 🟠 P1; 3 verified fixed: BUG-001, BUG-002, BUG-003)
- **P0 blockers**: None
- **Go-live blocker (P1)**: BUG-004
- **Release**: CYCLE-1

---

## Next Steps
1. Assign BUG-004 (P1) to DEV: `aire-dev-remediate` from this report, TDD with an Nginx-faithful header test, environment-specific header trust.
2. DevOps: align `AXES_PROXY_COUNT` and the comments in PR #1 with the fix before `aire-devops-deploy`.
3. Re-validate after the fix: repeat run E's scenario against the real deployment path (`aire-qa-regression`).

---

# 🛠️ Remediation — 2026-10-23

**Developer**: DEV Agent
**Severity Scope**: P1 (BUG-004); P2/P3 none open (BUG-001–003 already verified fixed, skipped)
**Scenario**: QA Triage
**Stories Affected**: 1.2 (lockout client IP), 1.8 (audit IP, same helper)
**Branch**: `main`

## Issues Remediated

| ID | Severity | Story | File:Line | Summary | Resolution | Test Added |
|------|----------|-------|-----------|---------|------------|------------|
| BUG-004 | P1 High | 1.2 / 1.8 | `config/settings/base.py:162-168`, `prod.py:32-35`, `pyproject.toml:15` | Behind the proxy, lockouts and audit rows used the proxy IP (or None) | `django-ipware` + `X-Forwarded-For` read only in prod + proxy count 0 for Nginx's overwrite header | `test_client_ip_behind_proxy.py` (6) + prod settings (3) ✅ |

## Issues Deferred (with user consent)

None in the application. The deployment value belongs to DevOps (hand-off above). Until it lands, BUG-004 remains a **go-live condition**, not an open application defect.

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `pyproject.toml`, `uv.lock` | Modified | `django-ipware>=7.0` (8.0.0 + python-ipware 4.1.1) |
| `src/config/settings/base.py` | Modified | Explicit `AXES_IPWARE_META_PRECEDENCE_ORDER = ("REMOTE_ADDR",)`, `PROXIED_IP_HEADERS`, proxy-count comment |
| `src/config/settings/prod.py` | Modified | `DJANGO_TRUST_X_FORWARDED_FOR` (default `true`) → read `X-Forwarded-For` first |
| `.env.example` | Modified | `DJANGO_TRUST_X_FORWARDED_FOR=true`, `AXES_PROXY_COUNT=0` with reasons |
| `tests/integration/web/accounts/test_client_ip_behind_proxy.py` | New | 6 tests with the Nginx header shape |
| `tests/integration/config/test_prod_security_settings.py` | Modified | +3 prod/dev header-order tests |

## Patterns Applied

| Pattern | Where Applied | Notes |
|---------|---------------|-------|
| Configuration (§10) | `env_bool` switch in `prod.py` | Same pattern as `TRUST_INCOMING_REQUEST_ID`: trust a proxy-set header only where a proxy overwrites it |
| Security (§13) | `base.py` default | Never read a client-forgeable header without the proxy |
| Testing (§12) | Header-shape fixture `behind_nginx` | Tests send what Nginx sends, not a patched helper, so causes 2 and 3 are covered |

## Testing Summary

- **Targeted tests added**: 9
- **Full suite**: 1541/1541 passing (×3); e2e 17/17
- **Coverage**: 100% (target ≥85%)

**Test Output**:
```
--- RED (before the fix; constant only)
FAILED test_client_ip_behind_proxy.py::test_axes_can_resolve_proxied_clients
FAILED test_client_ip_behind_proxy.py::test_behind_nginx_a_lockout_only_blocks_the_attacking_client
FAILED test_client_ip_behind_proxy.py::test_behind_nginx_attempts_and_audit_rows_record_the_real_client
FAILED test_client_ip_behind_proxy.py::test_proxy_count_one_cannot_read_the_single_value_nginx_header
FAILED test_prod_security_settings.py::test_prod_reads_the_client_ip_from_the_proxy_header_by_default
5 failed, 12 passed in 1.91s
--- GREEN
targeted (incl. tests/integration/web/accounts/): 131 passed in 2.77s
full run 1: 1541 passed, 17 deselected in 16.81s | Total coverage: 100.00%
full run 2: 1541 passed, 17 deselected in 17.25s | Total coverage: 100.00%
full run 3: 1541 passed, 17 deselected in 17.34s | Total coverage: 100.00%
e2e:        17 passed, 1541 deselected in 7.84s
[ruff format]    194 files already formatted
[ruff check]     All checks passed!
[mypy]           Success: no issues found in 119 source files
[lint-imports]   Contracts: 2 kept, 0 broken.
[makemigrations] No changes detected
```

**Real server, `config.settings.prod`** (fresh DB, Nginx simulated: `X-Forwarded-For` one value, `X-Forwarded-Proto: https`, no `AXES_PROXY_COUNT` / `DJANGO_TRUST_X_FORWARDED_FOR` set, so defaults apply):
```
step 1-4: attacker 203.0.113.10 wrong password   -> 200
step 5:   attacker 203.0.113.10 wrong password   -> 429
step 6:   student 198.51.100.20 CORRECT password -> 302 /en/        (was 429: BUG-004 fixed)
step 7:   attacker 203.0.113.10 CORRECT password -> 429             (lockout still holds)
axes|ana|'203.0.113.10'|5
audit auth.login_failed '203.0.113.10' x6, auth.lockout '203.0.113.10' x2, auth.login '198.51.100.20'
server log "level": "ERROR" lines: 0
```

## Deviations from Report Suggestions

- None. The triage report's constraints (environment-specific trust, Nginx-faithful tests, the DevOps hand-off) were followed. The prod switch is named `DJANGO_TRUST_X_FORWARDED_FOR`, after `DJANGO_TRUST_INCOMING_REQUEST_ID`.

## Lessons Learned

1. An optional dependency that a library uses only "if importable" fails silently. Pin the behaviour with a test that checks the library actually sees it.
2. "Proxy count" means different things to different tools. Test with the exact header the proxy sends, not with an assumed one.

## Next Steps

- [ ] DevOps: PR #1 hand-off (`AXES_PROXY_COUNT=0`, comment, env docs). Then BUG-004 is cleared as a go-live blocker.
- [ ] Re-run validation/regression (`aire-qa-regression`): required for P1. Repeat the scenario on staging once deployed.

