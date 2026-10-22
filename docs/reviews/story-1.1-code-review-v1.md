# Code Review - Story 1.1: Error Handling & Observability

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

---

### ISS-003: Error pages must stay renderable without the database (note for Story 1.7) 🟢 Low

**Category**: Robustness (forward-looking)
**File**: `templates/layouts/base.html` (inherited by every `errors/*.html`)

**Issue**: Today the base layout and error templates use no DB-backed context (grep: no `user`/`request.user`). Story 1.7 will add the role-aware top bar to `base.html`, which reads `request.user` and so the session and DB. When the DB is down, `handler500` would then raise while rendering the 500 page, and Django would fall back to a bare `Server Error` response. The same issue BUG-002 fixed for `/healthz`.

**Suggested Fix** (to apply in Story 1.7): render error pages from a minimal layout (`layouts/error.html`) without the top bar, or guard the top bar so a `DatabaseError` while resolving the user renders it as anonymous. Add a test: 500 page with every DB cursor raising still renders the localized page and the reference id.

---

### ISS-004: Any client can choose its own `X-Request-ID` 🟢 Low

**Category**: Security (log integrity)
**File**: `src/infrastructure/web/common/middleware.py` (`RequestIdMiddleware.__call__`)

**Issue**: An incoming id is accepted from any client once it matches `^[A-Za-z0-9-]{8,64}$`. That's correct for a request id set by the reverse proxy, but a client can also reuse another request's id to make log correlation ambiguous during an incident.

**Suggested Fix** (DevOps, small code change): accept the incoming header only behind the trusted proxy (setting `TRUST_INCOMING_REQUEST_ID`, false by default, true in prod behind the proxy that sets it), and configure the proxy to overwrite `X-Request-ID`. Record it in `aire-devops-discover`.

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
