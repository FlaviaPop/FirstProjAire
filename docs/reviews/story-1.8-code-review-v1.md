# Code Review - Story 1.8: Audit Log

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
**Code reviewed at**: `main` @ `1547237` (Story 1.8 commit `dd07213`, merged in `fb28aab`)
**Note**: the same agent session implemented this story. The review was therefore done adversarially: every guarantee was re-probed with a script rather than trusted from the self-review.

---

## Review Summary

**Components Reviewed**:
- `src/application/common/{audit,unit_of_work}.py`
- `src/application/accounts/record_security_event.py`
- `src/infrastructure/persistence/audit/{apps,models,repositories,receivers}.py` + migration `0001`
- `src/infrastructure/persistence/common/unit_of_work.py`
- `container.record_security_event()`
- `tests/fakes/*`
- `tests/unit/application/accounts/test_record_security_event.py`
- `tests/integration/persistence/audit/*` (3 files)
- `docs/stories-implemented/story-1.8-review.md`

**Lines of Code**: ~200 production, ~450 test
**Tests Reviewed**: Yes (37 in the story's files, all passing)
**Coverage**: 100% for every Story 1.8 module (statements + branches), re-run by the reviewer

**Overall Assessment**: Clean ports and adapters. The application layer is framework-free, the UoW never swallows exceptions, the clock is injected, and the fakes are reusable. Signal receivers are connected once and are best-effort with an alertable log line. Append-only enforcement holds through every public ORM path. No blockers or high issues. One medium: the sensitive-metadata guard is too literal (exact, case-sensitive keys) for a log about children's data. The lows cover a documented ORM back door, a privacy design question (verbatim failed usernames), and audit-table growth under attack.

### Evidence verification (re-run by reviewer)

```
$ uv run pytest -q tests/unit/application/accounts/test_record_security_event.py tests/integration/persistence/audit
37 passed in 0.27s
$ uv run pytest -q --cov=src --cov-branch                → 677 passed
src/application/common/audit.py                      4  0 0 0 100%
src/application/common/unit_of_work.py               2  0 0 0 100%
src/infrastructure/persistence/audit/apps.py         7  0 0 0 100%
src/infrastructure/persistence/audit/models.py      31  0 2 0 100%
src/infrastructure/persistence/audit/receivers.py   30  0 2 0 100%
src/infrastructure/persistence/audit/repositories.py 13 0 2 0 100%
src/infrastructure/persistence/common/unit_of_work.py 9 0 0 0 100%
$ uv run mypy                     → Success: no issues found in 92 source files
$ PYTHONPATH=src uv run lint-imports → Contracts: 2 kept, 0 broken.

Probes (reviewer script, config.settings.test):
== metadata guard variants
  'password'       rejected
  'Password'       ACCEPTED
  'PASSWORD'       ACCEPTED
  'new_password'   ACCEPTED
  'user_dob'       ACCEPTED
  'answer_text'    ACCEPTED
  'Token'          ACCEPTED
  'date_of_birth'  rejected
== append-only bypass routes
  objects.bulk_update                      blocked (PermissionError)
  objects.update_or_create (existing)      blocked (PermissionError)
  objects.filter().update                  blocked (PermissionError)
  _base_manager.filter().update            NOT blocked
  row action now: tampered
== what a failed sign-in stores
  actor_username stored for a mistyped password-in-username: Ana2018!secret
```

---

## Checklist Results

### Correctness
- [x] ✅ AC 1–11: ports, use case, model fields/indexes, append-only via the public API, clock, receivers with `dispatch_uid`, best-effort `DatabaseError` handling, UoW, container, fakes, coverage
- [x] ✅ Real login flow: 1 row per event; 5 failures → 5 `login_failed` + 1 `lockout`; cool-off attempts recorded as `lockout`, never `login`
- [x] ✅ Account deletion keeps rows with `actor_username` (SET_NULL)
- [x] ⚠️ Sensitive-metadata guard is exact and case-sensitive (ISS-001)

### Pattern Adherence
- [x] ✅ Use case §5 / Repository + UoW §6.3 / Adapter §15 / Fakes §12.2
- [x] ✅ Logs vs audit §9: the failure log line has only the event name, never exception text
- [x] ✅ Composition root; no singletons

### Testing
- [x] ✅ Unit (fakes), integration (signals), real-view flow, UoW commit/rollback
- [x] ✅ Coverage 100%
- [x] ⚠️ No test pins the metadata guard against case and prefix variants (fixed with ISS-001)

### Documentation
- [x] ✅ Docstrings on ports and the use case; *why* comments (best-effort decision, `_base_manager` note)
- [x] ✅ Self-review documents the hand-off to 1.4 and the cool-off behaviour accurately

### Security & Privacy
- [x] ✅ Identity from the auth framework only; passwords never read (cleansed credentials; only `username`)
- [x] ✅ Append-only through `objects` (update, delete, bulk_update, update_or_create all blocked)
- [x] ⚠️ `_base_manager` can still update rows (needed by the deletion collector; documented, but not guarded) (ISS-002)
- [x] ⚠️ Failed sign-ins store the typed username verbatim, which may be a mistyped password (ISS-003, design)
- [x] ⚠️ Every attempt writes a row; under spraying or lockout spam the table grows without bound (ISS-004)

### Performance
- [x] ✅ Indexes `(action, created_at)`, `(actor, created_at)`; one INSERT per event

### SOLID / Anti-Monolith
- [x] ✅ SRP across use case / port / adapter / receivers; DIP via ports + container; OCP: later stories audit through the same port

---

## Issues Found

### ISS-001: Sensitive-metadata guard is exact-match and case-sensitive 🟡 Medium

**Category**: Security / Privacy
**File**: `src/infrastructure/persistence/audit/repositories.py:8-11, 37-38`
**Pattern Reference**: patterns §9 "Never log: passwords or hashes, … dates of birth, test/exercise answers"; Story 1.8 AC 5

**Issue**:
`FORBIDDEN_METADATA_KEYS & set(data)` only rejects the seven exact lowercase keys. `Password`, `PASSWORD`, `new_password`, `user_dob`, `answer_text` and `Token` are all accepted (probe above). Later stories write metadata through this port (test submissions, moderation, account changes), and a natural key like `new_password` or `answer_text` would silently store sensitive data about children in an append-only table that can't be cleaned through the application.

**Current Code**:
```python
if leaked := FORBIDDEN_METADATA_KEYS & set(data):
    raise ValueError(f"Forbidden audit metadata keys: {sorted(leaked)}")
```

**Suggested Fix**:
```python
FORBIDDEN_METADATA_FRAGMENTS = ("password", "passwd", "secret", "token", "date_of_birth", "dob",
                                "birth", "answer", "response")

def _is_sensitive(key: str) -> bool:
    normalised = key.casefold().replace("-", "_")
    return any(fragment in normalised for fragment in FORBIDDEN_METADATA_FRAGMENTS)

if leaked := sorted(k for k in data if _is_sensitive(k)):
    raise ValueError(f"Forbidden audit metadata keys: {leaked}")
```
Add parametrised tests for case, prefix and suffix variants (`Password`, `new_password`, `user_dob`, `answer_text`, `Token`) plus a few allowed keys (`score`, `language`, `status`) so the guard can't over-block.

**Why This Matters**: The audit log is append-only by design, so a leak can't be undone by the platform. A defence that only matches exact strings gives a false sense of safety.

---

### ISS-002: `_base_manager` can update audit rows; no guard against application use 🟢 Low

**Category**: Security (defence in depth)
**File**: `src/infrastructure/persistence/audit/models.py` (comment above `actor`)

**Issue**: Django's deletion collector needs `_base_manager` to set `actor_id = NULL` when an account is deleted, so it isn't (and can't be) blocked in Python. The model comment explains this, but nothing stops application code from using `AuditLogModel._base_manager.filter(...).update(...)` (probe: `row action now: tampered`). The architecture only requires append-only "from the application", so this meets the spec, but it relies on convention.

**Suggested Fix** (either or both):
- A negative-space test that fails if `_base_manager` or `.raw(` is referenced on `AuditLogModel` anywhere in `src/` outside `models.py`.
- DB-level enforcement with a reversible `RunSQL` migration adding SQLite triggers: `BEFORE DELETE ON audit_log … RAISE(ABORT, 'append-only')`, and `BEFORE UPDATE` that aborts unless the only change is `actor_id` → `NULL`. That covers raw SQL and `dbshell` too.

---

### ISS-003: Failed sign-ins store the typed username verbatim (may be a mistyped password) 🟢 Low (design question)

**Category**: Privacy
**File**: `src/infrastructure/persistence/audit/receivers.py` (`on_login_failed`); Story 1.8 AC 2 / table row "Unknown username"

**Issue**: Recording the attempted username is explicitly required ("even if no such account exists"). A common mistake, especially for children, is typing the password into the username field. That password is then kept in plain text, forever, in an append-only table (probe: `Ana2018!secret`).

**Suggested Fix** (needs a product/architecture decision, so not a code change by DEV alone):
- Store the typed username only when it **matches an existing account**. Otherwise store `"(unknown)"` plus a short non-reversible fingerprint (e.g. the first 8 hex chars of an HMAC with `SECRET_KEY`), so repeated attempts can still be correlated.
- Record the decision in the architecture's Security Design and amend Story 1.8 AC 2.

---

### ISS-004: Audit rows grow without bound under repeated failed or locked-out attempts 🟢 Low

**Category**: Operations / Availability
**File**: receivers (`auth.login_failed`, `auth.lockout` per attempt)

**Issue**: Each failed attempt, and each attempt during a cool-off, writes a row. That's correct for an audit trail, but an attacker can generate rows at request rate. Story 1.8 puts retention and log shipping out of scope (DevOps), and Story 1.2's review already defers a login rate limit (1.2 ISS-005).

**Suggested Fix**: Track it together with 1.2 ISS-005 in `aire-devops-discover`: a reverse-proxy rate limit on `POST /*/accounts/login/`, plus a retention/archiving policy for `audit_log`. No code change in this story.

---

## Issue Summary

| # | ID | Severity | Category | File | Status |
|---|-----|----------|----------|------|--------|
| 1 | ISS-001 | 🟡 Medium | Security / Privacy | `audit/repositories.py:8-11,37-38` | Should Fix |
| 2 | ISS-002 | 🟢 Low | Security (defence in depth) | `audit/models.py` | Optional |
| 3 | ISS-003 | 🟢 Low | Privacy (design) | `audit/receivers.py` | Needs product decision |
| 4 | ISS-004 | 🟢 Low | Operations | receivers | Defer to DevOps |

**Summary**:
- Blockers: 0
- High: 0
- Medium: 1
- Low: 3

---

## What Was Done Well

1. ✅ Clear ports (`AuditPort`, `UnitOfWork`) and shared fakes, so every later use case can audit and be unit-tested without a DB.
2. ✅ The best-effort decision is explicit and alertable: the auth flow continues, an ERROR line is logged without exception text, and non-DB errors still propagate.
3. ✅ Append-only via the public ORM is airtight across `update`, `delete`, `bulk_update` and `update_or_create`.
4. ✅ Testing through the real Story 1.2 views caught real behaviour (cool-off lockout rows; lockout/failure ordering).
5. ✅ The `_base_manager` subtlety is documented and pinned by a test.

---

## Approval Status

**Decision**: ⚠️ APPROVED WITH COMMENTS

**Reason**: No blockers or high issues. ISS-001 should be fixed before later stories start writing audit metadata (1.9 account changes, CYCLE-3 submissions and moderation). ISS-002 is optional hardening; ISS-003 needs a product decision; ISS-004 belongs to DevOps.

**Next Steps**:
1. `aire-dev-remediate` for ISS-001 (and optionally ISS-002)
2. Product/architecture decision on ISS-003
3. Record ISS-004 with 1.2 ISS-005 for `aire-devops-discover`

---

## Sign-Off

**Reviewer**: REVIEWER Agent
**Date**: 2026-10-22
**Signature**: Approved with comments
