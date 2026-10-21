# Story 1.3 Self-Review

**Date**: 2026-10-21
**Story**: RBAC Core (CYCLE-1, wave 2, Dev 2)
**Developer**: DEV Agent
**Branch**: `feature/story-1.3-rbac-core` (from `main` @ `2c24482`, Story 1.0 merged)

---

## What Was Implemented

- `Role` StrEnum + `parse_role()` (unknown → `None`, never raises)
- `Permission` StrEnum (16 keys verbatim from `docs/requirements.md`), read-only `ROLE_PERMISSIONS` (`MappingProxyType` of `frozenset`s), `has_permission()`
- `can_view_student_records()` / `RecordAccessPolicy.can_view_student_records`: pure record-scope rule (own / linked child / `scores:view-all`; unknown role → False)
- `@require_permission(*keys)` (ALL keys; 403; anonymous → login with `next`; no keys → `ValueError`) and `@require_authenticated`, both exposing `required_permissions` and preserving name/doc, for function and class-based views
- Cross-cutting tests (patterns §12.4): matrix-equals-requirements, URL-coverage walker, role-by-route harness (`CLIENT_FOR_ROLE` / `ROWS`), `Role` = `ROLE_CHOICES`

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `src/domain/accounts/__init__.py` | New | Package |
| `src/domain/accounts/roles.py` | New | `Role`, `parse_role` |
| `src/domain/accounts/permissions.py` | New | `Permission`, `P`, `ROLE_PERMISSIONS`, `has_permission` |
| `src/domain/accounts/access_policy.py` | New | `can_view_student_records`, `RecordAccessPolicy` |
| `src/infrastructure/web/common/decorators.py` | Modified (shared) | Imports added at top; `PUBLIC_URL_NAMES` line unchanged; `GuardedView`, `_guard`, `require_permission`, `require_authenticated` appended |
| `tests/unit/domain/accounts/test_permissions.py` | New | 16 tests: matrix literal, 16 keys, read-only, frozensets, `has_permission`, `parse_role` |
| `tests/unit/domain/accounts/test_access_policy.py` | New | 12 tests: policy table + class alias |
| `tests/unit/domain/accounts/test_roles_match_model.py` | New | 1 test: `Role` = `ROLE_CHOICES` |
| `tests/integration/web/test_url_protection.py` | New | 21 tests: URL coverage, decorator per-role, anonymous `next`, no side effects, no elevation, `ValueError`, wrapper metadata, the coverage checker itself |
| `tests/integration/web/test_role_access_matrix.py` | Modified (shared) | `CLIENT_FOR_ROLE`, `ROWS` (`/healthz` × 5 roles), `test_role_access_matrix`, temporary role-client stand-ins |
| `docs/status.md` | Modified | Story Tracker start/end |

## Patterns Applied

| Pattern | Where Applied | Notes |
|---------|---------------|-------|
| Domain pattern §4 | `domain/accounts/*` | StrEnums, pure functions, stdlib only, docstrings (Google style) |
| Authorization decorator §7.2 | `decorators.py` | Uses `parse_role` instead of `Role(...)` so a corrupt role is 403, not 500 (story AC 6) |
| Mandatory cross-cutting tests §12.4 | `test_permissions.py`, `test_url_protection.py`, `test_role_access_matrix.py` | Expected matrix written literally in the test |
| Security §13 / IDOR guard | decorator + policy | Identity only from `request.user`; tested against `?role=`/`?as=`/headers |
| ADR-007 | whole story | No Django Groups/Permissions tables |

## Testing Summary

- **Unit tests**: 36 (29 new in `tests/unit/domain/accounts`: 16 + 12 + 1; plus 7 existing `test_env`), all passing
- **Integration tests**: 49 (26 new: 21 in `test_url_protection.py` + 5 `test_role_access_matrix` rows; plus 23 existing), all passing
- **Full suite**: 85 passed
- **Coverage**: 100.00% overall; `src/domain` 100% (statements + branches)

