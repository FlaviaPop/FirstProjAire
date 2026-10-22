# Story 1.9 Self-Review

**Date**: 2026-10-22
**Story**: Admin Account Management & Parent–Child Links (CYCLE-1, wave 3, in-one-go, atomic)
**Developer**: DEV Agent (story agent)
**Branch**: `feature/story-1.9-admin-accounts` (from `edc95f3`)

---

## What Was Implemented

- **`PlatformAdminSite`** (`name="admin"`), routed at `/<lang>/admin/` inside `i18n_patterns`. Only an active Admin-role account gets in. A signed-in non-Admin gets the platform's 403 page (Story 1.1), never Django's admin login form. Anonymous visitors are redirected to `accounts:login?next=…`. The site header, title and index title are translated (RO/EN).
- **`UserModel.save()`** derives `is_staff = is_superuser = (role == "ADMIN")` on every save, including `save(update_fields=[…"role"…])`. Demoting an Admin removes their access on the next request.
- **`ParentChildLinkModel`** with `UNIQUE(parent, student)` and `CHECK(parent <> student)`. CASCADE on both parties, SET_NULL on `created_by`. Migration `accounts/0002_parentchildlink`, reversible.
- **Use cases** (application layer, stdlib + domain only, mypy strict):
  - `LinkParent` (validate + race-safe execute + audit)
  - `UnlinkParent` (idempotent)
  - `AuditAccountChange` (field names only)
- **`DjangoParentLinks`** repository. `IntegrityError` → `LinkExists`.
- **Admin screens:**
  - **Accounts:** create, edit, deactivate, delete, password reset.
    - Guarded: you can't demote, deactivate or delete the last active Admin; you can't change the role of a Student or Parent who still has links.
    - Audited.
  - **Parent–child links:** add or delete only, through the use cases.
  - **Sign-in lockouts** (axes `AccessAttempt`): deleting an attempt unlocks the account; audited.
  - **Audit log:** read-only.
- **Container factories:** `audit_account_change()`, `link_parent()`, `unlink_parent()`.
- **Fixtures:** `linked_parent`, `unlinked_parent`, `ParentChildLinkFactory`. `AdminFactory` no longer sets the staff flags; `save()` derives them.
- **RO/EN catalogues:** every new string, including the 7 guard and link messages (owner decision 3).

### Owner decisions (2026-10-22) applied

