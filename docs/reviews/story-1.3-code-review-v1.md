# Code Review - Story 1.3: RBAC Core

> ## 🛠️ Remediation Status: ✅ Fully Remediated (5/5)
> - **Remediated**: 2026-10-21 by DEV Agent; ISS-004 on 2026-10-22 with Story 1.6
> - **Fixed**: 5 issue(s) — 🔴 0 / 🟠 0 / 🟡 1 / 🟢 4
> - **Deferred**: 0 (ISS-004, deferred to Story 1.6 on 2026-10-21, resolved in Story 1.6 on 2026-10-22)
> - **Tests**: 598/598 passing | **Coverage**: 100% | **Linter**: clean (2026-10-21 full suite)
> - **Tests (2026-10-22, ISS-004)**: `test_url_protection.py` 32/32 + `ui/test_styleguide.py` 16/16 = 48/48 passing (targeted, before integration)
> - **Tests (2026-10-22, Story 1.6 integration, full suite)**: 980/980 passing (3 consecutive runs) | **Coverage**: 100% (lines + branches) | **Linter**: ruff/mypy/lint-imports clean
> - **Scenario**: Code Review

**Date**: 2026-10-21
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
**Code reviewed at**: `feature/wave-2-dev-1` @ `7b9fac5` (Story 1.3 commit `8f2a01a`, merged in `09b8dea` with Story 1.2's `PUBLIC_URL_NAMES` and fixtures)

---

## Review Summary

**Components Reviewed**:
- `src/domain/accounts/roles.py`, `permissions.py`, `access_policy.py`
- `src/infrastructure/web/common/decorators.py`
- `tests/unit/domain/accounts/*` (3 files)
- `tests/integration/web/test_url_protection.py`, `test_role_access_matrix.py`
- `docs/stories-implemented/story-1.3-review.md`

**Lines of Code**: ~210 production, ~350 test
**Tests Reviewed**: Yes (73 tests in the story's files, all passing)
**Coverage**: 100% for `src/domain/accounts/*` and `decorators.py` (statements + branches), re-run by the reviewer

**Overall Assessment**: A tight, faithful implementation of ADR-007. The permission matrix is copied verbatim and locked by a literal test. Identity comes only from the session, and a corrupt role is denied (403) rather than crashing. The URL-coverage walker is itself tested against a synthetic route list. No blockers or high issues. Comments cover making the decorator fail fast on unknown keys, an async-view trap, a DEBUG-only blind spot in the coverage test, and a stale note in the self-review.

### Evidence verification (re-run by reviewer)

```
$ uv run pytest -q tests/unit/domain tests/integration/web/test_url_protection.py tests/integration/web/test_role_access_matrix.py
73 passed in 0.23s
$ uv run ruff check src/domain src/infrastructure/web/common/decorators.py   → All checks passed!
$ uv run mypy                                                              → Success: no issues found in 86 source files
$ PYTHONPATH=src uv run lint-imports                                       → Contracts: 2 kept, 0 broken.
$ uv run pytest -q --cov=src --cov-branch                                  → 592 passed
src/domain/accounts/access_policy.py             14      0      6      0   100%
src/domain/accounts/permissions.py               24      0      0      0   100%
src/domain/accounts/roles.py                     11      0      0      0   100%
src/infrastructure/web/common/decorators.py      32      0      6      0   100%

Probes (reviewer script, config.settings.test):
plain str key accepted by has_permission: True
typo key accepted at decoration: ('content:edt',)
async view stays a coroutine function: False
```

---

## Checklist Results

### Correctness
- [x] ✅ Matrix equals `docs/requirements.md` (literal expected table; 16 keys; read-only)
- [x] ✅ All-keys-required semantics; anonymous → `redirect_to_login(full_path)`; unknown role → 403
- [x] ✅ Record scope: own / linked child / `scores:view-all`; unknown role False (11-case table)
- [x] ✅ Denied requests: no DB writes, no session change, identical repeat (captured SQL)
- [x] ⚠️ Typo'd permission keys are accepted at decoration time and silently deny everyone (ISS-001)
- [x] ⚠️ An `async def` view wrapped by the guard is never awaited (ISS-002, latent)

### Pattern Adherence
- [x] ✅ Domain §4: StrEnums, pure functions, stdlib only (import-linter KEPT)
- [x] ✅ §7.2 decorator, with the documented improvement `parse_role` instead of `Role(...)` (500 → 403)
- [x] ✅ §12.4 mandatory tests present with the prescribed names
- [x] ✅ Naming §1.2; functions well under 30 lines; files small
- [x] ⚠️ `View` type alias in `decorators.py` reads like Django's `django.views.View` (ISS-003)

### Testing
- [x] ✅ Unit tests meaningful; integration covers function and class-based views, elevation attempts and side effects
- [x] ✅ Coverage walker tested on a synthetic list (`["open", "nameless"]`), so "no offenders" can't be vacuous
- [x] ⚠️ URL-coverage test only sees `DEBUG=False` routing; DEBUG-only routes are never checked (ISS-004)
- [x] ✅ Coverage 100% (domain gate 100%)

### Documentation
- [x] ✅ Google-style docstrings on public domain functions; comments explain *why*
- [x] ✅ No TODO/FIXME
- [x] ⚠️ Self-review still describes the fixture stand-ins as present (ISS-005)

### Security
- [x] ✅ Identity only from `request.user`; `?role=`, `?as=`, `X-Role` ignored (tested)
- [x] ✅ Fail-closed everywhere: unknown role, missing key, typo key (see ISS-001: safe, but silent)
- [x] ✅ 403 for role denial vs 404 for out-of-scope records (policy returns bool; query services raise `NotFound`)
- [x] ✅ No Django Groups/Permissions tables (ADR-007)
- [x] ✅ No secrets, no PII in logs

### Performance
- [x] ✅ O(k) frozenset lookups per request; no DB access in the guard beyond the session user Django already loads

### SOLID / Anti-Monolith
- [x] ✅ SRP: roles, permissions, policy and web guard are separate modules
- [x] ✅ OCP: new permissions/roles are data changes in one map; the guard doesn't change
- [x] ✅ DIP: the web layer depends on domain functions; the domain depends on nothing
- [x] ✅ No global mutable state (`MappingProxyType` is read-only)

---

## Issues Found

### ISS-001: Unknown permission keys are accepted at decoration time 🟡 Medium

**Category**: Correctness (fail-fast)
**File**: `src/infrastructure/web/common/decorators.py` (`require_permission`)
**Pattern Reference**: Story 1.3 AC 6 ("fail fast at import" for the no-argument case); patterns §13 (authorisation)

**Issue**:
`require_permission` validates that at least one key is passed, but not that each key is a real `Permission`. `Permission` is a `StrEnum`, so a plain string compares equal to a member. `require_permission("content:edt")` therefore decorates successfully and stores `('content:edt',)`. Every role then fails `has_permission` and the page returns 403 for everyone. That's safe (fail-closed), but it's a functional bug that surfaces only when someone opens the page. mypy catches it for typed callers, but not for `# type: ignore` sites, strings built at runtime, or untyped call sites.

**Current Code**:
```python
if not permissions:
    raise ValueError("require_permission needs at least one Permission")
required = tuple(permissions)
```

**Suggested Fix**:
```python
if not permissions:
    raise ValueError("require_permission needs at least one Permission")
required = tuple(Permission(p) for p in permissions)  # ValueError at import for unknown keys
```
Add a test: `with pytest.raises(ValueError): require_permission("content:edt")`.

**Why This Matters**: The story's own rule is "app fails fast" for a misconfigured guard. A typo should break the app at import like the empty case does, not ship a page nobody can open.


**Resolution** (2026-10-21, DEV):
- Fix: `require_permission` converts every key with `Permission(p)` at decoration, so an unknown key raises `ValueError("'content:edt' is not a valid Permission")` at import; valid plain strings are normalised to `Permission` members
- Commit / change ref: `src/infrastructure/web/common/decorators.py:66` (+ docstring `Raises:`)
- Test evidence: `tests/integration/web/test_url_protection.py:180` `test_decorator_rejects_unknown_permission_keys_at_import[content:edt|CONTENT_EDIT|'']` (3 cases, failed before the fix) and `:198` `test_decorator_normalises_valid_string_keys_to_permissions`; all green
- Status: ✅ Resolved

---

### ISS-002: Guard silently breaks `async` views 🟢 Low

**Category**: Correctness (latent)
**File**: `src/infrastructure/web/common/decorators.py` (`_guard`)

**Issue**:
`_guard` always returns a synchronous wrapper. For an `async def` view, the wrapper returns an un-awaited coroutine, and Django raises "didn't return an HttpResponse". `iscoroutinefunction(wrapper)` is `False` (probe above). No view is async today and the patterns don't call for async views, so this is latent.

**Suggested Fix** (either):
- Reject at decoration: `if inspect.iscoroutinefunction(view): raise TypeError("async views are not supported by require_permission")`, or
- Provide an async branch (`async def wrapper` + `markcoroutinefunction`) if async views are ever introduced.


**Resolution** (2026-10-21, DEV):
- Fix: `_guard` rejects coroutine functions at decoration with `TypeError("async views are not supported by the role guards")` (first suggested option; no async views exist, so no async branch is added)
- Commit / change ref: `src/infrastructure/web/common/decorators.py:36-38`
- Test evidence: `tests/integration/web/test_url_protection.py:189` `test_guards_reject_async_views_at_import[perm|auth]` (failed before the fix); green
- Status: ✅ Resolved

---

### ISS-003: `View` alias collides conceptually with `django.views.View` 🟢 Low

**Category**: Style / Maintainability
**File**: `src/infrastructure/web/common/decorators.py` (`View = Callable[..., HttpResponse]`)

**Issue**: Later stories will import both `django.views.View` (class-based views) and this module. A module-level `View` meaning "view callable" invites confusion or shadowing.

**Suggested Fix**: Rename to `ViewCallable` (or `ViewFunc`).


**Resolution** (2026-10-21, DEV):
- Fix: alias renamed `ViewCallable` (with a one-line comment on why); all 3 uses updated; `grep` showed no importers of the old name
- Commit / change ref: `src/infrastructure/web/common/decorators.py:22-23`, `_guard`, `require_permission`, `require_authenticated` signatures
- Test evidence: refactor only, no behaviour change (non-testable rename); mypy clean, full suite green
- Status: ✅ Resolved

---

### ISS-004: URL-coverage test never sees DEBUG-only routes 🟢 Low

**Category**: Testing / Security hygiene
**File**: `tests/integration/web/test_url_protection.py` (`test_every_url_is_protected_or_public`)

**Issue**: The test walks `ROOT_URLCONF` under `config.settings.test` (`DEBUG=False`). Routes registered only when `DEBUG=True` (today: Story 1.5's `styleguide:index`, intentionally unguarded) are never inspected. A future DEBUG-only route would ship without anyone noticing it's unguarded in dev. This isn't a production exposure, since those routes don't exist with `DEBUG=False`.

**Suggested Fix**: Add a second test that reloads the URLConf under `settings.DEBUG = True` (e.g. `override_settings(DEBUG=True)` + `clear_url_caches()` + `importlib.reload(config.urls)`), with an explicit allow-list `DEBUG_ONLY_URL_NAMES = {"styleguide:index"}`, so every unguarded dev route is a deliberate, reviewed decision.


**Deferral** (2026-10-21, DEV): deferred with user consent to **Story 1.6** (Molecule Primitives), which adds more DEBUG-only styleguide routes and is the natural place to introduce `DEBUG_ONLY_URL_NAMES` and the `DEBUG=True` walk. Still open.

**Resolution** (2026-10-22, DEV):
- Fix: `DEBUG_ONLY_URL_NAMES = frozenset({"styleguide:index"})` added to the test module; `_unprotected` takes an `allowed` set; a local `_debug_routing()` context manager / `debug_urlconf` fixture reloads `config.urls` under `override_settings(DEBUG=True)` + `clear_url_caches()` and restores production routing in `finally`. The new walk asserts every DEBUG-only route is guarded, public or allow-listed; each allow-list entry must resolve under `DEBUG=True` and NOT under `DEBUG=False` (stale entries fail); the styleguide stays out of `PUBLIC_URL_NAMES`. The existing `DEBUG=False` test and synthetic-list test are unchanged. No `src/` changes, no new routes
- Commit / change ref: `tests/integration/web/test_url_protection.py:42` (`DEBUG_ONLY_URL_NAMES`), `:54-64` (`_unprotected(..., allowed)`), `:75-121` (`_debug_routing`, `debug_urlconf`, `test_every_debug_only_url_is_protected_public_or_allow_listed`, `test_debug_only_allow_list_entries_exist_only_under_debug`, `test_debug_only_allow_list_is_exactly_the_styleguide`, `test_production_routing_is_restored_after_the_debug_walk`), `:290-297` (`test_coverage_check_excuses_only_allow_listed_debug_routes`); branch `feature/story-1.6-molecules`
- Test evidence: before (allow-list temporarily empty): `test_every_debug_only_url_is_protected_public_or_allow_listed` failed with `Unprotected DEBUG-only routes: ['styleguide:index']` (2 failed, 29 passed); stale-entry probe (`"styleguide:stale"` temporarily added) failed `test_debug_only_allow_list_entries_exist_only_under_debug[styleguide:stale]` with `NoReverseMatch`; after: `test_url_protection.py` + `ui/test_styleguide.py` 48/48 passed (routing restored: `test_styleguide_returns_404_in_production`, `test_production_routing_is_restored_after_the_debug_reload` green); ruff format/check clean, `uv run mypy` 0 issues; all green
- Status: ✅ Resolved

---

### ISS-005: Self-review describes the fixture stand-ins as still present 🟢 Low

**Category**: Documentation
**File**: `docs/stories-implemented/story-1.3-review.md` (Files Changed row for `test_role_access_matrix.py`; Gate 3 row; Deviations; Next Steps)

**Issue**: The stand-ins were removed when Story 1.3 was merged with 1.2 (`09b8dea`), and `CLIENT_FOR_ROLE` now resolves Story 1.2's `tests/conftest.py` fixtures. The review doc still says "temporary role-client stand-ins" and "delete them when Story 1.2 is merged".

**Suggested Fix**: Append a short "Post-merge note (2026-10-21)" stating the stand-ins were removed in `09b8dea`, and tick the Next Steps item. Don't rewrite the original evidence.


**Resolution** (2026-10-21, DEV):
- Fix: appended a "Post-merge note (2026-10-21)" (stand-ins removed in `09b8dea`; review remediation summary) and ticked the Next Steps items; original evidence untouched
- Commit / change ref: `docs/stories-implemented/story-1.3-review.md` (end of file)
- Test evidence: documentation-only (non-testable)
- Status: ✅ Resolved

---

## Issue Summary

| # | ID | Severity | Category | File | Status |
|---|-----|----------|----------|------|--------|
| 1 | ISS-001 | 🟡 Medium | Correctness | `decorators.py` `require_permission` | Should Fix |
| 2 | ISS-002 | 🟢 Low | Correctness (latent) | `decorators.py` `_guard` | Optional |
| 3 | ISS-003 | 🟢 Low | Style | `decorators.py` `View` alias | Optional |
| 4 | ISS-004 | 🟢 Low | Testing | `test_url_protection.py` | Optional |
| 5 | ISS-005 | 🟢 Low | Documentation | `story-1.3-review.md` | Optional |

**Summary**:
- Blockers: 0
- High: 0
- Medium: 1
- Low: 4

---

## What Was Done Well

1. ✅ The requirements matrix is spelled out literally in the test, so any drift in `ROLE_PERMISSIONS` fails CI.
2. ✅ The corrupt-role path parses to `None` and denies, closing the 500 that patterns §7.2's `Role(...)` would have produced.
3. ✅ The no-side-effects test inspects the actual SQL for writes, not just status codes.
4. ✅ The URL-coverage checker is tested on a synthetic list, so a green result means something.
5. ✅ The elevation test tries query parameters and a header, which matches the rulebook's IDOR checklist.
6. ✅ `RecordAccessPolicy` is pure and fully branch-covered, ready for the CYCLE-3 query services.

---

## Approval Status

**Decision**: ⚠️ APPROVED WITH COMMENTS

**Reason**: No blockers or high issues. ISS-001 should be fixed before routes start using the decorator in Story 1.7 / 2.2 (a two-line change plus a test). The Low items are optional.

**Next Steps**:
1. `aire-dev-remediate` for ISS-001 (and optionally ISS-002–ISS-005)
2. Continue with the remaining wave-2 reviews (1.2, 1.8, 1.1, 1.5, 2.1)

---

## Sign-Off

**Reviewer**: REVIEWER Agent
**Date**: 2026-10-21
**Signature**: Approved with comments

---

# 🛠️ Remediation — 2026-10-21

**Developer**: DEV Agent
**Severity Scope**: 🟡 Medium + chosen 🟢 Low (no 🔴/🟠 in this report); scope confirmed by the user
**Scenario**: Code Review
**Stories Affected**: 1.3
**Branch**: `feature/wave-2-dev-1` (after merging `feature/story-1.8-audit-log` in `fb28aab`)

## Issues Remediated

| ID | Severity | Story | File:Line | Summary | Resolution | Test Added |
|------|----------|-------|-----------|---------|------------|------------|
| ISS-001 | 🟡 Medium | 1.3 | `decorators.py:66` | Unknown permission keys accepted | `Permission(p)` at decoration → `ValueError` at import | `test_url_protection.py:180` (×3), `:198` ✅ |
| ISS-002 | 🟢 Low | 1.3 | `decorators.py:36-38` | Async views silently broken | `TypeError` at decoration | `test_url_protection.py:189` (×2) ✅ |
| ISS-003 | 🟢 Low | 1.3 | `decorators.py:22-23` | `View` alias ambiguous | Renamed `ViewCallable` | n/a (rename) |
| ISS-005 | 🟢 Low | 1.3 | `story-1.3-review.md` | Stale stand-in note | Post-merge note appended | n/a (docs) |
| ISS-004 | 🟢 Low | 1.3 → resolved in 1.6 (`feature/story-1.6-molecules`, 2026-10-22) | `test_url_protection.py:42-121` | DEBUG-only routes never walked | `DEBUG=True` URLConf walk + `DEBUG_ONLY_URL_NAMES` allow-list (non-vacuous, stale-checked) | `test_url_protection.py:95`, `:102`, `:114`, `:119`, `:290` ✅ |

## Issues Deferred (with user consent)

None remain. ISS-004 (originally deferred to Story 1.6 on 2026-10-21) was resolved on 2026-10-22; see the ISS-004 Resolution and the addendum below.

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `src/infrastructure/web/common/decorators.py` | Modified | Key validation, async rejection, `ViewCallable` |
| `tests/integration/web/test_url_protection.py` | Modified | 6 new tests (`import re` added) |
| `docs/stories-implemented/story-1.3-review.md` | Modified | Post-merge note |

## Patterns Applied

| Pattern | Where Applied | Notes |
|---------|---------------|-------|
| Fail fast at import (Story 1.3 AC 6) | `require_permission`, `_guard` | Misconfiguration breaks startup, never ships |
| Testing §12 (AAA, behavioural names) | new tests | Exact-message match on the rejected key |

## Testing Summary

- **Targeted tests added**: 6 (3 unknown-key cases, 1 normalisation, 2 async cases)
- **Full suite**: 598/598 passing
- **Coverage**: 100% (target ≥85%); `decorators.py` 100% (statements + branches); `src/domain` 100%
- **Gates**: ruff format/check clean · mypy 0 issues (86 files) · import-linter 2/2 kept · `makemigrations --check` no changes

**Test Output** (verbatim, filtered):
```
collected 598 items
tests/integration/web/test_url_protection.py .................           [ 49%]
tests/integration/web/test_url_protection.py ..........                  [ 54%]
TOTAL                                                     541      0     56      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
============================= 598 passed in 5.69s ==============================
```

## Deviations from Report Suggestions

- ISS-001: the first test draft used an alternation regex (`content:edt|CONTENT_EDIT|''`) that would pass if *any* key appeared. It was tightened to the exact `"<key>" is not a valid Permission` message per case.
- ISS-002: chose rejection over an async branch, because there are no async views and the patterns don't plan any.

## Lessons Learned

1. `StrEnum` membership checks accept plain strings, which hides typos. Validate at the boundary by constructing the enum.

## Next Steps

- [ ] Re-request code review (`aire-review-code`): optional (no 🔴 fixed)
- [x] ISS-004 with Story 1.6

## Addendum — Remediated with Story 1.6 (2026-10-22)

ISS-004 was resolved on `feature/story-1.6-molecules`. `tests/integration/web/test_url_protection.py` now also walks the root URLConf reloaded with `DEBUG=True` and allows only the explicit `DEBUG_ONLY_URL_NAMES = {"styleguide:index"}`. Production routing is restored in `finally`. Evidence: the DEBUG walk failed with `['styleguide:index']` while the allow-list was empty, and a stale allow-list entry failed with `NoReverseMatch`. With the fix, 48/48 tests pass across `test_url_protection.py` and `ui/test_styleguide.py`. Only the test file changed (it was already listed under Files Changed); `src/` is untouched. At Story 1.6 integration (2026-10-22), the full suite passed 980/980 in each of 3 consecutive runs (`uv run pytest -q --cov=src --cov-branch --cov-fail-under=85`), with 100% coverage.