**Test output** (verbatim; per-file 100% rows and environment header omitted):
```
============================= test session starts ==============================
django: version: 5.2.18, settings: config.settings.test (from ini)
testpaths: tests
collected 85 items

tests/integration/persistence/accounts/test_user_model.py ........       [  9%]
tests/integration/web/test_healthz.py .........                          [ 20%]
tests/integration/web/test_role_access_matrix.py ......                  [ 27%]
tests/integration/web/test_url_protection.py .................           [ 47%]
tests/integration/persistence/accounts/test_restart_persistence.py ..... [ 52%]
                                                                         [ 52%]
tests/integration/web/test_url_protection.py ....                        [ 57%]
tests/unit/config/test_env.py .......                                    [ 65%]
tests/unit/domain/accounts/test_access_policy.py ............            [ 80%]
tests/unit/domain/accounts/test_permissions.py ................          [ 98%]
tests/unit/domain/accounts/test_roles_match_model.py .                   [100%]

================================ tests coverage ================================

TOTAL                                                   149      0     16      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
============================== 85 passed in 1.36s ==============================
```

## DoD Evidence

### Quality gates (2026-10-21)

```
$ uv run ruff format --check .
43 files already formatted
$ uv run ruff check .
All checks passed!
$ uv run mypy
Success: no issues found in 41 source files
$ PYTHONPATH=src uv run lint-imports
Domain is framework-free KEPT
Contracts: 2 kept, 0 broken.
$ uv run python manage.py makemigrations --check --dry-run
No changes detected
$ uv run pytest --cov=src --cov-branch --cov-fail-under=85
85 passed — Total coverage: 100.00%
$ uv run coverage report --include="src/domain/*" --fail-under=100
TOTAL                                     49      0      6      0   100%
exit=0
```
(`mypy` applies `strict = true` to `domain.*` via `pyproject.toml`, so `domain.accounts` is strict-checked.)

### Manual checks (real `runserver`, scratch route `@require_permission(CONTENT_EDIT)` appended to `urls.py` locally and reverted; `git diff src/config/urls.py` empty afterwards)

```
== real server: GET /scratch-edit per role
STUDENT    -> 403
TEACHER    -> 200
PARENT     -> 403
ADMIN      -> 403
SUPERHERO  -> 403          (user whose role column was set to "SUPERHERO" in the DB)
STUDENT 403 body:
<!doctype html> … <title>403 Forbidden</title> … <h1>403 Forbidden</h1>
== anonymous
302 http://localhost:8767/accounts/login/?next=/scratch-edit%3Fx%3D1
== URL-coverage test with an unguarded scratch route
E       AssertionError: Unprotected routes: ['scratch-edit']
1 failed in 0.06s
```

### Gate 1 — Spec Echo

