# Bug Triage Report

**Date**: 2026-10-23
**Raised By**: QA (via `aire-raise-defect`, one-by-one, confirmed by the user)
**Triage Status**: 🟡 Raised, awaiting `aire-qa-triage`. Severity and priority below are as raised; P1 was proposed and accepted by the user.
**Source**: found during the 2026-10-23 remediation pass (the `python-ipware` hand-off in `docs/status.md`), then reproduced end to end before raising (evidence below)
**Code Under Test**: `main` @ `71d1ee5` (CYCLE-1 complete; 1532/1532 tests passing)
**Tracking**: Local (`docs/status.md` → Project Tracking); no external issue
**BUILDID**: CYCLE-1

---

## Summary

**Total Bugs**: 1
**Critical**: 0 🔴
**High**: 1 🟠 (Major / P1)
**Medium**: 0 🟡
**Low**: 0 🟢

**Release Blockers**: 1 for go-live behind the reverse proxy (BUG-004). It doesn't affect local development or direct access.

---

## Bug Details

### BUG-004: [Login lockout] Behind the reverse proxy, lockouts key on the proxy's IP: any client can lock any username out 🟠

#### Environment
**Build:** `main` @ `71d1ee5` | **Env:** local, `config.settings.dev`, with `AXES_PROXY_COUNT=1` (the staging/prod value from the PR #1 deployment design). The lockout settings live in `base.py`, so every environment behaves the same. | **OS:** macOS (Darwin 25.6) | **Client:** HTTP script (urllib); Nginx simulated by setting `X-Forwarded-For` as `nginx/conf.d/proxy_headers.inc` does. | **URL:** `/en/accounts/login/`

#### Preconditions
- The app runs behind one reverse proxy, so every request reaches Django from the proxy's address (here 127.0.0.1), with the real client in `X-Forwarded-For`.
- An active Student account `ana` with password `pilot-pass-123`.
- `django-ipware` isn't installed (`importlib.util.find_spec('ipware')` → `None`; it isn't in `pyproject.toml`).

#### Steps to Reproduce
1. Start the app with `AXES_PROXY_COUNT=1`.
2. As client **203.0.113.10** (`X-Forwarded-For: 203.0.113.10`), submit the sign-in form for `ana` with a wrong password 5 times.
3. As a different client, **198.51.100.20** (`X-Forwarded-For: 198.51.100.20`), submit the sign-in form for `ana` with the **correct** password.
4. Inspect `axes_accessattempt` and `audit_log`.

#### Expected Result
- Lockouts are **per username + client IP** (architecture; Story 1.2 `AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]`), with the client IP taken from the trusted proxy's `X-Forwarded-For` (`AXES_PROXY_COUNT=1`).
- Step 2 locks out only `ana` @ 203.0.113.10.
- Step 3 succeeds: 302 to `/en/`.
- The access attempt and the audit rows record 203.0.113.10 and 198.51.100.20.

#### Actual Result
```
step 1-4: attacker 203.0.113.10 wrong password -> 200
step 5:   attacker 203.0.113.10 wrong password -> 429
step 6:   student 198.51.100.20 CORRECT password -> 429      <- legitimate user locked out
axes_accessattempt: ana|127.0.0.1|5
audit_log: auth.login_failed|127.0.0.1 (x4), auth.lockout|127.0.0.1, auth.login_failed|127.0.0.1,
           auth.lockout|127.0.0.1, auth.login_failed|127.0.0.1   (every row has the proxy address)
ipware importable: False
```

**Cause:** django-axes 8.3.1 resolves the client IP with `ipware.ip.get_client_ip(..., proxy_count=AXES_IPWARE_PROXY_COUNT)` only when `ipware` is importable. Otherwise it falls back to `request.META["REMOTE_ADDR"]` (`axes/helpers.py:206-225`). So `AXES_PROXY_COUNT` (`src/config/settings/base.py:156`) has no effect. The audit receivers use the same helper (`src/infrastructure/persistence/audit/receivers.py:27`).

**Impact behind the proxy:**
- every client shares one IP, so the lockout is effectively per username;
- anyone who knows a username (student, teacher or admin) can lock it out for 15 minutes, repeatedly;
- the audit log and the admin lockout screen show the proxy's address instead of the client's.

#### Severity / Priority / Reproducibility
**Severity:** Major | **Priority:** P1 | **Reproducibility:** Always (behind a proxy); not visible with direct access, e.g. local dev.

#### Affected Story / Component
- **Story 1.2** Login & Session Security: axes lockout keying, `AXES_IPWARE_PROXY_COUNT`.
- **Story 1.8** Audit Log: `ip_address` of auth events.
- No tracker ID (local tracking).

#### Notes for triage / remediation (not a fix decision)
- Not a duplicate of 1.2 review ISS-005 (password spraying across usernames, mitigated by the Nginx rate limit). That's a different failure.
- The `docs/status.md` hand-off named `python-ipware`. Axes actually imports the `django-ipware` package (module `ipware`); the note is corrected.

---
Raised via AIRE `aire-raise-defect` by QA. Drafted with AI (Claude Opus 5.5).

---

## Tracker

**Tracking**: Local. Defect recorded in this report; no GitHub or Azure DevOps issue created.

## Next Steps

1. `aire-qa-triage`: classify BUG-004 and confirm P1 and the release decision for go-live.
2. `aire-dev-remediate` from this report (TDD: a failing test showing the client IP behind one proxy, then the fix).
