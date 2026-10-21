# Story 1.8 Self-Review

**Date**: 2026-10-21
**Story**: Audit Log (CYCLE-1, wave 2, Dev 2)
**Developer**: DEV Agent
**Branch**: `feature/story-1.8-audit-log` (from `feature/wave-2-dev-1` @ `7b9fac5`: Stories 1.0–1.3, 1.5, 2.1 merged)

---

## What Was Implemented

- Application ports `UnitOfWork` and `AuditPort` (`application/common/`), which every later auditing story depends on
- `RecordSecurityEvent` use case + `SecurityEvent` (`auth.login`, `auth.logout`, `auth.login_failed`, `auth.lockout`) + `SecurityEventCommand`
- `audit` persistence app:
  - `AuditLogModel` (append-only; actor kept as username after account deletion)
  - `DjangoAuditPort(clock)` (rejects sensitive metadata keys)
  - signal receivers for Django auth + axes lockout (best-effort: `DatabaseError` → `ERROR audit.write_failed`)
  - migration `0001`
- `DjangoUnitOfWork` (patterns §6.3) and the first real composition-root entry `record_security_event()`
- Shared test fakes `FakeAuditPort`, `FakeUnitOfWork`, `FixedClock` (`from tests.fakes import …`)

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `src/application/common/__init__.py`, `audit.py`, `unit_of_work.py` | New | `AuditPort`, `UnitOfWork` Protocols |
| `src/application/accounts/record_security_event.py` | New | Use case, event enum, command |
| `src/infrastructure/persistence/common/__init__.py`, `unit_of_work.py` | New | `DjangoUnitOfWork` |
| `src/infrastructure/persistence/audit/__init__.py`, `apps.py`, `models.py`, `repositories.py`, `receivers.py`, `migrations/0001_initial.py` | New | Audit app |
| `src/infrastructure/container.py` | Modified (shared) | First entry: `record_security_event()` |
| `src/config/settings/base.py` | Modified (shared) | One `INSTALLED_APPS` line |
| `tests/fakes/__init__.py`, `audit.py`, `uow.py`, `clock.py` | New | Shared fakes |
| `tests/unit/application/accounts/test_record_security_event.py` | New | 9 tests |
| `tests/integration/persistence/audit/test_audit_log.py` | New | 20 tests (signals, append-only, deletion, metadata, failure path, clock) |
| `tests/integration/persistence/audit/test_audit_login_flow.py` | New | 6 tests through Story 1.2's real login/logout/lockout views |
| `tests/integration/persistence/audit/test_unit_of_work.py` | New | 2 tests (commit; rollback + re-raise) |
| `docs/status.md` | Modified | Story Tracker |

## Patterns Applied

| Pattern | Where Applied | Notes |
|---------|---------------|-------|
| Application use case §5 | `RecordSecurityEvent` | Ports injected; one `execute`; writes inside the UoW |
| Repository & Unit of Work §6.3 | `DjangoUnitOfWork`, `DjangoAuditPort` | UoW never suppresses exceptions |
| Adapter §15 | `DjangoAuditPort` implements `AuditPort` | |
| Logs vs audit §9 | receivers | Audit = business record; log line on failure contains only the event name |
| Fakes & FixedClock §12.2 | `tests/fakes/` | Hand-written, no `unittest.mock` |
| Composition root §5 | `container.record_security_event()` | No singletons |

## Testing Summary

- **Unit tests**: 78 (9 new), all passing
- **Integration tests**: 514 (28 new), all passing
- **Full suite**: 592 passed (3 consecutive runs)
- **Coverage**: 100.00% overall; `src/application` 100%; `src/domain` 100%

**Test output** (verbatim, filtered to the new test files and the totals):
```
$ uv run pytest --cov=src --cov-branch --cov-fail-under=85
tests/integration/persistence/audit/test_audit_log.py .................. [  4%]
tests/integration/persistence/audit/test_audit_login_flow.py ......      [  5%]
tests/integration/persistence/audit/test_unit_of_work.py ..              [ 50%]
tests/unit/application/accounts/test_record_security_event.py .........  [ 88%]
TOTAL                                                     538      0     54      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
============================= 592 passed in 5.68s ==============================
```
(`test_audit_log.py` has 20 tests; the progress line wraps after 18 dots. `pytest --collect-only` counts: 20 / 6 / 2 / 9.)

