# Code Review - Story 1.8: Audit Log

> ## 🛠️ Remediation Status: 🟡 Partially Remediated (3/4)
> - **Remediated**: 2026-10-22 by DEV Agent
> - **Fixed**: 3 issue(s) — 🔴 0 / 🟠 0 / 🟡 1 / 🟢 2
> - **Deferred (with user consent)**: 1 (ISS-004 → `aire-devops-discover`) — see Remediation Section
> - **Tests**: 717/717 passing | **Coverage**: 100% | **Linter**: clean
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


**Resolution** (2026-10-22, DEV):
- Fix: `is_sensitive_metadata_key()` case-folds the key, treats `-` as `_`, and rejects any key **containing** `password`, `passwd`, `secret`, `token`, `birth`, `dob`, `answer` or `response`
- Commit / change ref: `src/infrastructure/persistence/audit/repositories.py` (`FORBIDDEN_METADATA_FRAGMENTS`, `is_sensitive_metadata_key`, `record`)
- Test evidence: `test_audit_log.py::test_forbidden_metadata_is_rejected` (19 keys: the original 7 plus 12 variants such as `Password`, `new_password`, `user_dob`, `Date-Of-Birth`, `answer_text`, `refresh_token`, `client_secret`; the 12 failed before the fix) and `test_ordinary_metadata_keys_are_allowed` (6 keys, guards against over-blocking)
- Status: ✅ Resolved

---

### ISS-002: `_base_manager` can update audit rows; no guard against application use 🟢 Low

**Category**: Security (defence in depth)
**File**: `src/infrastructure/persistence/audit/models.py` (comment above `actor`)