| # | Decision | Where |
|---|----------|-------|
| 1 | Role change writes **two** rows: `accounts.updated` `{"fields": [all changed incl. "role"]}` + `accounts.role_changed` `{"fields": ["role"]}`. Every other save writes exactly one row. | `admin.py:185-192`; tests `test_user_admin.py:205,221,197` |
| 2 | `auth.lockout_cleared` target is `("user", <id>)` for an existing account, otherwise `("user", "(unknown):<8-hex username_fingerprint>")` (`(empty)` for a blank one). Never the raw typed text. Goes through `AuditAccountChange` (action in `ACCOUNT_ACTIONS`, no fields metadata, so `{}`). | `admin.py:263-301`, `manage_account.py:13-23,67`; tests `test_lockout_and_audit_admin.py:45,68,83,91`, `test_manage_account.py:74,84` |
| 3 | The Parent guard has its own message, "Remove this parent's child links before changing the role." (RO + EN). The Student text stays verbatim. **AC 15 count is 7 messages, not 6.** | `admin_forms.py:24-27`; tests `test_user_admin.py:287`, `test_admin_translations.py:64` |
| 4 | The last active Admin can't be deleted: there is no delete button, a direct POST gets 403, and bulk delete is refused with "There must be at least one active administrator." This includes deleting yourself. All three paths are tested. | `admin.py:121-132,179-183`; tests `test_user_admin_password_and_delete.py:97,103,111,128,139` |

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `src/application/accounts/link_parent.py` | New | `LinkExists`, `ParentLinkPort`, `LinkParentCommand`, `LinkParent`, `UnlinkParent` |
| `src/application/accounts/manage_account.py` | New | `ACCOUNT_ACTIONS`, `AuditAccountChange` |
| `src/application/common/audit.py` | Modified (out of list) | `MetadataValue = str \| int \| bool \| list[str]` |
| `src/infrastructure/persistence/accounts/models.py` | Modified | staff-flag derivation; `ParentChildLinkModel`; translated verbose names and role labels |
| `src/infrastructure/persistence/accounts/migrations/0002_parentchildlink.py` | New (generated) | link table + no-op `AlterField`s (verbose names) |
| `src/infrastructure/persistence/accounts/repositories.py` | Modified | `DjangoParentLinks` appended |
| `src/infrastructure/persistence/accounts/admin.py` | New | site + 4 registrations (328 lines) |
| `src/infrastructure/persistence/accounts/admin_forms.py` | New | creation/change/link forms + guards (split per tasks.json, 133 lines) |
| `src/infrastructure/persistence/accounts/apps.py` | Modified (out of list) | translated app name "Accounts" |
| `src/infrastructure/persistence/audit/repositories.py` | Modified (out of list) | list metadata type; fills `actor_username` from the actor |
| `src/infrastructure/persistence/audit/models.py` | Modified (out of list) | translated verbose names (no schema change) |
| `src/infrastructure/persistence/audit/migrations/0003_verbose_names.py` | New (generated, out of list) | SQL no-op (`sqlmigrate`: all `(no-op)`); triggers untouched |
| `src/infrastructure/persistence/audit/apps.py` | Modified (out of list) | translated app name "Audit log" |
| `src/infrastructure/web/common/errors.py` | Modified (out of list) | 4 link codes in `ERROR_MESSAGES` (no format params) |
| `src/infrastructure/container.py` | Modified | 3 factories in the accounts block (alphabetical) |
| `src/config/urls.py` | Modified | `path("admin/", platform_admin_site.urls)` in `i18n_patterns` |
| `src/infrastructure/i18n/locale/{ro,en}/LC_MESSAGES/django.po` | Modified | 39 new msgids, 0 fuzzy, 0 obsolete |
| `tests/conftest.py`, `tests/factories/accounts.py` | Modified | `linked_parent`, `unlinked_parent`, `ParentChildLinkFactory`; `AdminFactory` flags derived |
| `tests/fakes/parent_links.py`, `tests/fakes/__init__.py` | New / Modified (out of list) | shared `FakeParentLinks` |
| `tests/unit/application/accounts/test_{link_parent,unlink_parent,manage_account}.py` | New | 29 unit tests with fakes |
| `tests/integration/persistence/accounts/test_parent_child_link.py` | New | DB constraints, cascade, SET_NULL (`transaction=True`, no audit rows) |
| `tests/integration/persistence/accounts/test_parent_links_repository.py` | New | repository, container wiring, fixtures |
| `tests/integration/persistence/accounts/test_user_model.py` | Modified | staff-flag derivation for every role, `update_fields` |
| `tests/integration/persistence/audit/test_audit_log.py` | Modified | list metadata; `actor_username` fill-in |
| `tests/integration/web/admin/*.py` | New | access matrix, users, password/delete, links, lockouts and audit log, translations, privacy sweep; `admin_helpers.py` |

## Patterns Applied

| Pattern | Where Applied | Notes |
|---------|---------------|-------|
| Use case + UoW (§5) | `LinkParent`, `UnlinkParent`, `AuditAccountChange` | ports as in-module Protocols; Clock injected; returns ids/bools |
| Repository + IntegrityError mapping (§6.3) | `DjangoParentLinks.add` | `raise LinkExists() from exc` |
| Models + constraints + migrations (§6.2/6.4) | `ParentChildLinkModel`, 0002 | generated, reversible (verified both directions) |
| Forms for shape, rules via use case (§7.3) | `ParentChildLinkForm.clean` → `LinkParent.validate` | violations mapped to field and non-field errors |
| Errors keyed by code (§8) | `ERROR_MESSAGES` link codes | `LinkExists` escaping → 409 page with localized text |
| Audit inside the transaction (§9) | admin `save_model`/`delete_*` run inside Django admin's `atomic`; password views wrapped in `transaction.atomic()` | an audit failure rolls the change back |
| Identity from the session (IDOR) | `_actor_id(request)`, `form.actor_id` set in `get_form` | forged `created_by`/`actor_id`/`is_staff` POST fields are ignored (tested) |
| Fakes, not mocks (§12.2) | `FakeParentLinks`, `FakeAuditPort`, `FakeUnitOfWork`, `FixedClock` | AAA, behavioural names |

