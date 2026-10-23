# Code Review - Story 1.1: Error Handling & Observability

> ## 🛠️ Remediation Status: ✅ Resolved
> - **Remediated**: 2026-10-23 by DEV Agent (deferred item; earlier passes on 2026-10-22)
> - **Fixed**: 4 issue(s) — 🔴 0 / 🟠 0 / 🟡 1 / 🟢 3 (ISS-004 in this pass; ISS-003 resolved earlier as a binding hand-off note in Story 1.7)
> - **Deferred (with user consent)**: 0
> - **Tests**: 1532/1532 passing (+17 e2e) | **Coverage**: 100% | **Linter**: clean
> - **Scenario**: Code Review

**Date**: 2026-10-22
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
**Code reviewed at**: `main` @ `ccd8819`. Story 1.1's commit `43aa67a` merged in `e3deb8e`, plus later fixes to its files: BUG-002 (`process_view`), BUG-003 (`csrf_failure`), `LOG_LEVEL` in dev (1.0 ISS-005).

---

## Review Summary

**Components Reviewed**:
- `src/domain/common/{errors,clock,language}.py`, `src/infrastructure/system_clock.py`
- `src/infrastructure/web/common/{middleware,errors,htmx}.py`
- `src/infrastructure/logging/{json_formatter,request_context,stdout_handler}.py`
- `templates/errors/*.html` (6 pages + `_error.html` + `_partial.html`)
- `LOGGING` / `MIDDLEWARE` in `base.py`, `handler400/403/404/500` in `urls.py`
- `tests/integration/web/common/*`, `tests/unit/domain/common/*`
- `docs/stories-implemented/story-1.1-review.md`