**Issue**: Django's deletion collector needs `_base_manager` to set `actor_id = NULL` when an account is deleted, so it isn't (and can't be) blocked in Python. The model comment explains this, but nothing stops application code from using `AuditLogModel._base_manager.filter(...).update(...)` (probe: `row action now: tampered`). The architecture only requires append-only "from the application", so this meets the spec, but it relies on convention.

**Suggested Fix** (either or both):
- A negative-space test that fails if `_base_manager` or `.raw(` is referenced on `AuditLogModel` anywhere in `src/` outside `models.py`.
- DB-level enforcement with a reversible `RunSQL` migration adding SQLite triggers: `BEFORE DELETE ON audit_log … RAISE(ABORT, 'append-only')`, and `BEFORE UPDATE` that aborts unless the only change is `actor_id` → `NULL`. That covers raw SQL and `dbshell` too.


**Resolution** (2026-10-22, DEV):
- Fix: reversible migration `audit 0002_append_only_triggers`, with SQLite triggers `audit_log_append_only_delete` (aborts every DELETE) and `audit_log_append_only_update` (aborts every UPDATE unless the only change is `actor_id` → NULL, i.e. account deletion)
- Commit / change ref: `src/infrastructure/persistence/audit/migrations/0002_append_only_triggers.py`
- Test evidence: `tests/integration/persistence/audit/test_append_only_db.py` (9: raw SQL UPDATE/DELETE, `_base_manager` update, 3 "smuggling" cases alongside the unlink, unlink-only allowed, account deletion still works, migration reversible); real `sqlite3` CLI: `Error: stepping, audit_log is append-only (19)` for both UPDATE and DELETE. `test_unit_of_work.py` now runs in the per-test transaction (savepoint), because `transaction=True` teardown DELETEs the table, which the triggers forbid
- Status: ✅ Resolved

---

### ISS-003: Failed sign-ins store the typed username verbatim (may be a mistyped password) 🟢 Low (design question)

**Category**: Privacy
**File**: `src/infrastructure/persistence/audit/receivers.py` (`on_login_failed`); Story 1.8 AC 2 / table row "Unknown username"

**Issue**: Recording the attempted username is explicitly required ("even if no such account exists"). A common mistake, especially for children, is typing the password into the username field. That password is then kept in plain text, forever, in an append-only table (probe: `Ana2018!secret`).

**Suggested Fix** (needs a product/architecture decision, so not a code change by DEV alone):
- Store the typed username only when it **matches an existing account**. Otherwise store `"(unknown)"` plus a short non-reversible fingerprint (e.g. the first 8 hex chars of an HMAC with `SECRET_KEY`), so repeated attempts can still be correlated.
- Record the decision in the architecture's Security Design and amend Story 1.8 AC 2.


**Resolution** (2026-10-22, DEV; product decision by the owner: "Only real accounts"):
- Fix: `RecordSecurityEvent` takes `UsernameDirectory` + `Fingerprint` ports. For events without a `user_id`, the typed username is kept only if `directory.exists()`; otherwise `(unknown):<8-hex HMAC-SHA256(SECRET_KEY)>`. Empty input → `(empty)`. Signed-in events never look anything up. Adapters: `DjangoUsernameDirectory`, `username_fingerprint`; wired in `container.record_security_event()`
- Commit / change ref: `src/application/accounts/record_security_event.py` (`_actor_username`), `src/infrastructure/persistence/accounts/repositories.py`, `src/infrastructure/persistence/audit/fingerprint.py`, `src/infrastructure/container.py`; Story 1.8 spec + architecture Security Design updated
- Test evidence: unit `test_record_security_event.py` (16, incl. unknown → fingerprint only, real account kept, signed-in never looked up, same text → same fingerprint); `test_username_fingerprint.py` (4: hex/deterministic, input-sensitive, keyed by `SECRET_KEY`, doesn't contain input); integration `test_audit_log.py` + `test_audit_login_flow.py` (unknown `ghost` stored nowhere); real server `(unknown):74b10eda` ×2 and `0` rows containing the typed secret
- Status: ✅ Resolved

---

### ISS-004: Audit rows grow without bound under repeated failed or locked-out attempts 🟢 Low

**Category**: Operations / Availability
**File**: receivers (`auth.login_failed`, `auth.lockout` per attempt)

**Issue**: Each failed attempt, and each attempt during a cool-off, writes a row. That's correct for an audit trail, but an attacker can generate rows at request rate. Story 1.8 puts retention and log shipping out of scope (DevOps), and Story 1.2's review already defers a login rate limit (1.2 ISS-005).

**Suggested Fix**: Track it together with 1.2 ISS-005 in `aire-devops-discover`: a reverse-proxy rate limit on `POST /*/accounts/login/`, plus a retention/archiving policy for `audit_log`. No code change in this story.


**Deferral** (2026-10-22, DEV): deferred with user consent to `aire-devops-discover`, together with Story 1.2 ISS-005 (login rate limit) and an `audit_log` retention policy. A retention job will need to drop and re-create the 0002 triggers explicitly. Still open.

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

---

# 🛠️ Remediation — 2026-10-22

**Developer**: DEV Agent
**Severity Scope**: 🟡 ISS-001 + 🟢 ISS-002 (user: "add triggers") + 🟢 ISS-003 (user product decision: "only real accounts"); ISS-004 deferred
**Scenario**: Code Review
**Stories Affected**: 1.8
**Branch**: `main` (the only branch)

## Issues Remediated

| ID | Severity | Story | File | Summary | Resolution | Test Added |
|------|----------|-------|------|---------|------------|------------|
| ISS-001 | 🟡 Medium | 1.8 | `audit/repositories.py` | Literal metadata guard | Fragment match on case-folded keys | 19 rejected + 6 allowed ✅ |
| ISS-002 | 🟢 Low | 1.8 | `audit/migrations/0002_append_only_triggers.py` | `_base_manager`/raw SQL bypass | SQLite triggers; unlink-only UPDATE allowed | 9 ✅ + CLI check |
| ISS-003 | 🟢 Low | 1.8 | `record_security_event.py`, `fingerprint.py`, `accounts/repositories.py`, `container.py` | Verbatim failed usernames | Real accounts only; else keyed fingerprint | 16 unit + 4 fingerprint + integration ✅ |

## Issues Deferred (with user consent)

| ID | Severity | Story | Reason |
|----|----------|-------|--------|
| ISS-004 | 🟢 Low | 1.8 | Audit growth under attack: proxy rate limit + retention policy (DevOps) |

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `src/infrastructure/persistence/audit/repositories.py` | Modified | Fragment-based sensitive-key guard |
| `src/infrastructure/persistence/audit/migrations/0002_append_only_triggers.py` | New | DB-level append-only |
| `src/application/accounts/record_security_event.py` | Modified | `UsernameDirectory`, `Fingerprint`, `_actor_username` |
| `src/infrastructure/persistence/audit/fingerprint.py` | New | HMAC-SHA256 fingerprint |
| `src/infrastructure/persistence/accounts/repositories.py` | Modified | `DjangoUsernameDirectory` |
| `src/infrastructure/container.py` | Modified | Wiring |
| `tests/integration/persistence/audit/test_append_only_db.py` | New | 9 tests |
| `tests/unit/infrastructure/test_username_fingerprint.py` | New | 4 tests |
| `tests/unit/application/accounts/test_record_security_event.py` | Modified | 16 tests (new ports) |
| `tests/integration/persistence/audit/test_audit_log.py`, `test_audit_login_flow.py`, `test_unit_of_work.py` | Modified | New expectations; savepoint-based UoW test |
| `docs/plans/stories/epic-1-story-1.8-Audit-Log.md`, `docs/architecture/design/00-system-architecture-greenfield.md` | Modified | Owner decision recorded |

## Patterns Applied

| Pattern | Where Applied | Notes |
|---------|---------------|-------|
| Ports & adapters §5/§15 | `UsernameDirectory`, `Fingerprint` | The policy stays in the application; data lookups and crypto in infrastructure |
| Logging §9 never-log list | metadata guard, username masking | Passwords never reach the append-only table |
| Migrations §6.4 | 0002 | Reversible (`reverse_sql`), proven by test |

## Testing Summary

- **Targeted tests added/changed**: 12 metadata variants + 6 allowed keys; 9 DB-level; 16 use case; 4 fingerprint; integration expectations
- **Full suite**: 717/717 passing (3 runs)
- **Coverage**: 100% (target ≥85%); `src/application` 100%; `src/domain` 100%
- **Gates**: ruff format/check clean · mypy 0 issues (94 files) · import-linter 2/2 kept · `makemigrations --check` no changes

**Test Output** (verbatim, filtered):
```
collected 717 items
tests/integration/persistence/audit/test_append_only_db.py .........     [  2%]
tests/integration/persistence/audit/test_audit_log.py .................. [  4%]
tests/integration/persistence/audit/test_audit_login_flow.py ......      [  8%]
tests/integration/persistence/audit/test_unit_of_work.py ..              [  9%]
tests/unit/application/accounts/test_record_security_event.py .......... [ 85%]
tests/unit/infrastructure/test_username_fingerprint.py ....              [100%]
src/application/accounts/record_security_event.py            38      0      6      0   100%
src/infrastructure/persistence/audit/fingerprint.py           7      0      0      0   100%
src/infrastructure/persistence/audit/repositories.py         16      0      2      0   100%
TOTAL                                                       665      0     74      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
============================= 717 passed in 7.37s ==============================
```

**Real server + sqlite3 CLI**:
```
wrong password for ana -> 200 · password typed as username -> 200 · same text again -> 200 · ana correct -> 302
auth.login_failed            ana
auth.login_failed            (unknown):74b10eda
auth.login_failed            (unknown):74b10eda
auth.login         1         ana
== secret text stored anywhere?  0
== sqlite3 CLI tampering
Error: stepping, audit_log is append-only (19)      (UPDATE)
Error: stepping, audit_log is append-only (19)      (DELETE)
4 rows still present
== account deletion still works → auth.login_failed|NULL|ana · auth.login|NULL|ana
```

## Deviations from Report Suggestions

- ISS-002: both suggestions were considered; the DB triggers alone cover raw SQL, `_base_manager` and dbshell, so the extra grep test wasn't needed.
- ISS-003: also applied to `auth.lockout`. Axes passes the same typed username, so the same leak existed there.

## Lessons Learned

1. "Append-only in Python" is a convention; triggers make it a guarantee. Account deletion's `SET NULL` must be explicitly allowed.
2. Defence-in-depth guards should match on meaning (fragments, case-folded), not on exact strings.

## Next Steps

- [ ] Re-request code review (`aire-review-code`): optional (no 🔴 fixed)
- [ ] ISS-004 in `aire-devops-discover`