## DoD Evidence

### Quality gates (2026-10-21)

```
$ uv run ruff format --check .
112 files already formatted
$ uv run ruff check .
All checks passed!
$ uv run mypy
Success: no issues found in 86 source files
$ PYTHONPATH=src uv run lint-imports
Contracts: 2 kept, 0 broken.
$ uv run python manage.py makemigrations --check --dry-run
No changes detected
$ uv run pytest --cov=src --cov-branch --cov-fail-under=85
592 passed — Total coverage: 100.00%
$ uv run coverage report --include="src/application/*" --fail-under=100
TOTAL                                                  30      0      0      0   100%
exit=0
```

### Manual check (real `runserver`, real CSRF tokens, fresh DB)

```
ana login: 302
ana logout: 302
ghost wrong: 200
bob x5 wrong: 200 200 200 200 429
== SELECT action, actor_id, actor_username, ip_address, created_at, metadata FROM audit_log ORDER BY id
auth.login         1         ana             127.0.0.1   2026-10-21 13:27:57.881803  {}
auth.logout        1         ana             127.0.0.1   2026-10-21 13:27:57.900512  {}
auth.login_failed            ghost           127.0.0.1   2026-10-21 13:27:57.937065  {}
auth.login_failed            bob             127.0.0.1   2026-10-21 13:27:57.968992  {}
auth.login_failed            bob             127.0.0.1   2026-10-21 13:27:58.001258  {}
auth.login_failed            bob             127.0.0.1   2026-10-21 13:27:58.033143  {}
auth.login_failed            bob             127.0.0.1   2026-10-21 13:27:58.070301  {}
auth.lockout                 bob             127.0.0.1   2026-10-21 13:27:58.102307  {}
auth.login_failed            bob             127.0.0.1   2026-10-21 13:27:58.102532  {}
== delete ana's account, then her rows
auth.login|NULL|ana
auth.logout|NULL|ana
== app tries to edit/delete a row
blocked: audit_log is append-only
blocked: audit_log is append-only
blocked: audit_log is append-only
rows still: 9
```
`created_at` is stored in UTC (13:27 UTC = 16:27 Europe/Bucharest). In the original console label for the deletion step, "bob" was a typo. The command deleted `ana`, as the output shows.

### JSON `audit.write_failed` line

Asserted by `test_audit_failure_does_not_break_login_signal`: the captured stdout line parses as JSON with `level == "ERROR"`, `event == "audit.write_failed"`, `audit_action == "auth.login"`, and does **not** contain the exception text (`database is locked`).

### Gate 1 — Spec Echo

