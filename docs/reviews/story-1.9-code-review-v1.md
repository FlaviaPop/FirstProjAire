# Code Review - Story 1.9: Admin Account Management & Parent–Child Links

**Date**: 2026-10-22
**Reviewed By**: REVIEWER Agent
**Review Number**: 1
**Review Mode**: INITIAL_REVIEW
**Status**: ⚠️ APPROVED WITH COMMENTS

---

## Review Metadata

**Previous Review**: None
**Previous Status**: N/A
**Files Changed Since Last Review**: All (first review). Reviewed at `main` @ `52dfd72` (story commit `61ce5aa`, built in one go by an atomic story-agent)
**Severity Threshold Applied**: All

---

## Review Summary

**Components Reviewed**:
- **Use cases:** `src/application/accounts/link_parent.py` (125 lines: `LinkParent`, `UnlinkParent`, `LinkExists`, `ParentLinkPort`) and `manage_account.py` (70: `AuditAccountChange`)
- **Admin:** `src/infrastructure/persistence/accounts/admin.py` (328: `PlatformAdminSite`, `PlatformUserAdmin`, `ParentChildLinkAdmin`, `AccessAttemptAdmin`, `AuditLogAdmin`) and `admin_forms.py` (132)
- **Persistence:** `models.py` (`UserModel.save` staff flags, `ParentChildLinkModel`), `repositories.py`, migration `accounts/0002_parentchildlink.py`
- **Audit changes:** `application/common/audit.py` (`MetadataValue`), `persistence/audit/repositories.py` (`_actor_name`), `audit/0003_verbose_names.py` (labels only)
- **Wiring:** `web/common/errors.py` (link error codes), `container.py`, `config/urls.py`
- **Translations:** RO/EN catalogues

**Lines of Code**: ~740 production lines (+156 changed), ~1,700 test lines
**Tests Reviewed**: Yes:
- `tests/integration/web/admin/` (account, password/delete, link, lockout/audit admin)
- `tests/unit/application/accounts/test_link_parent.py`, `test_unlink_parent.py`, `test_manage_account.py`
- `tests/integration/persistence/accounts/test_parent_child_link.py`, `test_parent_links_repository.py`
- the updated audit and user-model tests

**Coverage**: 100% overall. The six story modules are at 100% line and branch coverage, and domain/application are at 100%.

**Overall Assessment**: The most security-sensitive story so far, and the code holds up under every attack I tried:
- Every admin route rejects every non-admin role (70 route×method combinations).
- No inline script or style on any admin page, so it works under the strict CSP.
- No personal data in logs; audit metadata holds field **names** only.
- Deactivation ends the user's session at once.
- Unlocking works.
- The last-active-Admin rule covers demote, deactivate, delete, self-delete and bulk delete.
- `IMMEDIATE` transactions serialise concurrent admin saves, so the "last admin" race the build agent worried about can't happen.

The two findings are documentation and privacy hardening:
- The story file still describes the pre-decision contract, so QA will test against wrong expectations (ISS-001).
- The lockout list shows raw typed usernames, which can be mistyped passwords (ISS-002).

---

## Evidence Verified (re-run by REVIEWER, 2026-10-22)

Every gate is read from its own output line:
```
[ruff format]  155 files already formatted
[ruff check]   All checks passed!
[mypy]         Success: no issues found in 104 source files          (--no-incremental)
[lint-imports] Contracts: 2 kept, 0 broken.
[migrations]   No changes detected
src/application/accounts/link_parent.py                      54      0     14      0   100%
src/application/accounts/manage_account.py                   20      0      4      0   100%
src/infrastructure/persistence/accounts/admin.py            178      0     28      0   100%
src/infrastructure/persistence/accounts/admin_forms.py       66      0     14      0   100%
src/infrastructure/persistence/accounts/models.py            46      0      2      0   100%
src/infrastructure/persistence/accounts/repositories.py      28      0      2      0   100%
TOTAL                                                      1207      0    182      0   100%
1273 passed in 10.11s
Story modules alone: 302 passed in 2.21s
```

**Probes**: temporary test files, deleted afterwards (working tree clean), plus a real server on a fresh database.