## Testing Summary

- **Unit tests:** 29 new, all passing (application coverage 100%)
- **Integration tests:** 80 persistence (new + extended) + 211 admin integration, all passing
- **Full suite:** 1273 passed, 0 failed (3 consecutive runs)
- **Coverage:** 100.00% lines + branches (target 85%); domain 100%; application 100%

**Test Output** (see DoD Evidence for the complete verbatim gate output):
```
### unit
29 passed in 0.04s
### persistence
80 passed in 0.27s
### admin integration
211 passed in 0.99s
### cross-cutting (url protection, translations complete, unsafe-html, permission matrix)
159 passed in 0.28s
```

## DoD Evidence

### Quality gates (verbatim, 2026-10-22)

```
### run 1
TOTAL                                                      1207      0    182      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
1273 passed in 9.97s
### run 2
TOTAL                                                      1207      0    182      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
1273 passed in 10.20s
### run 3
TOTAL                                                      1207      0    182      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
1273 passed in 9.89s
### domain/application coverage
TOTAL                                     79      0      8      0   100%
TOTAL                                                     142      0     28      0   100%
### ruff format
155 files already formatted
### ruff check
All checks passed!
### mypy
src/infrastructure/web/templatetags/ui_molecules.py:72: error: Unsupported operand types for | ("dict[str, str | bool]" and "dict[str, str]")  [operator]
Found 1 error in 1 file (checked 104 source files)
### lint-imports
Layers point inward KEPT
Domain is framework-free KEPT

Contracts: 2 kept, 0 broken.
### makemigrations --check
No changes detected
exit=0
```

**mypy note:** the single error is **pre-existing**. It comes from `ui_molecules.py`, which this story doesn't touch, and was introduced by `edc95f3` (Story 1.6 review remediation). Running mypy on an untouched `git archive HEAD` snapshot gives the identical `Found 1 error in 1 file (checked 98 source files)`. Every file this story adds or changes is mypy-clean, and `application.*` passes strict mode.

### Translations

`makemessages -l ro -l en --no-wrap --ignore=.venv --ignore=.claude --ignore=docs --ignore=SPEC --ignore=tests` reported:

```
processing locale en
processing locale ro
```

It fuzzy-matched four new msgids to old ones. I reviewed each one and rewrote it:
- `Access` matched `Access denied`; now "Acces".
- `actor username` matched `Username`; now "numele de utilizator al autorului".
- `parent-child link(s)` matched the earlier en-dash spelling; now "legătură/legături părinte-copil".

Every new RO msgstr is filled with correct diacritics (ș ț ă â î). EN msgstr equals the msgid (project convention). No new plurals.

```
ro fuzzy=0 obsolete=0 msgids=144
en fuzzy=0 obsolete=0 msgids=144
$ uv run python manage.py compilemessages --ignore=.venv
File “…/locale/en/LC_MESSAGES/django.po” is already compiled and up to date.
File “…/locale/ro/LC_MESSAGES/django.po” is already compiled and up to date.
```

The four existing entries the diff shows as "removed" (`Student`, `Română`, `English`, `(required)`) were only reordered by makemessages. Each still exists exactly once with its original msgstr.

### Migrations (fresh DB, both directions)

```
$ DATABASE_PATH=<tmp>/real.sqlite3 DJANGO_SETTINGS_MODULE=config.settings.dev uv run python manage.py migrate
  Applying accounts.0001_initial... OK
  Applying accounts.0002_parentchildlink... OK
  Applying audit.0001_initial... OK
  Applying audit.0002_append_only_triggers... OK
  Applying audit.0003_verbose_names... OK
$ migrate audit 0002 → Unapplying audit.0003_verbose_names... OK ; migrate audit → Applying ... OK
$ migrate accounts 0001 → Unapplying accounts.0002_parentchildlink... OK ; migrate accounts → Applying ... OK
$ sqlite3 … "select name from sqlite_master where type='trigger';"
audit_log_append_only_delete
audit_log_append_only_update
```

`sqlmigrate audit 0003` and the `AlterField`/`AlterModelOptions` steps of `accounts 0002` are all `-- (no-op)`, so no table rebuild happens and the append-only triggers survive.

### Real-server check (`runserver 127.0.0.1:8767 --noreload`, fresh DB, real CSRF tokens, curl)