| # | Requirement | Proof |
|---|-------------|-------|
| AC1 | `UnitOfWork` Protocol (`__enter__`/`__exit__`); `AuditPort.record` signature with `target: tuple[str,str] \| None`, `metadata: Mapping[str, str\|int\|bool] \| None` | `src/application/common/unit_of_work.py`, `src/application/common/audit.py`; mypy strict on `application.*` passes |
| AC2 | One `record(event.value, actor_id, actor_username, ip_address)` inside the UoW; empty username → `"(empty)"` (LOGIN_FAILED, LOCKOUT); truncate to 150 | `record_security_event.py`; `test_each_event_records_one_entry_in_a_unit_of_work[*]` (4), `test_empty_username_is_recorded_explicitly[*]` (2), `test_long_username_is_truncated`, `test_audit_failure_rolls_back_the_unit_of_work_and_propagates` |
| AC3 | `AuditLogModel` fields, `db_table="audit_log"`, ordering `-created_at`, two indexes | `audit/models.py`; migration `0001_initial.py`; manual `SELECT` columns |
| AC4 | `save()` on existing row, `delete()`, queryset `update()`/`delete()` raise; user deletion still works (`SET_NULL`) | `test_rows_are_append_only` (4 raises + value unchanged), `test_deleting_user_keeps_rows_with_username`; manual "blocked ×3", "NULL|ana" |
| AC5 | `created_at = clock.now()` (aware UTC); forbidden metadata keys → `ValueError` | `test_created_at_comes_from_injected_clock`, `test_forbidden_metadata_is_rejected[*]` (all 7 keys), `test_target_and_metadata_are_stored` |
| AC6 | Receivers for login/logout/login_failed/lockout with `dispatch_uid`; logout skipped when `user is None`; IP via `axes.helpers.get_client_ip_address` or None | `receivers.py`; `test_login_and_logout_signals_write_rows` (IP `127.0.0.1`), `test_logout_without_user_writes_no_row`, `test_failed_login_records_attempted_username_never_password` (IP `10.1.2.3`), `test_failed_login_without_request_or_username_is_still_recorded` (IP None), `test_lockout_signal_records_lockout`, `test_each_signal_is_connected_exactly_once` |
| AC7 | `DatabaseError` → `ERROR audit.write_failed {"audit_action": …}`, not raised; other exceptions propagate | `test_audit_failure_does_not_break_login_signal`, `test_non_database_errors_propagate` |
| AC8 | `DjangoUnitOfWork` per §6.3; container `record_security_event()`; rewire `update_preferred_language()` | `persistence/common/unit_of_work.py`, `test_unit_of_work_commits_on_clean_exit`, `test_unit_of_work_rolls_back_and_reraises_on_error`; `container.py`. **Rewire: not applicable yet**, see Deviations |
| AC9 | `INSTALLED_APPS` gains the audit app; `makemigrations --check` clean | `base.py` line after catalogue; gate output |
| AC10 | `tests/fakes` exports `FakeUnitOfWork`, `FakeAuditPort`, `FixedClock` | `tests/fakes/__init__.py`; imported by the unit + integration tests |
| AC11 | `application/common` and `record_security_event.py` 100%; overall ≥85% | `coverage report --include="src/application/*" --fail-under=100` → 100%; overall 100% |
| Step 1 | Fakes + unit tests first | unit test collection error before `record_security_event.py` existed |
| Steps 2–6 | ports/use case, model/port, receivers/apps, container, settings + migration | files above |
| Step 7 | All gates | gate output above |
| Ref: architecture `AUDIT_LOG` entity | id, actor_id (nullable, SET_NULL), actor_username, action, target_type, target_id, metadata, ip_address, created_at | `models.py` matches 1:1 |
| Ref: architecture Security Design — audit logins, failures, lockouts; append-only, no edit UI | receivers + append-only guards; no route added |
| Ref: architecture "Account deletion … `AUDIT_LOG.actor_username` is kept" | `test_deleting_user_keeps_rows_with_username`; manual |
| Ref: patterns §9 never-log list (passwords, DOB, answers, tokens) | receivers read only `username`; metadata guard; failure log has no exception text |
| Ref: patterns §5 "DON'T call `timezone.now()` in application code; inject Clock" | clock injected into `DjangoAuditPort`; application has no time calls |
| QA-observable: 5 wrong passwords → 5 `login_failed` + 1 `lockout` | `test_fifth_failure_records_five_failures_and_one_lockout`; manual (bob) |
| QA-observable: HTTP responses unchanged | `test_login_response_is_unchanged_by_auditing`; all of Story 1.2's 102 tests still pass |

AC rows: 11 of 11. AC 8 is fully proven except the `update_preferred_language` rewire, which has no target yet (Story 1.4 is unbuilt). This is documented as a hand-off below, not dropped.

### Gate 2 — Negative-Space Check

