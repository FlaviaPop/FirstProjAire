# Bug Triage Report

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
