# Bug Triage Report

> ## 🛠️ Remediation Status: ✅ Resolved
> - **Remediated**: 2026-10-21 by DEV Agent (with `bug-triage-2026-10-21-2.md`)
> - **Fixed**: 1 bug — P3:1 · **Deferred**: 0
> - **Tests**: 605/605 passing | **Coverage**: 100% | **Linter**: clean
> - **Scenario**: QA Triage

**Date**: 2026-10-21
**Triaged By**: QA Agent
**Source Report(s)**: `docs/testing/validation-report-story-1.0-2026-10-21.md` (story 1.0, commit `26b4ece`)
**BUILDID**: CYCLE-1

---

## Summary

**Total Bugs**: 1
**Critical**: 0 🔴
**High**: 0 🟠
**Medium**: 0 🟡
**Low**: 1 🟢

**Release Blockers**: 0

---

## Release Blocking Bugs

| ID | Severity | Summary | Impact | Recommendation |
|----|----------|---------|--------|----------------|
| — | — | None | — | — |

---

## Priority Classification

### P0 - Must Fix Now (Release Blockers)
- None

### P1 - Should Fix Before Release
- None

### P2 - Can Fix After Release
- None

### P3 - Nice to Have
- BUG-001: `/healthz` logs a database fault when the real cause is a read-only data directory

---

## Bug Details

### BUG-001: `/healthz` logs the wrong cause for a read-only data directory 🟢
**Severity**: Low
**Priority**: P3
**Category**: Functional (operational logging / diagnosability)
**Story**: 1.0 Root Tooling Seed · `src/infrastructure/web/common/health.py:14-25`
**Affected Features**: `/healthz` failure diagnostics (server log only). The HTTP contract (`503 {"status": "unavailable", "db": "error"}`) is correct.
**Affected Users**: Operators / DevOps reading logs during an incident. No impact on students, teachers, parents or admins: no UI and no data effect.
**Workaround**: When `/healthz` returns 503 with `healthz.db_unavailable`, also check write permissions on the `DATABASE_PATH` directory (`ls -ld data/`). Add this to the Story 1.1 / DevOps runbook until fixed.

**Root cause**: In WAL mode, a new SQLite connection must create the `-wal`/`-shm` files next to the database. If the directory is read-only, `SELECT 1` already raises `OperationalError`, so `_database_ok()` returns through the `DatabaseError` branch (`healthz.db_unavailable`). The `os.access(db_dir, os.W_OK)` branch (`healthz.data_dir_not_writable`) is reached only when a connection is already open. The integration test `test_healthz_returns_503_when_data_directory_not_writable` patches `os.access` after a successful query, so it doesn't reproduce the real situation.

**Reproduction**:
1. `rm -rf data && uv run python manage.py migrate`
2. `uv run python manage.py runserver 8766 --noreload`
3. `chmod -w data`
4. `curl -i localhost:8766/healthz` → `503` ✅
5. Server log shows `healthz.db_unavailable` ❌ (expected `healthz.data_dir_not_writable`)
6. `chmod u+w data`

**Evidence**: validation report TC-020 (`server log: healthz.db_unavailable`)

**Dependencies**:
- Related to review item **ISS-005** (dev log level), already deferred to **Story 1.1**, which replaces `LOGGING` with the JSON formatter and adds the request id. Both touch the same logging path and should be fixed together.
- The console handler currently drops the `extra={"error": …}` class name. Story 1.1's JSON formatter makes that field visible, which also helps here.

**Recommendation**: Fix later (non-blocking). Check directory writability **before** opening the cursor, so the cause is reported correctly. Replace the `os.access` patch in the test with a real read-only temp directory (skip when running as root). Target: Story 1.1 (wave 2, Dev 1), or `aire-dev-remediate` from this report if you want it fixed now.
**Assigned To**: DEV
**Target**: CYCLE-1, with Story 1.1

**Resolution** (2026-10-21, DEV):
- Fix: the health check verifies the data directory before querying (`src/infrastructure/web/common/health.py:14-27`)
- Test evidence: `tests/integration/web/test_healthz.py:70` (real read-only directory); full evidence in `docs/testing/bug-triage-2026-10-21-2.md` → Remediation
- Status: ✅ Resolved

---

## Release Decision

**Recommendation**:
- [x] ✅ APPROVE RELEASE (no blockers). Story 1.0 can merge to `main` for wave 2
- [ ] ❌ BLOCK RELEASE (P0 bugs exist)
- [ ] ⚠️ CONDITIONAL RELEASE (with documented issues)

**Rationale**: The only bug is 🟢 Low / P3. It affects log wording, not the health-check contract, user-facing behaviour or data. A workaround exists, and it has a natural fix point in Story 1.1.

---

## Tracker

`docs/status.md` → **Tracking: Local**, so no GitHub/Azure DevOps push.

### Triage Summary

- **Total bugs**: 1
- **P0 blockers**: None
- **Release**: CYCLE-1

---

## Next Steps
1. Merge `feature/story-1.0-root-tooling-seed` (`26b4ece`) to `main`
2. Carry BUG-001 and ISS-005 into Story 1.1 (or remediate BUG-001 now via `aire-dev-remediate`)
3. Re-check `/healthz` logging in QA Group 1 after Story 1.1, and run `aire-qa-regression` against the 2026-10-21 baseline