```
anonymous GET /ro/admin/                                   302 http://127.0.0.1:8767/ro/accounts/login/?next=/ro/admin/
admin sign-in                                              302 http://127.0.0.1:8767/ro/
admin GET /ro/admin/                                       200
Administrarea platformei de învățare
create Student ana (weak password 12345678)                200
create Student ana (strong password)                       302 http://127.0.0.1:8767/ro/admin/accounts/usermodel/2/change/
create Parent mama                                         302 http://127.0.0.1:8767/ro/admin/accounts/usermodel/3/change/
create Teacher prof                                        302 http://127.0.0.1:8767/ro/admin/accounts/usermodel/4/change/
accounts: boss=1 ana=2 mama=3 prof=4
link mama -> ana                                           302 http://127.0.0.1:8767/ro/admin/accounts/parentchildlinkmodel/
link mama -> ana again (duplicate)                         200
Acest părinte este deja legat de acest elev.
link prof (Teacher) as parent (guard)                      200
Contul de părinte selectat nu este de tip Părinte/Tutore.
change linked ana role -> TEACHER (guard)                  200
Eliminați legăturile elevului cu părinții înainte de a schimba rolul.
demote last admin boss (guard)                             200
Trebuie să existe cel puțin un administrator activ.
delete last admin boss (direct POST)                       403
edit ana DOB                                               302 http://127.0.0.1:8767/ro/admin/accounts/usermodel/
reset ana password                                         302 http://127.0.0.1:8767/ro/admin/accounts/usermodel/2/change/
teacher sign-in                                            302 http://127.0.0.1:8767/en/
teacher GET /ro/admin/                                     403
teacher GET /ro/admin/audit/auditlogmodel/                 403
ana: 5 wrong passwords                                      200 200 200 200 429
ana: right password while locked                           429
admin clears ana's lockout                                 302 http://127.0.0.1:8767/ro/admin/
ana: right password after unlock                           302 http://127.0.0.1:8767/ro/
unlink mama -> ana                                         302 http://127.0.0.1:8767/ro/admin/
unlink again (no-op)                                       302 http://127.0.0.1:8767/ro/admin/
admin GET audit log                                        200
admin POST audit add (forged)                              403
--- staff flags (username|role|is_staff|is_superuser)
boss|ADMIN|1|1
ana|STUDENT|0|0
mama|PARENT|0|0
prof|TEACHER|0|0
--- audit_log (admin actions)
accounts.created|boss|user|2|{"fields": ["date_of_birth", "full_name", "role", "username"]}
accounts.created|boss|user|3|{"fields": ["date_of_birth", "full_name", "role", "username"]}
accounts.created|boss|user|4|{"fields": ["date_of_birth", "full_name", "preferred_language", "role", "username"]}
accounts.parent_linked|boss|parent_child_link|1|{"parent_id": 3, "student_id": 2}
accounts.updated|boss|user|2|{"fields": ["date_of_birth"]}
accounts.password_changed|boss|user|2|{"fields": []}
auth.lockout|ana|||{}
auth.lockout|ana|||{}
auth.lockout_cleared|boss|user|2|{}
accounts.parent_unlinked|boss|parent_child_link|1|{"parent_id": 3, "student_id": 2}
```

The weak password (EN page) showed `This password is entirely numeric.` and `This password is too common.`

Server log scan (156 JSON lines). Each count is the number of log lines containing that value:

```
ERROR lines: 0
2018-03-02: 0   2018-03-03: 0   1988-07-01: 0   1980-02-02: 0   1980-01-10: 0
Ana-Start-2026: 0   Ana-Reset-2026: 0   Boss-Pilot-2026: 0   Mama-Start: 0   Prof-Start: 0
12345678: 0   wrong-pass-1: 0   Ana Pop: 0   Maria Pop: 0
statuses: 22×200, 14×302, 4×403, 2×429
audit rows containing DOB/password values: 0
django_admin_log change messages: field labels only, e.g. [{"changed": {"fields": ["Date of birth"]}}]
```

The server was stopped afterwards (`pkill -f "runserver 127.0.0.1:8767"`).

**Observation, not this story:** a lockout writes `auth.lockout` twice, once on the 5th failure and once on the locked attempt. That comes from Story 1.2/1.8's axes signal handling.