```
# Every admin URL pattern (35 routes incl. catch-all, history, password, autocomplete, jsi18n, r/ shortcut) × GET/POST
PROBE anonymous: {302: 70}     PROBE student: {403: 70}     PROBE teacher: {403: 70}     PROBE parent: {403: 70}

# Real server (fresh DB, config.settings.dev), admin signed in through the platform login
GET /ro/admin/ -> 200
Content-Security-Policy: … style-src 'self'; … script-src 'self'; …
index / add / changelist / change / password / link add / audit list / lockouts / history:
  inline <script> 0 · style= 0 · <style> 0 · on*= 0   (all 9 pages)
POST add student (with DOB + password) -> 302 …/usermodel/2/change/
audit: accounts.created boss user 2 {'fields': ['date_of_birth', 'full_name', 'role', 'username']}
server log: ERROR lines 0 · DOB 0 · passwords 0 · names 0

# Lockout → unlock → sign in
after 5 failures + correct password: 429
unlock (bulk delete AccessAttempt) -> 302; next correct login -> 302 /ro/; audit ('auth.lockout_cleared', '2')

# Deactivation
deactivate a signed-in student -> 302; their next request -> 302 /ro/accounts/login/?next=… (session ended)
```

---

## Acceptance Criteria Check

| AC | Result | Evidence |
|----|--------|----------|
| 1 `is_staff = is_superuser = role == ADMIN` on every save | ✅ | `models.py` `save()` (also widens `update_fields`); tests in `test_user_model.py` |
| 2 `PlatformAdminSite`: titles, `has_permission`, `login` → 403 / platform sign-in, routed in `i18n_patterns` | ✅ (one documented deviation) | `admin.py:56-99`; probe 70×4. Deviation: an already-authorised Admin opening `/admin/login/` is redirected to the admin index instead of 403 (Django's own behaviour; noted in the self-review; harmless) |
| 3 `UserAdmin` list/filters/search/add/change forms, validators, excluded fields | ✅ | `admin.py:135-177`, `admin_forms.py:53-71`; weak-password test |
| 4 Guards: last active Admin, linked Student, linked Parent (+ owner decision 4: no delete) | ✅ | `admin_forms.py:43-88`, `admin.py:121-183`; tests for demote/deactivate/delete/self-delete/bulk |
| 5 `ParentChildLinkModel` FKs, unique + check constraints | ✅ | `models.py`, `0002_parentchildlink.py`; constraint tests |
| 6 `LinkParent.validate/execute`: four violations, re-validate in UoW, `IntegrityError`→`LinkExists`, audit | ✅ | `link_parent.py:60-99`; race test in `test_parent_link_admin.py` |
| 7 `UnlinkParent` idempotent, audited once | ✅ | `link_parent.py:102-125`; tests |
| 8 Link admin: limited choices, `clean()` maps violations, use cases on save/delete, read-only change | ✅ | `admin.py:215-260`, `admin_forms.py:91-132` |
| 9 `AuditAccountChange`: actions, names-only metadata, password changes | ✅ | `manage_account.py`; real-server audit row above |
| 10 `AccessAttemptAdmin` list; unlock audited | ✅ (target per owner decision 2; see ISS-002) | `admin.py:263-302`; unlock probe |
| 11 `AuditLogAdmin` read-only, list/filter/search/date hierarchy | ✅ | `admin.py:305-328`; no-button and POST-403 tests |
| 12 Container factories | ✅ | `container.py` |
| 13 Fixtures `linked_parent`, `unlinked_parent`; `ParentChildLinkFactory` | ✅ | `tests/conftest.py`, `tests/factories/accounts.py` |
| 14 Role-access rows for `/ro/admin/` | ✅ | `tests/integration/web/admin/`; extended by the 70-route probe |
| 15 RO/EN for new strings | ✅ (7 messages per owner decision 3; see ISS-001) | catalogue tests |

---

## Checklist Results

### Correctness
- [x] ✅ All system-response rows reproduced or covered by tests (including the duplicate-link race, CASCADE on delete with audit kept, unlock then sign in)
- [x] ✅ Concurrency: SQLite `transaction_mode="IMMEDIATE"` (`base.py:70`) serialises admin saves, so the last-admin and link-versus-role-change checks can't interleave
- [x] ✅ Deleting a user who authored audit rows works: the 1.8 trigger permits exactly the FK `SET NULL` update, and `actor_username` keeps the name

### Pattern Adherence
- [x] ✅ Use cases in the application layer (domain + stdlib only), ports as Protocols, `DjangoUnitOfWork`, wired in `container.py`; import-linter kept
- [x] ✅ Forms only shape input; link rules live in `LinkParent.validate` and are reused by the form, so there's one source of truth
- [x] ✅ Files < 400 lines (largest 328); functions < 30 lines

### Testing
- [x] ✅ Forged ids/usernames posted and proven ignored; every guard tested on every path; race simulated
- [x] ✅ Coverage 100%; domain/application 100%

### Documentation
- [x] ✅ Docstrings explain the why (IDOR guard, audit-before-delete, race retry)
- [x] ⚠️ The story file wasn't updated with the four owner decisions (ISS-001)
- [x] ✅ Self-review records the decisions, the deviations and the honest "no browser" limitation

### Security
- [x] ✅ Every admin route: anonymous → platform sign-in, non-admin → 403 (70×4 probe); `has_permission` re-reads the role per request, so a demoted Admin loses access at once
- [x] ✅ CSP-clean admin pages (9 pages, 0 inline script/style/handlers)
- [x] ✅ No personal data in logs; audit metadata = field names only; password inputs stripped from `fields`
- [x] ✅ Deactivation and password reset end sessions (session-hash/backend checks)
- [x] ⚠️ Lockout admin shows raw typed usernames (ISS-002)

### Performance
- [x] ✅ `list_select_related` on links; per-row audit inserts on bulk actions are fine at pilot scale

### SOLID / Anti-Monolith
- [x] ✅ Admin classes delegate to use cases; `admin_forms.py` split out to stay under the size limit

---

## Issues Found

### ISS-001: The story file still describes the pre-decision contract, so QA will test the wrong behaviour 🟡 Medium

**Category**: Documentation
**File**: `docs/plans/stories/epic-1-story-1.9-Admin-Accounts-and-Parent-Links.md` (AC 4, AC 10, AC 15, "System responses", "QA-observable behaviour")
**Pattern Reference**: SPEC CLAUDE.md "Reference First"; Story 2.1 precedent (owner decision recorded in the story file itself); `aire-qa-test-plan` derives scenarios from the story file

**Issue**:
The four owner decisions (2026-10-22) are implemented and recorded in `docs/stories-implemented/story-1.9-review.md`, but the story file, the contract QA plans from, still says:
- AC 15: "the **6** error messages". There are now 7 (separate Parent guard message).
- QA-observable: "Every admin save … produces **exactly one** corresponding `audit_log` row". A role change now writes two (`accounts.updated` + `accounts.role_changed`).
- AC 10: lockout cleared, "target username". It's now the user id, or `(unknown):<fingerprint>` for non-existent accounts.
- AC 4 / system responses: nothing about the last active Admin being **undeletable** (no button, POST 403, bulk delete refused).
- AC 2: "if authenticated → 403". An authorised Admin is now redirected to the index.

`aire-qa-test-plan` / `aire-qa-validate` will turn each of these into a failing scenario and raise false defects. Two of them (exactly one row; 6 messages) directly contradict the code.

**Suggested Fix**: add an "Owner decisions (2026-10-22)" block before the Acceptance Criteria (as Story 2.1 did), and amend the affected lines in place:
```markdown
> **Owner decisions (2026-10-22, recorded at implementation):**
> 1. Role change → two audit rows: `accounts.updated` {"fields": [...incl. "role"]} + `accounts.role_changed` {"fields": ["role"]}. Every other admin save writes exactly one row.
> 2. `auth.lockout_cleared` target = ("user", <id>) for an existing account, else ("user", "(unknown):<8-hex fingerprint>"); the typed text is never stored.
> 3. Parent guard message: "Remove this parent's child links before changing the role." (7 messages in total).
> 4. The last active Admin can't be deleted: no delete button, direct POST → 403, bulk delete refused with "There must be at least one active administrator."
> Implementation note: an Admin already signed in who opens `/admin/login/` is redirected to the admin index (others still get 403).
```
Then change AC 15's "6" to "7", the QA-observable sentence to "…exactly one row, except a role change which writes two", AC 10's "target username" to the decision-2 rule, and add a system-response row for deleting the last active Admin.

**Why This Matters**: the story file is the contract for QA and later stories. Leaving it stale turns correct behaviour into reported bugs and wastes a triage cycle.

---

### ISS-002: The lockout list shows (and searches) the raw typed username, which can be a mistyped password 🟢 Low

**Category**: Security / Privacy
**File**: `src/infrastructure/persistence/accounts/admin.py:277-280` (`AccessAttemptAdmin.list_display`, `search_fields`, `fields`)
**Pattern Reference**: owner decisions for Story 1.8 ISS-003 and Story 1.9 decision 2 ("never store the raw typed username" for non-existent accounts); patterns §9

**Issue**:
`AccessAttempt.username` is whatever was typed into the username box (stored by django-axes, Story 1.2). The audit log now deliberately avoids keeping that text for non-existent accounts, because users sometimes type their password there. The lockout admin still shows it verbatim to every Admin, in the list, the read-only detail and search, for as long as the lockout row exists. AC 10 asks for a `username` column, so this follows the letter of the story, but it undercuts the privacy rule the owner set twice.

**Suggested Fix**: show the same label the audit uses, so a real account still appears by name (which is what the Admin needs to unlock it):
```python
@admin.display(description=_("username"))
def account(self, obj: AccessAttempt) -> str:
    _user_id, label = _lockout_target(obj.username)
    return label  # real username for existing accounts, "(unknown):<fingerprint>" otherwise

list_display = ("account", "ip_address", "failures_since_start", "attempt_time")
fields = ("account", "ip_address", "failures_since_start", "attempt_time")
readonly_fields = ("account",)
```
Keep `search_fields = ("username",)` (an Admin searching for a known username still finds it), or restrict it to exact matches. Add a test that a lockout for a non-existent "username" is listed as `(unknown):…` and never shows the typed text.

---

## Issue Summary

| # | ID | Severity | Category | File | Status |
|---|-----|----------|----------|------|--------|
| 1 | ISS-001 | 🟡 Medium | Documentation | Story 1.9 file (AC 2/4/10/15, QA notes) | Should Fix |
| 2 | ISS-002 | 🟢 Low | Security / Privacy | `accounts/admin.py:277-280` | Optional |

**Summary**:
- Blockers: 0
- High: 0
- Medium: 1
- Low: 1

**Observation (not a 1.9 issue)**: each sign-in attempt against an already-locked account writes **two** audit rows (`auth.lockout` + `auth.login_failed`). That comes from Story 1.8's signal handling and adds to the audit-growth item already deferred to DevOps (Story 1.8 review ISS-004).

---

## What Was Done Well

1. ✅ **Airtight access control**: `admin_view` is wrapped before Django's own wrapper, so non-admins never see Django's login form. It is proven across all 35 admin routes × GET/POST × 4 roles.
2. ✅ **Privacy by construction**: only field names cross into the audit use case; password inputs are stripped; logs carry no DOB, password or name (real server).
3. ✅ **Every path of the last-admin rule** (demote, deactivate, delete, self-delete, bulk) is tested, plus the owner's deletion decision.
4. ✅ **One source of truth for link rules**: `LinkParent.validate` serves both the form and the race-safe `execute`, with `IntegrityError` mapped to a friendly form error on a lost race.
5. ✅ **CSP-compatible admin**: 9 pages with no inline script or style under `script-src 'self'; style-src 'self'`.
6. ✅ **Found and fixed a gate issue elsewhere**: the build agent caught the mypy error left by the Story 1.6 remediation instead of ignoring it.

---

## Approval Status

**Decision**: ⚠️ APPROVED WITH COMMENTS

**Reason**: no blockers and no high-severity issues; the code is correct and secure under every probe. ISS-001 should be fixed before `aire-qa-test-plan` runs for Epic 1, or QA will report false defects. ISS-002 is optional privacy hardening.

**Next Steps**:
1. `aire-dev-remediate` for ISS-001 (recommended; documentation only), with ISS-002 optional.

---

## Sign-Off

**Reviewer**: REVIEWER Agent
**Date**: 2026-10-22
**Signature**: Approved with comments
