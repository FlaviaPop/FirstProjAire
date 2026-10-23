# Code Review - Story 1.8: Audit Log

**Date**: 2026-10-23
**Reviewed By**: REVIEWER Agent
**Review Number**: 2
**Review Mode**: NEW_CHANGES
**Status**: ✅ APPROVED

---

## Review Metadata

**Previous Review**: `docs/reviews/story-1.8-code-review-v1.md`
**Previous Status**: ⚠️ APPROVED WITH COMMENTS; remediated, now ✅ Resolved (ISS-004 fixed 2026-10-23)
**Files Changed Since Last Review**: new `src/infrastructure/persistence/audit/retention.py` and `management/commands/purge_audit_log.py`; `src/infrastructure/container.py`, `src/config/settings/base.py`, and tests (combined remediation commit `47d8d2d`)
**Severity Threshold Applied**: 🔴 Blocker + 🟠 High only, in the changed files. I also verified the previous issue.

---

## Review Summary

**Components Reviewed**: `AuditRetention.purge()` and `PurgeResult`; the `purge_audit_log` command (`--dry-run`); `container.audit_retention()`; `AUDIT_RETENTION_DAYS = 365`; `test_audit_retention.py` (11 tests).
**Tests Reviewed**: Yes
**Coverage**: 100% for `src/`

**Overall Assessment**: A narrow, well-reasoned exception to the append-only guarantee:
  - only the DELETE trigger is lifted, for one statement, inside the transaction that restores it;
  - the purge is itself audited;
  - the trigger SQL is reused from the migration;
  - the command is thin and built by the container.

The unit tests run inside a pytest savepoint, so I re-checked the risky behaviour on a real database with real transactions: rollback, the cutoff boundary and a concurrent writer.

---

## Previous Issue Verification

| ID | Severity | Fix verified | Evidence |
|----|----------|--------------|----------|
| ISS-004 | 🟢 Low | ✅ Resolved | real-DB probes P1–P3 (below); 73 audit tests + full suite |

### Independent verification (REVIEWER, 2026-10-23)

```
Fresh migrated file DB (config.settings.dev), cutoff with 0 microseconds (exact second):
P1 induced audit failure  -> raised 'induced'; rows unchanged ['kept.equal','kept.half','old.1s','old.1us'];
                             both triggers present; no transaction left open
P2 boundary               -> deleted 2 (cutoff-1us, cutoff-1s); kept: equal-to-cutoff, cutoff+0.5s; purge audited
P3 concurrent writer      -> second connection INSERT waited 1.29s for the purge's lock, then committed;
                             its DELETE afterwards: 'audit_log is append-only'; both triggers present
```

```
[full suite + cov] 1532 passed, 17 deselected in 14.19s | Total coverage: 100.00%
[ruff format]      193 files already formatted
[ruff check]       All checks passed!
[mypy]             Success: no issues found in 119 source files   (--no-incremental)
[lint-imports]     Contracts: 2 kept, 0 broken.
[makemigrations]   No changes detected
```

---

## Checklist Results (changed files)

- [x] ✅ **Correctness:**
  - `created_at < cutoff` matches the dry-run's ORM `__lt`, since both use Django's own datetime adaptation;
  - `rowcount` is the deleted count;
  - DROP has no `IF EXISTS`, so the purge refuses to run on an unexpected schema.
- [x] ✅ **Transactions (ADR-004):** IMMEDIATE takes the write lock at BEGIN, so concurrent writers wait (timeout 20 s) instead of interleaving. SQLite DDL rolls back with the data.
- [x] ✅ **Architecture:**
  - the service depends on `AuditPort` and `Clock`;
  - the container picks the implementations;
  - the command is a thin entry point;
  - import contracts are kept.
- [x] ✅ **Testing:**
  - cutoff boundary;
  - purge audited, including a heartbeat purge that deletes nothing;
  - dry run;
  - triggers back and still blocking DELETE and UPDATE;
  - rollback;
  - input validation;
  - container;
  - command output.
- [x] ✅ **Security:** the ORM guards and the UPDATE trigger are untouched. The `(system)` actor can't collide with a real username.

---

## Issues Found

None at 🔴 or 🟠 in the changed files.

## Issue Summary

| # | ID | Severity | Category | File | Status |
|---|-----|----------|----------|------|--------|
| — | — | — | — | — | — |

**Summary**:
- Blockers: 0
- High: 0
- Medium / Low: not assessed (NEW_CHANGES threshold)

---

## What Was Done Well

1. ✅ The guard is lifted for exactly one statement, inside the transaction that restores it.
2. ✅ Every purge leaves its own audit row, so retention is visible in the very log it trims.
3. ✅ The SQL is reused from the migration, so it can't drift from it.

---

## Approval Status

**Decision**: ✅ APPROVED

**Reason**: No blockers or high issues. The previously deferred item is fixed and independently verified.

---

## Sign-Off

**Reviewer**: REVIEWER Agent
**Date**: 2026-10-23
**Signature**: Approved