### Manual browser / screen-reader checks — NOT DONE

I couldn't run a browser in this environment, so the following were not done:
- the story's screenshots: admin user form in RO, the duplicate-link error, the audit-log list, and the Teacher 403 page;
- the integrator's check that the Django admin renders under the CSP (`script-src`/`style-src 'self'`) with no blocked resources;
- a screen-reader pass.

The same flows were exercised over HTTP with curl (above), and every page and status was asserted by the integration tests. A human or Story 1.10's Playwright E2E still needs to do the visual and CSP checks.

### Gate 1 — Spec Echo

| # | Requirement | Proof (code `file:line` + test) |
|---|-------------|---------------------------------|
| AC1 | `save()` sets `is_staff = is_superuser = role == ADMIN` on every save; demotion revokes access next request | `models.py:42-48`; `test_user_model.py:115,123,133,143,153`; `test_admin_access.py:94,104` |
| AC2 | `PlatformAdminSite(name="admin")`, translated header/title, `has_permission` = active + ADMIN, `login` 403 for signed-in non-Admin / redirect to `accounts:login` with `next`, URL in `i18n_patterns` | `admin.py:56-84,102`; `urls.py:19`; `test_admin_access.py:41,47,70,78,87,132,145,157` |
| AC3 | list / filters / search; add fields exactly `username, full_name, date_of_birth, role, preferred_language, password1, password2` with validators; change form + `is_active` + password link; `date_joined`/`last_login` read-only; groups / perms / staff flags excluded | `admin.py:136-176`, `admin_forms.py:53-71`; `test_user_admin.py:39,53,71,79,100,141` |
| AC4 | last-active-Admin guard (demote and deactivate); Student links guard; Parent links guard | `admin_forms.py:43-50,73-88`; `test_user_admin.py:244,256,266,276,287,301,311` |
| AC5 | `ParentChildLinkModel`: table name, FKs and related names, SET_NULL, `created_at`, both constraints | `models.py:58-97`; `test_parent_child_link.py:19,31,38,50,62` |
| AC6 | `LinkParent.validate` codes and order; `execute` re-validates in the UoW, maps IntegrityError → `LinkExists`, audits target + `{parent_id, student_id}` | `link_parent.py:52-99`; `repositories.py:39-47`; `test_link_parent.py:17,49,61,69,77,92,102,115`; `test_parent_links_repository.py:46` |
| AC7 | `UnlinkParent.execute` deletes + audits; missing → `False`, no audit | `link_parent.py:102-125`; `test_unlink_parent.py:15,35,46` |
| AC8 | link form querysets (PARENT active / STUDENT); `clean` maps violations to field/non-field errors; `save_model` → `LinkParent`; `delete_*` → `UnlinkParent`; change view read-only | `admin_forms.py:91-132`; `admin.py:216-260`; `test_parent_link_admin.py:28,71,92,105,115,148,168,181` |
| AC9 | `AuditAccountChange` actions; `{"fields": sorted names}`; called from `save_model` / `delete_model` / `delete_queryset` with `form.changed_data`; password view → `accounts.password_changed` | `manage_account.py:13-70`; `admin.py:185-212`; `test_manage_account.py:15-104`; `test_user_admin.py:110,182`; `test_user_admin_password_and_delete.py:21,62,82` |
| AC10 | `AccessAttemptAdmin` list columns; delete = unlock, audited `auth.lockout_cleared` | `admin.py:263-301`; `test_lockout_and_audit_admin.py:45,68,91,106,120` |
| AC11 | `AuditLogAdmin`: no add / change / delete; list columns; `action` filter; `actor_username` search; `created_at` date hierarchy | `admin.py:306-328`; `test_lockout_and_audit_admin.py:138,152,165,175,193` |
| AC12 | container factories with `DjangoAuditPort(SystemClock())` + `DjangoUnitOfWork()` | `container.py:23-48`; `test_parent_links_repository.py:69` |
| AC13 | `linked_parent`, `unlinked_parent` fixtures; `ParentChildLinkFactory` | `conftest.py:48-60`; `factories/accounts.py:43-50`; `test_parent_links_repository.py:94,99,104` |
| AC14 | `/ro/admin/`: anonymous 302, Student/Teacher/Parent 403, Admin 200 (in this story's admin module) | `test_admin_access.py:29-44` (+ every admin URL, `:47,70,83`) |
| AC15 | RO/EN for every new string: field labels, the **7** messages (owner decision 3), admin titles | `django.po` ×2; `test_admin_translations.py:64,69,74,78,90,101` |
| Step 1 | Tests first: unit → constraints → admin | each layer's tests were run red first (ModuleNotFoundError / ImportError / missing `admin.py`), then green |
| Step 2 | model changes + `makemigrations accounts` → `0002_parentchildlink` | `migrations/0002_parentchildlink.py` (generated; `--check` clean) |
| Step 3 | use cases; `AuditAccountChange` strips `password1/2`; password change is its own action | `manage_account.py:25,67-70`; `test_manage_account.py:49` |
| Step 4 | `DjangoParentLinks` appended to `repositories.py` | `repositories.py:29-56` |
| Step 5 | `admin.py`: site, 4 registrations, `get_form` sets `actor_id` from `request.user`, `save_model` sets `obj.pk`, links never changed | `admin.py:230-251`; `test_parent_link_admin.py:51,181`; `test_lockout_and_audit_admin.py:204` |
| Step 6 | URL inside `i18n_patterns` (alphabetical "admin" block) | `urls.py:17-19` |
| Step 7 | container, fixtures, factory, translations, all gates | rows AC12, AC13 and AC15; Quality gates above |
| Sys-resp | every system-response row: create 302 + message + audit; weak 200; role ADMIN 302 + 2 rows; last admin 200; link 302; repeat 200; race 200 / one row; wrong roles 200; linked role 200; unlink twice; delete with links; unlock; audit-row POST 403 | `test_user_admin.py:110,141,205,244,276`; `test_parent_link_admin.py:28,92,105,124,148`; `test_user_admin_password_and_delete.py:62`; `test_lockout_and_audit_admin.py:45,138` |
| QA-obs | staff flags only for ADMIN; one link row per pair; audit metadata names only; 302 after unlock; 403 on index, user list, link add, audit list | real-server SQL above; `test_admin_access.py:47`; `test_admin_privacy.py:43` |
| Ref: requirements matrix | only Admin holds `accounts:manage` / `parents:link`; the other 3 roles get 403 | `test_admin_access.py:41,47`; `ROLE_PERMISSIONS` untouched (Gate 2 #5) |
| Ref: requirements accounts | admin creates every account, links parents, stores name + DOB; hard delete cascades | `test_user_admin.py:110,174`; `test_parent_child_link.py:38`; `test_user_admin_password_and_delete.py:62,169` |
| Ref: NFR privacy / language | links enforced; RO/EN | AC8 and AC15 rows; `test_admin_privacy.py:43` |
| Ref: arch Roles & Authz | admin limited to the Admin role; account CRUD, password resets and links only (plus unlock and read-only audit) | `test_lockout_and_audit_admin.py:204` (exactly 4 models) |
| Ref: arch Data Model / Integrity | `PARENT_CHILD_LINK` columns; link roles in `LinkParent` + UNIQUE; deletion cascade; `actor_username` kept | `models.py:58-97`; `test_audit_log.py:246`; `test_user_admin_password_and_delete.py:62` |
| Ref: arch Security Design | validators min 8 / common / numeric; admins reset passwords; admins unlock; audit for create / update / delete / role / links; sensitive keys rejected | `test_user_admin.py:141`; `test_user_admin_password_and_delete.py:21`; `test_lockout_and_audit_admin.py:45`; `test_admin_privacy.py:43` |
| Ref: arch Error Handling | role-forbidden → 403 localized page; anonymous → 302 login with `next` | `test_admin_access.py:47,70` (asserts `errors/403.html`, never `admin/login.html`) |
| Ref: patterns §5 / §6 / §8 / §9 / §12 / §13 | use case + UoW + Clock; constraints; IntegrityError mapping; code-keyed messages; no PII logged; fakes; `redirect_to_login`; no `csrf_exempt` | Patterns table above; Gate 2 |
| Ref: Story 1.3 AC9 | `admin` namespace exempt only because the site enforces ADMIN on **every** admin URL | `admin.py:66-77` wraps every `admin_view`; `test_url_protection.py` green; `test_admin_access.py:47` (incl. catch-all `/no-such-page/`) |
| Ref: Story 1.8 | `AuditPort` inside the use case's UoW; append-only (savepoint tests, triggers kept); fingerprint rule for typed usernames | `test_manage_account.py:104`; Migrations section; `test_lockout_and_audit_admin.py:68` |
| Owner 1–4 | see the "Owner decisions" table | the tests cited there |

AC rows: 15 of 15.

### Gate 2 — Negative-Space Check (commands rerunnable from the worktree)

```
1 unsafe html/csrf_exempt/TODO/print in changed src:  0
2 external URLs in changed src:                        0
3 admin templates/static/css/html added:               0   (no custom admin styling — OUT)
4 settings/INSTALLED_APPS changed:                     0   (git diff --stat src/config/settings)
5 domain (ROLE_PERMISSIONS) changed:                   0   (git diff --stat src/domain)
6 base layout / menu changed:                          0   (no menu link — Story 1.7, OUT)
7 default admin.site routed:                           0   (grep -cF 'admin.site.urls' src/config/urls.py)
8 django imports in application:                       0
9 datetime.now/timezone.now in application:            0
10 non-admin routes: ['accounts:login', 'accounts:logout', 'healthz', 'set_language']  (no bulk import / self-service reset / email)
   platform site models: ['accounts.ParentChildLinkModel', 'accounts.UserModel', 'audit.AuditLogModel', 'axes.AccessAttempt']
   moderation fields on registered models: []   (moderation fields — OUT)
11 audit metadata keys in new use cases: parent_id, student_id, fields  (none is sensitive; is_sensitive_key sweep in test_admin_privacy.py:43)
logger calls in new admin code: 0
```

Further "must not" checks proven by tests:
- **No values in audit:** `test_admin_privacy.py:43`, which also checks log lines.
- **Audit rows never changed:** `test_lockout_and_audit_admin.py:138,165`.
- **Forged POST identity ignored:** `test_parent_link_admin.py:51`, `test_user_admin.py:159`.
- **No second login form:** `test_admin_access.py:47`.

### Gate 3 — Contract Consistency

| Producer | Consumer | Match |
|----------|----------|-------|
| `LinkParent.validate` codes `parent_not_parent_role`, `student_not_student_role`, `self_link`, `link_exists` | `ERROR_MESSAGES` (4 keys, `errors.py:26-31`) → `ParentChildLinkForm` (`FIELD_OF_VIOLATION`: 2 field errors, 2 non-field) → RO/EN catalogues | every code has a message in both languages (`test_parent_link_admin.py:215`); an unknown code can't reach `ERROR_MESSAGES[...]` because codes are fixed in `validate` |
| `ParentLinkPort` (4 methods) | `DjangoParentLinks`, `FakeParentLinks` | same names and signatures; `add` raises `LinkExists` in both |
| `AuditPort.record(metadata: Mapping[str, MetadataValue])` | `DjangoAuditPort.record` (same type), `FakeAuditPort` | list values stored as JSON (`test_audit_log.py:216`) |
| `ACCOUNT_ACTIONS` (6) | admin callers: `accounts.created/updated/role_changed` (`save_model`), `accounts.deleted` (`delete_*`), `accounts.password_changed` (2 password views), `auth.lockout_cleared` (`AccessAttemptAdmin`) | all 6 used; anything else → `ValueError` before any write (`test_manage_account.py:94`) |
| `UserCreationForm` fields | `add_fieldsets` | identical 7 names (`test_user_admin.py:39`) |
| `UserChangeForm.Meta.fields` | `fieldsets` (+ read-only dates) | identical (`test_user_admin.py:53`) |
| Container factories | use-case constructors | `test_parent_links_repository.py:69` checks the adapter types |
| `linked_parent` / `unlinked_parent` (conftest) | patterns §12.3 role-fixture list | names as specified; `parent` stays unlinked |

There is no silent default: a link form can't save without `LinkParent.execute` (`save_model` never calls `obj.save()`), and the user admin can't save without an audit row.

## Challenges Encountered

| Challenge | Resolution | Time Spent |
|-----------|------------|------------|
| Django's `AdminSite.admin_view` redirects to its own login URL before `login()` runs, so the story's "403, never a second login form" needs `admin_view` itself overridden | the platform guard wraps Django's wrapper (`admin.py:66-77`); `login()` still handles the direct `/admin/login/` URL | 0.3 h |
| `ModelForm.full_clean` also validates `Meta.constraints` with Django's generic "already exists" text (duplicate messages; the race test saw the generic one) | link fields excluded from model-level validation (`_get_validation_exclusions`), so `LinkParent` is the single source of rule text | 0.3 h |
| Race path must show a form error (200), not a 409 | `add_view` catches `LinkExists` after the admin transaction rolled back, then re-renders the form with `lost_race` set | 0.2 h |
| Deleting yourself would leave an audit row pointing at a deleted actor | audit **before** delete; `actor_username` is filled from the actor, so the row survives SET_NULL | 0.1 h |
| Django's password views can redirect without saving ("Conflicting form data") | audit only when the stored hash actually changed, inside one `atomic()` | 0.1 h |
| `ModelAdmin` / `UserCreationForm` aren't subscriptable at runtime, but django-stubs wants type args | `TYPE_CHECKING` aliases for the generic bases | 0.1 h |

## Deviations from Plan

1. **Out-of-list edits that the planner flagged, made with tests:**
   - `application/common/audit.py` and `persistence/audit/repositories.py`: list-valued metadata (`MetadataValue`).
   - `persistence/audit/repositories.py`: `actor_username` filled from `actor_id` when the caller passes none.
   - `web/common/errors.py`: the 4 link codes are registered (no format params).
2. **Out-of-list edits not in the plan:**
   - `persistence/audit/models.py` verbose names + generated `audit/0003_verbose_names` (SQL no-op, triggers kept) and `audit/apps.py` / `accounts/apps.py` translated app names. These are needed for a bilingual audit-log screen (AC15).
   - `tests/fakes/parent_links.py` (shared fake instead of importing between test modules).
   - `admin_forms.py`, created because admin + forms would exceed 400 lines (allowed by tasks.json).
3. **AC15 count:** **7** messages, not 6 (owner decision 3).
4. **AC2 `login()`:** a signed-in **Admin** opening `/admin/login/` is redirected to the admin index rather than given a 403. The 403 applies to non-Admins as specified.
5. **Audit metadata details:**
   - `auth.lockout_cleared` stores `{}` (owner decision 2: "no fields metadata").
   - `accounts.deleted` and `accounts.password_changed` store `{"fields": []}`.
   - `accounts.created` lists `form.changed_data`, so fields left at their default (e.g. `preferred_language="ro"`) aren't listed.
   - A save with no changes still writes one `accounts.updated` `{"fields": []}`, so every save writes exactly one row (two for a role change).
6. **Extra audits:** the Admin's **own** password change (`/admin/password_change/`) is audited as `accounts.password_changed`.
7. **Link form:** forged out-of-queryset ids get the rule text ("isn't a Parent/Guardian" / "isn't a Student") as the `invalid_choice` message. An inactive parent gets the parent message.
8. **AccessAttempt detail:** hides axes' captured GET/POST data, which may echo what was typed.
9. **Msgids:** use an ASCII hyphen ("parent-child link") because ruff RUF001 forbids the en dash in source.
10. **Test layout:**
    - `tests/integration/web/admin/__init__.py` was not created; the repo uses no test-package `__init__` files (importlib mode). Shared constants live in `admin_helpers.py`.
    - The user-admin tests are split across two files to respect the 400-line limit.
11. **Not built:** a data migration to re-derive staff flags for existing rows. Every save derives them, and the only pre-existing admins come from `createsuperuser` (flags already consistent).

## Lessons Learned

1. Django admin's permission redirect happens in `admin_view`, not `login()`. Overriding only `login()` still shows Django's sign-in page to non-admins.
2. `ModelForm` validates `Meta.constraints` itself (since Django 4.1). When a use case owns the rule text, exclude those fields from model validation, or every duplicate is reported twice.
3. Audit **before** a delete whose actor might be the deleted row; fill `actor_username` so history survives the FK going NULL.

## Next Steps

- [ ] Ready for code review
- [ ] Manual browser checks: RO/EN admin flows, the CSP rendering of Django admin assets, and the 4 screenshots (not done here)
- [ ] Parent / integrator: the pre-existing mypy error in `ui_molecules.py:72` (Story 1.6) still needs fixing