| # | Requirement | Proof |
|---|-------------|-------|
| AC1 | `Role` = STUDENT/TEACHER/PARENT/ADMIN, values = `ROLE_CHOICES` keys | `src/domain/accounts/roles.py:6-12`; `test_persisted_role_choices_equal_domain_roles` |
| AC2 | `Permission` = exactly 16 keys, identical strings | `permissions.py:9-26`; `test_permission_keys_are_exactly_the_sixteen_from_requirements` |
| AC3 | `ROLE_PERMISSIONS` `MappingProxyType` of `frozenset`s = matrix (literal in test) | `permissions.py:31-56`; `test_permission_matrix_matches_requirements`, `test_matrix_is_read_only`, `test_matrix_values_are_frozensets` |
| AC4 | `has_permission`; `parse_role` → `None` for unknown | `permissions.py:59-61`, `roles.py:15-28`; `test_has_permission[*]`, `test_parse_role_rejects_unknown_values[*]`, `test_parse_role_accepts_canonical_values[*]` |
| AC5 | `RecordAccessPolicy.can_view_student_records` rules; unknown role False; pure; 100% branches | `access_policy.py:9-40`; `test_can_view_student_records[*]` (11 cases), `test_policy_class_exposes_the_same_rule`; branch coverage 6/6 |
| AC6 | `require_permission`: ≥1 key (`ValueError`), anonymous → `redirect_to_login(full_path)`, unknown role → 403, ANY missing → 403, exposes `required_permissions` | `decorators.py:34-60`; `test_decorator_requires_at_least_one_permission`, `test_anonymous_is_redirected_to_login_with_next[/edit?x=1]`, `test_decorators_enforce_role_permissions[*]` (incl. SUPERHERO, child-and-all), `test_wrappers_expose_required_permissions_and_names`; manual curl |
| AC7 | `require_authenticated`: anonymous → login, valid role → runs, `required_permissions = ()` | `decorators.py:63-65`; `[STUDENT-/any]`, `[PARENT-/any]`, `[SUPERHERO-/any]=403`, `test_anonymous_…[/any?x=1]`, wrapper test |
| AC8 | `functools.wraps`; function views and `View.as_view()` | `decorators.py:35`; `_edit.__name__/__doc__` asserts; `[ADMIN-/review]=200`, `[TEACHER-/review]=403` (class-based) |
| AC9 | URL-coverage walker; `namespace:name` vs `PUBLIC_URL_NAMES`; `admin` exempt; unnamed patterns fail | `test_url_protection.py` `_leaves`/`_unprotected`; `test_every_url_is_protected_or_public` (real URLConf), `test_coverage_check_reports_unguarded_and_unnamed_routes` (`["open","nameless"]`); manual: names `scratch-edit` |
| AC10 | `CLIENT_FOR_ROLE` (5 entries) + `ROWS`; `/healthz` 200 for every role | `test_role_access_matrix.py`; 5 `test_role_access_matrix[*]` rows pass |
| AC11 | Denied request: no DB writes, no session change, identical repeat | `test_denied_request_has_no_side_effects_and_repeats_identically` (captured SQL has no INSERT/UPDATE/DELETE; session count and `last_login` unchanged; identical bodies) |
| AC12 | `src/domain/accounts` coverage 100% | `coverage report --include="src/domain/*" --fail-under=100` → 100%, exit 0 |
| Step 1 | Tests first | domain tests: 3 collection errors before code; decorator tests: collection error before code |
| Step 2 | `roles.py`, `permissions.py` per patterns §4 | files above |
| Step 3 | `access_policy.py` | file above |
| Step 4 | Decorators extend seeded file; `PUBLIC_URL_NAMES` kept | `decorators.py:19` unchanged `frozenset({"healthz"})` |
| Step 5 | URL-coverage test | `test_url_protection.py` |
| Step 6 | Matrix harness | `test_role_access_matrix.py` |
| Step 7 | All gates; domain 100% | gate output above |
| Ref: requirements Roles & Permissions Matrix | verbatim keys and role sets | literal `EXPECTED` in `test_permissions.py` equals the table at `docs/requirements.md:37-42` |
| Ref: architecture Roles & Authorization | role check = 403, record scope = 404; identity from session | decorator raises `PermissionDenied`; policy returns bool for the query layer to raise `NotFound` (query services are CYCLE-3) |
| Ref: ADR-007 | code-defined map; no Groups tables | Gate 2 grep |
| Ref: patterns §12.4 | three mandatory tests exist with those names | `test_permission_matrix_matches_requirements`, `test_every_url_is_protected_or_public`, `test_role_access_matrix` |

AC rows: 12 of 12.

### Gate 2 — Negative-Space Check