**Lines of Code**: ~380 production (incl. templates); ~900 test
**Tests Reviewed**: Yes (114 in the story's test packages, all passing)
**Coverage**: 100% for every Story 1.1 module (statements + branches), re-run by the reviewer

**Overall Assessment**: A solid cross-cutting foundation:
- one place maps `DomainError` → HTTP
- localized error pages, with HTMX partials and the same status
- request-id correlation that survives Django's late `django.request` logging
- strict request-id validation
- no query strings in logs
- a stdout handler that stays correct when stdout is replaced

Every story test and gate is green. No blockers or high issues. The main comment: the JSON formatter serialises *any* `extra` field, so the patterns §9 "never log" list isn't enforced. The lows cover a 422 that can turn into a 500, a forward-looking note for Story 1.7's layout, and trust in client-supplied request ids.

### Evidence verification (re-run by reviewer)

```
$ uv run pytest -q tests/integration/web/common tests/unit/domain/common   → 114 passed in 0.61s
$ uv run pytest -q --cov=src --cov-branch                                  → 717 passed
src/domain/common/errors.py                        22  0 2 0 100%
src/infrastructure/logging/json_formatter.py       13  0 2 0 100%
src/infrastructure/logging/request_context.py      13  0 2 0 100%
src/infrastructure/logging/stdout_handler.py        7  0 0 0 100%
src/infrastructure/system_clock.py                  5  0 0 0 100%
src/infrastructure/web/common/errors.py            29  0 0 0 100%
src/infrastructure/web/common/htmx.py               3  0 0 0 100%
src/infrastructure/web/common/middleware.py        55  0 4 0 100%

Probes (reviewer script, config.settings.test):
extra fields serialised: ['count', 'date_of_birth', 'full_name', 'password']
violation missing param -> raises KeyError (would become a 500 instead of a 422)
violation ok -> At most 10 items allowed.
grep user/request.user in layouts/base.html + errors/*.html → no matches
```
Real-server behaviour (404/500 pages with request id and JSON logs, `DEBUG=False`) was also exercised in the wave-2 merge smoke test, BUG-002/003 verification and the 2026-10-21 regression run.

---

## Checklist Results

### Correctness
- [x] ✅ AC 1–16: domain errors (`PolicyViolation([])` raises), Clock/Language, `SystemClock` aware UTC, MRO-ordered status mapping, handlers, pages + HTMX partials, message resolution, 422 lists all violations, 500 shows only the reference, `RequestIdMiddleware` first with id validation, JSON lines with context, no query strings, `domain_error` INFO and 500 ERROR logs, RO/EN entries, coverage
- [x] ⚠️ A missing violation parameter raises `KeyError` while rendering a 422 → 500 (ISS-002)

### Pattern Adherence
- [x] ✅ Error handling §8: one mapping table; domain errors carry stable codes
- [x] ⚠️ Logging §9 "never log" list isn't enforced by the formatter (ISS-001)
- [x] ✅ HTMX §7.4: single `is_htmx` detector; response conventions §7.5
- [x] ✅ Naming (`noqa: N818` with reason for architecture-fixed names); small functions

### Testing
- [x] ✅ JSON parsed from captured stdout (`capfd`); request id matched across log, header and page; DEBUG=False 500 page
- [x] ✅ Coverage 100%
- [x] ⚠️ No test pins redaction of sensitive `extra` fields (added with ISS-001)

### Documentation
- [x] ✅ *Why* comments: stale stdout stream, Django's late `django.request` lines, `request` never serialised
- [x] ✅ No TODO/FIXME

### Security & Privacy
- [x] ✅ No exception text or stack trace in any page; 500 page shows only the reference id
- [x] ✅ `path` only, never the query string; `request` objects never serialised
- [x] ✅ Request-id format validated before echoing (no header/log injection)
- [x] ⚠️ Sensitive `extra` keys are written as-is (ISS-001)
- [x] ⚠️ Any client can choose a valid `X-Request-ID` (ISS-004)

### Performance
- [x] ✅ One `perf_counter` and one log line per request; ContextVars are reset in `finally`

### SOLID / Anti-Monolith
- [x] ✅ SRP: formatter / context filter / handler / middleware / renderer are separate; OCP: `ERROR_MESSAGES` is extended by later stories without editing the renderer

---

## Issues Found

### ISS-001: JSON log formatter serialises any `extra` field, including passwords and personal data 🟡 Medium

**Category**: Security / Privacy
**File**: `src/infrastructure/logging/json_formatter.py` (`payload.update(...)`)
**Pattern Reference**: patterns §9 "Never log: passwords or hashes, session/CSRF tokens, SECRET_KEY, full names, dates of birth, test/exercise answers, block reasons, request bodies"

**Issue**:
Only the `request` attribute is excluded. Every other `extra` key is written verbatim (probe: `password`, `date_of_birth`, `full_name` all serialised). Today no code logs those, but there's no guard. Story 1.9 (account management) and CYCLE-3 (answers, block reasons) will log around exactly this data, and stdout logs are shipped off-box. Story 1.8 already guards audit metadata the same way.

**Suggested Fix**: Redact rather than raise, because logging must never fail a request:
```python
from infrastructure.logging.sensitive import is_sensitive_key  # shared with the audit guard

REDACTED = "[redacted]"
...
for key, value in vars(record).items():
    if key in _STANDARD or key in _CONTEXT or key in _NEVER_SERIALISED:
        continue
    payload[key] = REDACTED if is_sensitive_key(key) else value
```
- Move `is_sensitive_metadata_key` / `FORBIDDEN_METADATA_FRAGMENTS` from `persistence/audit/repositories.py` into one shared module (e.g. `infrastructure/logging/sensitive.py`) so audit and logs share the same rule.
- For logs, also cover `full_name`, `first_name`, `last_name`, `reason` and `body`.
- Tests: the formatter redacts each sensitive variant, and keeps `count`, `status`, `code`.

**Why This Matters**: Logs leave the server and are retained elsewhere. A single careless `extra` would leak a child's personal data or a credential.


**Resolution** (2026-10-22, DEV):
- Fix: new shared module `infrastructure/logging/sensitive.py` (`SENSITIVE_FRAGMENTS`, `is_sensitive_key`, `is_sensitive_log_key`). `JsonFormatter` writes `"[redacted]"` for any sensitive `extra` key; it never raises. Logs additionally cover `full_name`, `first_name`, `last_name`, `body`, `block_reason`, `moderation_reason`. Django's CSRF `reason` stays visible (operational, not personal). The Story 1.8 audit guard now uses the same rule (no behaviour change; its tests pass)
- Commit / change ref: `src/infrastructure/logging/sensitive.py` (new), `src/infrastructure/logging/json_formatter.py` (`REDACTED`, `payload.update`), `src/infrastructure/persistence/audit/repositories.py` (import)
- Test evidence: `tests/unit/infrastructure/test_log_redaction.py` (18 sensitive keys redacted, 7 ordinary keys kept, fixed keys never redacted) — failed before the fix. Real server: CSRF failure line keeps `reason: "CSRF cookie not set."`; `0` log lines contain the posted password
- Status: ✅ Resolved

---

### ISS-002: A violation missing a message parameter turns a 422 into a 500 🟢 Low

**Category**: Correctness (robustness)
**File**: `src/infrastructure/web/common/errors.py` (`violation_message`)

**Issue**: `str(template).format(**violation.params)` raises `KeyError` when a registered message uses a placeholder the violation doesn't supply (probe). That's a coding mistake in a later story, but the user then sees a 500 instead of the validation feedback, and the other violations on the page are lost too.

**Suggested Fix**:
```python
class _KeepMissing(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"

def violation_message(violation: Violation) -> str:
    template = str(ERROR_MESSAGES.get(violation.code, violation.code))
    return template.format_map(_KeepMissing(violation.params))
```
Optionally log a WARNING `error_message.missing_param` with the code. Test: a missing param renders the template with `{limit}` left in place, and the response stays 422.


**Resolution** (2026-10-22, DEV):
- Fix: `violation_message` uses `format_map` with `_KeepMissingParams`, so a missing placeholder stays visible (`{limit}`) and logs `WARNING error_message.missing_param` with `code` and `param`
- Commit / change ref: `src/infrastructure/web/common/errors.py` (`_KeepMissingParams`, `violation_message`)
- Test evidence: `test_error_middleware.py::test_violation_missing_a_message_param_still_renders_422` (failed before the fix with `assert 500 == 422`; now 422, both violations listed, warning asserted)
- Status: ✅ Resolved

---

### ISS-003: Error pages must stay renderable without the database (note for Story 1.7) 🟢 Low

**Category**: Robustness (forward-looking)
**File**: `templates/layouts/base.html` (inherited by every `errors/*.html`)

**Issue**: Today the base layout and error templates use no DB-backed context (grep: no `user`/`request.user`). Story 1.7 will add the role-aware top bar to `base.html`, which reads `request.user` and so the session and DB. When the DB is down, `handler500` would then raise while rendering the 500 page, and Django would fall back to a bare `Server Error` response. The same issue BUG-002 fixed for `/healthz`.

**Suggested Fix** (to apply in Story 1.7): render error pages from a minimal layout (`layouts/error.html`) without the top bar, or guard the top bar so a `DatabaseError` while resolving the user renders it as anonymous. Add a test: 500 page with every DB cursor raising still renders the localized page and the reference id.


**Resolution** (2026-10-22, DEV):
- Fix: a forward-looking risk with no defect in current code (error templates use no DB-backed context today). Recorded as a **binding hand-off** at the top of Story 1.7's Acceptance Criteria: minimal error layout or a guarded top bar, plus a "500 page with every DB cursor raising" test. Story 1.4's `/` redirect tests and the language-switcher inclusion were added there as well
- Commit / change ref: `docs/plans/stories/epic-1-story-1.7-App-Shell-and-Role-Homes.md` ("Hand-offs from implemented stories")
- Test evidence: documentation (non-testable now); grep confirms `layouts/base.html` and `errors/*.html` reference no `user`/`request.user`
- Status: ✅ Resolved

---

### ISS-004: Any client can choose its own `X-Request-ID` 🟢 Low

**Category**: Security (log integrity)
**File**: `src/infrastructure/web/common/middleware.py` (`RequestIdMiddleware.__call__`)

**Issue**: An incoming id is accepted from any client once it matches `^[A-Za-z0-9-]{8,64}$`. That's correct for a request id set by the reverse proxy, but a client can also reuse another request's id to make log correlation ambiguous during an incident.

**Suggested Fix** (DevOps, small code change): accept the incoming header only behind the trusted proxy (setting `TRUST_INCOMING_REQUEST_ID`, false by default, true in prod behind the proxy that sets it), and configure the proxy to overwrite `X-Request-ID`. Record it in `aire-devops-discover`.


**Deferral** (2026-10-22, DEV): deferred with user consent to `aire-devops-discover`: trust `X-Request-ID` only from the reverse proxy (setting + proxy overwrites the header). Still open.

**Resolution** (2026-10-23, DEV):
- Fix: new setting `TRUST_INCOMING_REQUEST_ID`. It is `False` in base/dev/test, so a client's `X-Request-ID` is ignored and a fresh id generated. In prod it comes from `DJANGO_TRUST_INCOMING_REQUEST_ID` (default `true`), because Nginx always overwrites the header with `$request_id` (PR #1, `nginx/conf.d/proxy_headers.inc`). The header validation still applies when trusted.
- Commit / change ref: `src/infrastructure/web/common/middleware.py:38-42`, `src/config/settings/base.py:123-125`, `src/config/settings/prod.py:29-31`, `src/config/settings/env.py:24-35` (`env_bool`)
- Test evidence:
  - `tests/integration/web/common/test_request_id_logging.py:82` (client id ignored by default), and the reuse/boundary/invalid tests now run `behind_proxy`;
  - `tests/integration/config/test_prod_security_settings.py` (prod default on, env off, dev never trusts);
  - `tests/unit/config/test_env.py:54-80` (`env_bool`, 15 cases).
  - All green.
- Status: ✅ Resolved

---

## Issue Summary

| # | ID | Severity | Category | File | Status |
|---|-----|----------|----------|------|--------|
| 1 | ISS-001 | 🟡 Medium | Security / Privacy | `logging/json_formatter.py` | Should Fix |
| 2 | ISS-002 | 🟢 Low | Correctness | `web/common/errors.py` | Optional |
| 3 | ISS-003 | 🟢 Low | Robustness | `layouts/base.html` | Note for Story 1.7 |
| 4 | ISS-004 | 🟢 Low | Security (log integrity) | `web/common/middleware.py` | Defer to DevOps |

**Summary**:
- Blockers: 0
- High: 0
- Medium: 1
- Low: 3

---

## What Was Done Well

1. ✅ Django writes `django.request` 4xx/5xx lines after the middleware chain has reset the ContextVars. The `request.log_context` snapshot keeps those lines correlated, a subtle problem found and solved on a real server.
2. ✅ `StdoutHandler` binds `sys.stdout` at emit time, fixing a real "logs go nowhere under supervisors/pytest" trap.
3. ✅ Request-id validation before echoing closes header and log injection.
4. ✅ One `_STATUS_BY_ERROR` table in MRO order: the HTTP mapping lives in exactly one place.
5. ✅ Error pages never reveal exception text; the 500 page shows only a reference.

---

## Approval Status

**Decision**: ⚠️ APPROVED WITH COMMENTS

**Reason**: No blockers or high issues. ISS-001 should be fixed before Story 1.9 and CYCLE-3 start logging around personal data. ISS-002 is a small robustness fix; ISS-003 is a note for Story 1.7; ISS-004 belongs to DevOps.

**Next Steps**:
1. `aire-dev-remediate` for ISS-001 (+ optionally ISS-002)
2. Carry ISS-003 into Story 1.7, and ISS-004 into `aire-devops-discover`

---

## Sign-Off

**Reviewer**: REVIEWER Agent
**Date**: 2026-10-22
**Signature**: Approved with comments

---

# 🛠️ Remediation — 2026-10-22

**Developer**: DEV Agent
**Severity Scope**: 🟡 ISS-001 + 🟢 ISS-002 + 🟢 ISS-003 (hand-off note); ISS-004 deferred; scope confirmed by the user
**Scenario**: Code Review
**Stories Affected**: 1.1 (and the Story 1.8 audit guard, which now shares the same rule)
**Branch**: `main`

## Issues Remediated

| ID | Severity | Story | File | Summary | Resolution | Test Added |
|------|----------|-------|------|---------|------------|------------|
| ISS-001 | 🟡 Medium | 1.1 | `logging/sensitive.py`, `logging/json_formatter.py` | Sensitive `extra` fields logged | Redacted via one shared rule (also used by audit) | `test_log_redaction.py` (26) ✅ |
| ISS-002 | 🟢 Low | 1.1 | `web/common/errors.py` | Missing param → 500 | `format_map` keeps `{param}`; WARNING | `test_error_middleware.py` (1) ✅ |
| ISS-003 | 🟢 Low | 1.1→1.7 | Story 1.7 file | Error pages vs DB-backed top bar | Binding hand-off in Story 1.7 | n/a (docs) |

## Issues Deferred (with user consent)

| ID | Severity | Story | Reason |
|----|----------|-------|--------|
| ISS-004 | 🟢 Low | 1.1 | Trusted `X-Request-ID` from the proxy only: DevOps |

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `src/infrastructure/logging/sensitive.py` | New | Shared sensitive-key rule |
| `src/infrastructure/logging/json_formatter.py` | Modified | Redaction |
| `src/infrastructure/persistence/audit/repositories.py` | Modified | Uses the shared rule |
| `src/infrastructure/web/common/errors.py` | Modified | Missing-param tolerant formatting |
| `tests/unit/infrastructure/test_log_redaction.py` | New | 26 tests |
| `tests/integration/web/common/test_error_middleware.py` | Modified | +1 test, +1 route |
| `docs/plans/stories/epic-1-story-1.7-App-Shell-and-Role-Homes.md` | Modified | Hand-offs (1.1 ISS-003, 1.4) |

## Patterns Applied

| Pattern | Where Applied | Notes |
|---------|---------------|-------|
| Logging §9 never-log list | formatter + audit | One rule, two consumers; redact in logs, reject in audit |
| Error handling §8 | `violation_message` | Degrade gracefully; never turn a 4xx into a 5xx |

## Testing Summary

- **Targeted tests added**: 27
- **Full suite**: 744/744 passing (3 runs)
- **Coverage**: 100% (target ≥85%); domain 100%; application 100%
- **Gates**: ruff format/check clean · mypy 0 issues (95 files) · import-linter 2/2 kept · `makemigrations --check` no changes

**Test Output** (verbatim, filtered):
```
collected 744 items
tests/integration/web/common/test_error_middleware.py .................. [ 31%]
tests/unit/infrastructure/logging/test_json_formatter.py ............    [ 92%]
tests/unit/infrastructure/test_log_redaction.py ........................ [ 99%]
src/infrastructure/logging/json_formatter.py                 15      0      2      0   100%
src/infrastructure/logging/sensitive.py                       9      0      0      0   100%
src/infrastructure/web/common/errors.py                      37      0      0      0   100%
TOTAL                                                       681      0     74      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
============================= 744 passed in 7.15s ==============================
```

**Real server**:
```
POST without CSRF -> 403
{'event': 'csrf.failure', 'level': 'WARNING', 'reason': 'CSRF cookie not set.', 'request_id': '1b1b38d1…'}
log lines containing the posted password: 0
```

## Deviations from Report Suggestions

- ISS-001: `reason` is **not** treated as sensitive in general (Django's CSRF reason is operational); only `block_reason` / `moderation_reason` are (patterns §9: "block reasons"). The shared module lives under `infrastructure/logging/` as suggested.
- ISS-003: resolved as a binding hand-off rather than code, because the risk only arises when Story 1.7 adds the top bar.

## Lessons Learned

1. Guards for "never log / never store" belong in one module shared by every sink, or they drift apart, as the audit and log guards had.
2. Error rendering must degrade gracefully at every layer: a 4xx page that can throw is a 5xx page in disguise.

## Next Steps

- [ ] Re-request code review (`aire-review-code`): optional (no 🔴 fixed)
- [ ] ISS-004 in `aire-devops-discover`; ISS-003 is checked when Story 1.7 is implemented

---

# 🛠️ Remediation — 2026-10-23

**Developer**: DEV Agent
**Severity Scope**: 🟢 Low (ISS-004, the previously deferred item)
**Scenario**: Code Review
**Stories Affected**: 1.1
**Branch**: `main`

Combined pass: the four DevOps-deferred review items (1.0 ISS-004, 1.1 ISS-004, 1.2 ISS-005, 1.8 ISS-004) were remediated together on `main`, scope confirmed by the user.

## Issues Remediated

| ID | Severity | Story | File:Line | Summary | Resolution | Test Added |
|------|----------|-------|-----------|---------|------------|------------|
| ISS-004 | 🟢 Low | 1.1 | `web/common/middleware.py:38-42` | Any client could choose its own `X-Request-ID` | Reused only when `TRUST_INCOMING_REQUEST_ID` (prod, behind Nginx) | `test_request_id_logging.py:82` + prod settings tests ✅ |

## Issues Deferred (with user consent)

None.

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `src/infrastructure/web/common/middleware.py` | Modified | Reuse the incoming id only when trusted |
| `src/config/settings/base.py` | Modified | `TRUST_INCOMING_REQUEST_ID = False` |
| `src/config/settings/prod.py` | Modified | `env_bool("DJANGO_TRUST_INCOMING_REQUEST_ID", default=True)` |
| `src/config/settings/env.py` | Modified | `env_bool()`: true/false/1/0, anything else is a start-up error naming the variable |
| `.env.example` | Modified | Variable documented (placeholder) |
| `tests/integration/web/common/test_request_id_logging.py` | Modified | New default-ignore test; `behind_proxy` fixture for reuse tests |
| `tests/integration/web/common/test_error_middleware.py` | Modified | 500-reference test sets the proxy trust |
| `tests/integration/config/test_prod_security_settings.py` | New | Prod switches loaded in a subprocess (shared with 1.0 ISS-004) |
| `tests/unit/config/test_env.py` | Modified | `env_bool` cases |

## Testing Summary

- **Red first**: `test_incoming_request_id_is_ignored_unless_behind_the_proxy` and the 3 prod trust tests failed; `test_env.py` failed to import `env_bool`.
- **Green**: targeted 59 passed; full suite below.

**Test Output** (whole combined pass):
```
[full suite x3]  1532 passed, 17 deselected (13.87s / 14.30s / 14.58s) | Total coverage: 100.00%
[e2e]            17 passed, 1532 deselected in 7.11s
[ruff format]    193 files already formatted
[ruff check]     All checks passed!
[mypy]           Success: no issues found in 119 source files   (--no-incremental)
[lint-imports]   Contracts: 2 kept, 0 broken.
[makemigrations] No changes detected
```

## Deviations from Report Suggestions

- None. Suggested setting name used; the proxy side was already delivered by DevOps (PR #1).

## Lessons Learned

1. When a header's trustworthiness depends on the deployment, make trust an explicit setting that is off by default, rather than a validation rule alone.

## Next Steps

- [ ] Re-request code review (`aire-review-code`) — optional (no 🔴 fixed)
- [ ] DevOps (PR #1): add the new env names to `docs/deployment/pipeline-secrets.md` / compose env, and schedule `manage.py purge_audit_log` daily (systemd timer)