| Rule | Check | Result |
|------|-------|--------|
| Application imports no Django/axes | import-linter; `grep -rnE "^(import\|from) (django\|axes)" src/application` | KEPT; none |
| Never read/store password or DOB | `grep -rn "password\|date_of_birth" receivers.py record_security_event.py` → none; metadata guard tests | ✓ |
| No audit row updated/deleted by the app | 4 append-only assertions + manual "blocked ×3, rows still: 9" | ✓ |
| No route reads the log (Story 1.9) | `git diff --stat` shows no `urls.py`/views change; URL-coverage test unchanged and green | ✓ |
| Failure log has no PII / exception text | `"database is locked" not in json.dumps(failure)` | ✓ |
| No TODO/FIXME | grep | none |

### Gate 3 — Contract Consistency

| Producer | Consumer | Consistent? |
|----------|----------|-------------|
| `AuditPort.record` signature | `DjangoAuditPort.record`, `FakeAuditPort.record`, patterns §5 `SubmitTest` example | ✓ same keyword-only parameters |
| `UnitOfWork` Protocol | `DjangoUnitOfWork`, `FakeUnitOfWork`; Story 1.4's `AbstractContextManager` expectation | ✓ (mypy) |
| `SecurityEvent` values | `audit_log.action` rows (manual SELECT) | ✓ |
| axes `user_locked_out(request, username, ip_address)` (axes 8.3.1 `handlers/database.py`) | `on_lockout(sender, request, username, **kwargs)` | ✓ |
| Django `user_login_failed(credentials, request=None)` | `on_login_failed` handles missing request/username | ✓ tested |
| `MAX_USERNAME = 150` | `AuditLogModel.actor_username max_length=150`, `UserModel.username` | ✓ |

## Challenges Encountered

| Challenge | Resolution | Time Spent |
|-----------|------------|------------|
| Lockout row precedes the 5th failure row | axes' own `user_login_failed` receiver fires `user_locked_out` before ours. The story asks for counts, not order, so the test asserts counts and the order is documented | 5 min |
| `Atomic.__exit__` is typed `-> None` | `DjangoUnitOfWork.__exit__ -> None`; still satisfies the `UnitOfWork` Protocol | 5 min |
| RUF012 on `Meta` lists | tuples; the unmerged migration was regenerated, not edited by hand | 5 min |

## Deviations from Plan

- **AC 8, `update_preferred_language()` rewire, deferred to Story 1.4.** The story assumed 1.4 would land first. It hasn't been built, so the container entry doesn't exist. Story 1.4's own note (line 104) says its use case accepts either `transaction.atomic` or `DjangoUnitOfWork`. **Hand-off:** when 1.4 is implemented, wire `UpdatePreferredLanguage(DjangoUserPreferences(), DjangoUnitOfWork)` directly.
- **Attempts during the lockout cool-off** (even with the correct password) are recorded as `auth.lockout` rows. That's because Story 1.2 sets `AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = False`, and axes then sends `user_locked_out` on each blocked attempt. Each blocked attempt is a real security event, so one row per attempt matches the "each event fires once per real occurrence" rule. Pinned by `test_attempts_during_cool_off_are_recorded_as_lockouts`.
- **`DjangoAuditPort` takes a `Clock`**, as the story says. Patterns §5's container example shows `DjangoAuditPort()` without one; the story is newer and more specific.
- **Extra tests** beyond the story's list: real-view flow (6), UoW commit/rollback (2), queryset `update`/`delete`, all 7 forbidden keys, missing request/username, double-connection guard, non-DB exceptions propagate, `__str__`, and the use case rolling back the UoW.
- **Index names** are explicit (`audit_action_created_idx`, `audit_actor_created_idx`) so migrations don't depend on auto-generated names.

## Lessons Learned

1. When two receivers listen to the same signal, their order is framework-defined. Test the counts the spec asks for, not an incidental order.
2. Testing through the real view, not only by sending signals directly, caught the cool-off behaviour that direct signal tests would never show.

## Next Steps

- [ ] Ready for code review (`aire-review-code`)
- [ ] Story 1.4 must wire `DjangoUnitOfWork` into `update_preferred_language()` (hand-off above)
- [ ] Story 1.9 adds the read-only Admin view of `audit_log`