| Rule | Check | Result |
|------|-------|--------|
| Domain imports stdlib only | import-linter "Domain is framework-free"; `grep -rnE "^(import\|from) " src/domain` excluding stdlib/domain | KEPT; "domain imports: stdlib + domain only" |
| No Django Groups/Permissions (ADR-007 rejected) | `grep -rn "Group\|auth.models.Permission" src` | none |
| No TODO/FIXME/`csrf_exempt`/`mark_safe` | grep `src tests` | none |
| Role never taken from request input | `test_role_cannot_be_elevated_by_request_parameters` (`?role=TEACHER&as=ADMIN`, `X-Role` header) | 403 |
| Corrupt role never granted | `[SUPERHERO-*]` tests; manual SUPERHERO → 403; policy `("SUPERHERO", …) → False` | ✓ |
| No side effects on denial | AC 11 test | ✓ |
| Out of scope not built (ParentChildLink, admin restriction, nav hiding, login view) | `ls src/infrastructure/persistence/accounts` unchanged; no `LOGIN_URL` set; no templates changed | ✓ |

### Gate 3 — Contract Consistency

| Producer | Consumer | Consistent? |
|----------|----------|-------------|
| `Role` values | `UserModel.ROLE_CHOICES` (Story 1.0) | ✓ test-proven |
| `Permission` values | `docs/requirements.md` keys | ✓ test-proven |
| `required_permissions` on wrappers | `test_every_url_is_protected_or_public` | ✓ (introspection works for function and CBV wrappers) |
| `PUBLIC_URL_NAMES` | URL-coverage walker + seeded `test_public_routes_are_reachable_anonymously` | ✓ |
| `CLIENT_FOR_ROLE` fixture names | Story 1.2 `tests/conftest.py` fixture names (`student_client`, `teacher_client`, `parent_client`, `admin_client`) | ✓ same names; stand-ins to be removed on merge |
| `redirect_to_login` target | `settings.LOGIN_URL` (default `/accounts/login/` until Story 1.2 sets it) | ✓ manual 302 shows `next` with full path |

## Challenges Encountered

| Challenge | Resolution | Time Spent |
|-----------|------------|------------|
| `CLIENT_FOR_ROLE` needs Story 1.2's role-client fixtures, which are being built in parallel on Dev 1's branch | Module-local stand-ins with the same names (`UserFactory(role=…)` + `force_login`); no edit to the shared `tests/conftest.py` | 10 min |
| mypy rejects attaching `required_permissions` to a plain function | `GuardedView` Protocol + `cast` | 5 min |
| Real-server check without a login view (Story 1.2) | Sessions created with `Client.force_login` in the dev DB, sent to `runserver` via `curl -b sessionid=…` | 10 min |

## Deviations from Plan

- **Decorator uses `parse_role`** rather than patterns §7.2's `Role(request.user.role)`, which would raise `ValueError` → 500 for a corrupt role. This follows the story (AC 6: unknown role → 403), which is newer and more specific.
- **`RecordAccessPolicy`** is a thin class exposing the module-level function, so both names from the story (AC 5 and Step 3) work.
- **Imports in `decorators.py` were added at the top** of the shared file. `PUBLIC_URL_NAMES` itself is untouched, but its line moved down. Merging with Story 1.2, which also edits `PUBLIC_URL_NAMES`, may need a trivial manual resolution.
- **Temporary fixture stand-ins** in `test_role_access_matrix.py`: delete them when Story 1.2 is merged (they shadow conftest fixtures of the same name).
- **403 page evidence** is the response HTML from `curl`, not a browser screenshot (no browser in this environment). The page is Django's default until Story 1.1's `handler403` lands.
- **Extra tests** beyond the story's list: no-elevation via parameters/headers, all-keys-required negative, class-based view, coverage checker's own behaviour, accepted role values, frozenset values.

## Lessons Learned

1. A guard that converts input with `Enum(value)` turns bad data into a 500. Parsing to `None` keeps denial the default.
2. Test the coverage walker itself on a synthetic URL list. Otherwise "no offenders" could just mean "the walker found nothing".

## Next Steps

- [ ] Commit on `feature/story-1.3-rbac-core`; merge order with wave 2: remove the fixture stand-ins when 1.2 lands
- [ ] Ready for code review (`aire-review-code`)
- [ ] Dev 2 next: Story 1.8 (Audit Log), then 1.4 (Internationalization)
