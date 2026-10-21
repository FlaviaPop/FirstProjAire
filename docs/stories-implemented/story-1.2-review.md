# Story 1.2 Self-Review

**Date**: 2026-10-21
**Story**: Login & Session Security (CYCLE-1, wave 2, Dev 1)
**Developer**: DEV Agent (story-agent, in-one-go wave mode)
**Branch**: `worktree-agent-a44322bf323a435fc` (based on `feature/wave-2-dev-1` @ 179c213)

---

## What Was Implemented

- Argon2id as the first password hasher, with PBKDF2/PBKDF2-SHA1/Scrypt kept so older hashes upgrade on the next login. Validators: minimum length 8, common password, numeric-only.
- django-axes brute-force protection: 5 failures per username+IP give a 15-minute lockout with a localized 429 page. A successful login resets the counter. Attempts during the cool-off have no side effect.
- Session hardening: DB sessions, 8 h lifetime, `HttpOnly`, `SameSite=Lax` and an `HttpOnly` CSRF cookie (prod already had `Secure` from 1.0). The key rotates on every login, including a repeat login.
- Security headers: django-csp 4 policy (`default-src 'self'`, no inline code), `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy: same-origin`.
- `PlatformLoginView` (safe `next` or `/<preferred_language>/`) and a POST-only `PlatformLogoutView`. Both are under `accounts:` in `i18n_patterns` and listed in `PUBLIC_URL_NAMES`. `LOGIN_URL = "accounts:login"`.
- Login and lockout templates (class hooks for Story 1.6, Phosphor sprite references for Story 1.5).
- Role factories and the shared role and logged-in-client fixtures.
- RO and EN catalogue entries for every new msgid.

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `src/infrastructure/web/accounts/{__init__,forms,views,urls}.py` | New | Login form (generic error), login/logout views, URL names `accounts:login` / `accounts:logout` |
| `src/infrastructure/web/templates/accounts/login.html`, `locked_out.html` | New | Login form and 429 lockout page |
| `src/config/settings/base.py` | Modified (shared) | `CSPMiddleware` inserted after `SecurityMiddleware`; `AxesMiddleware` appended last; imports `timedelta`, `csp.constants`; appended "Story 1.2" block (hashers, validators, axes, sessions, headers, CSP, `LOGIN_URL`) |
| `src/config/urls.py` | Modified (shared) | `include` import; one line in `i18n_patterns` including `infrastructure.web.accounts.urls` |
| `src/infrastructure/web/common/decorators.py` | Modified (shared) | `PUBLIC_URL_NAMES` += `accounts:login`, `accounts:logout` |
| `src/infrastructure/i18n/locale/{ro,en}/LC_MESSAGES/django.po` | Modified (shared) | 6 msgids appended at the end |
| `tests/conftest.py` | Modified (shared) | Appended role fixtures and `*_client` fixtures |
| `tests/factories/accounts.py` | Modified | Appended `StudentFactory`, `TeacherFactory`, `ParentFactory`, `AdminFactory` |
| `tests/integration/web/test_role_access_matrix.py` | Modified (shared) | GET loop excludes `POST_ONLY_PUBLIC_URL_NAMES`; new POST row for `accounts:logout` |
| `pyproject.toml` | Modified (shared) | Appended a `[[tool.mypy.overrides]]` for `axes.*` (no stubs). `uv.lock` unchanged |
| `README.md` | Modified (shared) | `AXES_PROXY_COUNT` row in the Configuration table; lockout row in Troubleshooting |
| `tests/integration/web/accounts/conftest.py` | New | Seam: enables `LocaleMiddleware` for these tests until Story 1.4 merges (no-op afterwards) |
| `tests/integration/web/accounts/test_login.py` | New | 27 tests: login, next, generic errors, required fields, CSRF |
| `tests/integration/web/accounts/test_lockout.py` | New | 14 tests: axes thresholds, cool-off, per username+IP, signal, logs |
| `tests/integration/web/accounts/test_logout.py` | New | 7 tests |
| `tests/integration/web/accounts/test_security_settings.py` | New | 18 tests: settings, headers, cookies, expiry |
| `tests/integration/web/accounts/test_password_hashing.py` | New | 6 tests: Argon2id, upgrade, validators |
| `tests/integration/web/accounts/test_templates.py` | New | 8 tests: AC 13 |
| `tests/integration/web/accounts/test_translations.py` | New | 12 tests: AC 15 |
| `tests/integration/web/accounts/test_role_fixtures.py` | New | 10 tests: AC 14 |

## Patterns Applied

| Pattern | Where Applied | Notes |
|---------|---------------|-------|
| Thin views §7.1 | `views.py` | Django `LoginView`/`LogoutView` subclasses; no business logic, and no use case is needed because there are no writes beyond Django auth |
| Public-route registry §7.2 | `decorators.py:8` | Both routes listed; the matrix test was extended |
| Fixed policy constants §10 | `base.py:93-149` | Only `AXES_PROXY_COUNT` is read from the environment, via `env_str` |
| Security rules §13 | `views.py:22-31`, templates | `url_has_allowed_host_and_scheme`; `{% csrf_token %}`; no `csrf_exempt`, `|safe` or inline code |
| Logging §9 | axes defaults | `AXES_SENSITIVE_PARAMETERS` masks username and IP; passwords are never logged (`test_axes_logs_never_contain_password_or_username`) |
| i18n §11.3 | templates, `forms.py` | `{% translate %}` / `gettext_lazy`; English msgids |
| Testing §12.3 | `tests/conftest.py`, factories | Role fixtures as specified; AAA; file-based test DB |

## Testing Summary

- **Unit tests**: 0 new (no domain/application code in this story). The existing 7 still pass.
- **Integration tests**: 102 in `tests/integration/web/accounts/` plus 1 new matrix row, all passing
- **Total**: 134 passed, 0 failed
- **Coverage**: 100.00% overall, branch coverage included (target 85%). `src/domain` and `src/application` were not changed.

**Test output** (`uv run pytest --cov=src --cov-branch --cov-fail-under=85`, verbatim tail):
```
tests/integration/web/accounts/test_role_fixtures.py ..........          [ 53%]
tests/integration/web/accounts/test_security_settings.py ............... [ 64%]
...                                                                      [ 67%]
tests/integration/web/accounts/test_templates.py ........                [ 73%]
tests/integration/web/test_healthz.py .........                          [ 79%]
tests/integration/web/test_role_access_matrix.py ...                     [ 82%]
tests/integration/persistence/accounts/test_restart_persistence.py ..... [ 85%]
                                                                         [ 85%]
tests/integration/web/accounts/test_translations.py ............         [ 94%]
tests/unit/config/test_env.py .......                                    [100%]

================================ tests coverage ================================
src/infrastructure/web/accounts/forms.py                  4      0      0      0   100%
src/infrastructure/web/accounts/urls.py                   4      0      0      0   100%
src/infrastructure/web/accounts/views.py                 20      0      4      0   100%
src/infrastructure/web/common/decorators.py               1      0      0      0   100%
---------------------------------------------------------------------------------------
TOTAL                                                    97      0      8      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
============================= 134 passed in 1.93s ==============================
```

TDD record: the tests were written first. The first run gave `72 failed, 25 passed, 2 errors` and an axes collection error (`Model class axes.models.AccessFailureLog ... isn't in an application in INSTALLED_APPS`). After the implementation, two failures remained:
- **Repeat login did not rotate the key.** Django's `login()` skips `cycle_key()` when the same user is already signed in. Fixed in `views.py:16-20`.
- **Test bug.** The lockout test assumed the first rendered template was the lockout page. It isn't, because AxesMiddleware replaces the view's response.

A later test, `test_attempts_during_cool_off_have_no_side_effect`, failed red before `AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT=False` was added.

## DoD Evidence

### Quality gates (run 2026-10-21, verbatim)

```
$ uv run ruff format --check .
48 files already formatted
$ uv run ruff check .
All checks passed!
$ uv run mypy
Success: no issues found in 42 source files
$ PYTHONPATH=src uv run lint-imports
Layers point inward KEPT
Domain is framework-free KEPT

Contracts: 2 kept, 0 broken.
$ uv run python manage.py makemigrations --check --dry-run
AXES: BEGIN version 8.3.1, blocking by combination of username and ip_address
No changes detected
$ uv run pytest --cov=src --cov-branch --cov-fail-under=85
134 passed — Total coverage: 100.00%
```

### Manual checks: real `runserver` with real CSRF tokens (dev settings, fresh `data/db.sqlite3`)

`manage.py migrate` applied `axes.0001` through `axes.0010`. Users were created with `shell --no-imports`, and each stored password starts with `argon2$argon2id$` (ana STUDENT/en, dan TEACHER/ro, pat PARENT/ro). The curl script output, verbatim:

```
== 1. curl -I /ro/accounts/login/
HTTP/1.1 200 OK
X-Frame-Options: DENY
Content-Security-Policy: font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; img-src 'self' data:; script-src 'self'; default-src 'self'; style-src 'self'
X-Content-Type-Options: nosniff
Referrer-Policy: same-origin
Set-Cookie:  csrftoken=kdutHIHxCp2UhhUTu87XzknANtVw6gAZ; expires=Wed, 20 Oct 2027 09:37:57 GMT; HttpOnly; Max-Age=31449600; Path=/; SameSite=Lax
== 2. /en/accounts/login/ on this branch (LocaleMiddleware is Story 1.4)
404
== 3. login ana (preferred en), real CSRF
302 http://127.0.0.1:8792/en/
== 4. Set-Cookie flags on successful login
HTTP/1.1 302 Found
Location: /ro/
Content-Security-Policy: font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; img-src 'self' data:; script-src 'self'; default-src 'self'; style-src 'self'
Set-Cookie:  sessionid=svkmoouqp0xksd95e9iv6peaf12ud0nn; expires=Wed, 21 Oct 2026 17:37:57 GMT; HttpOnly; Max-Age=28800; Path=/; SameSite=Lax
== 5. unsafe next ignored
302 http://127.0.0.1:8792/ro/
== 6. POST login without CSRF token
403
== 7. GET logout
405
== 8. POST logout without CSRF token
403
== 9. POST logout with CSRF token
302 http://127.0.0.1:8792/ro/accounts/login/
== 10. five wrong passwords for pat, then the right one
200
200
200
200
429
429
== 11. lockout body + headers
<title>Too many attempts</title>
<h1 id="lockout-title">
Too many attempts
<div class="form-banner form-banner--error" role="alert">Too many failed attempts. Try again in 15 minutes or ask the administrator.</div>
HTTP/1.1 429 Too Many Requests
X-Frame-Options: DENY
Content-Security-Policy: frame-ancestors 'none'; default-src 'self'; font-src 'self'; img-src 'self' data:; form-action 'self'; script-src 'self'; base-uri 'self'; style-src 'self'
$ uv run python manage.py axes_list_attempts      # after 2 extra attempts during the lockout
127.0.0.1	pat	5
$ uv run python manage.py axes_reset_username pat
AXES: Reset 1 access attempts from database.
1 attempts removed.
```

### Gate 1 — Spec Echo

| # | Requirement | Proof |
|---|-------------|-------|
| AC1 | `PASSWORD_HASHERS` = Argon2, PBKDF2, PBKDF2SHA1, Scrypt; validators MinLength(8), Common, Numeric; test keeps MD5 and a test asserts the base value | `base.py:96-109`; `test_password_hashers_keep_fallbacks_for_upgrade`, `test_password_validators_are_min_length_8_common_and_numeric`, `test_argon2_is_the_primary_hasher_in_real_settings`; `test.py:9` unchanged |
| AC2 | `axes` installed with migrations applied; backends `[AxesStandaloneBackend, ModelBackend]`; `AxesMiddleware` last | `base.py:111-115`, `base.py:32`; `test_axes_backend_runs_before_the_model_backend`, `test_axes_middleware_is_last_and_csp_follows_security`; manual `migrate` shows `axes.0001…0010 OK` |
| AC3 | Axes settings (5, 15 min, `[["username","ip_address"]]`, reset on success, template, 429, proxy count from `AXES_PROXY_COUNT` default 0) | `base.py:116-125`; `test_axes_policy_constants`, `test_axes_proxy_count_comes_from_the_environment` |
| AC4 | DB sessions, 8 h, HttpOnly, Lax, CSRF HttpOnly; prod Secure cookies | `base.py:127-131`, `prod.py:16-17`; `test_session_policy`, `test_prod_keeps_secure_cookies`, `test_session_cookie_flags`; manual step 4 `Max-Age=28800; HttpOnly; SameSite=Lax` |
| AC5 | CSP string plus XFO DENY, nosniff, Referrer same-origin on every response | `base.py:134-149`, `base.py:25`; `test_security_headers_on_login_page[ro,en]`, `test_security_headers_on_redirects`, `test_lockout_page_has_the_security_headers`; manual steps 1, 4 and 11 (200, 302, 429) |
| AC6 | `accounts:login` GET/POST, `accounts:logout` POST-only (GET 405), both in `PUBLIC_URL_NAMES`, `LOGIN_URL` | `accounts/urls.py:5-9`, `config/urls.py:13`, `decorators.py:8`, `base.py:133`; `test_login_and_logout_are_public_routes`, `test_logout_requires_post_and_flushes_session`, `test_post_only_public_routes_accept_anonymous_post`; manual step 7 → 405 |
| AC7 | Key rotated; 302 to a safe `next`, otherwise `/<preferred_language>/` | `views.py:16-31`; `test_login_rotates_session_key`, `test_repeat_login_while_signed_in_rotates_the_key_again`, `test_valid_login_redirects_to_preferred_language_home[ro,en]`, `test_safe_next_is_honoured`, `test_safe_next_from_query_string_is_honoured`, `test_unsafe_next_is_ignored[4 cases]`; manual steps 3 and 5 |
| AC8 | Wrong password, unknown user and inactive user give 200 with exactly one identical error; password cleared, username kept | `forms.py:5-11`, `login.html:10-12`; `test_failures_share_one_generic_message[3]`, `test_failure_messages_are_byte_identical_across_cases`, `test_failed_login_keeps_username_and_clears_password` |
| AC9 | Missing fields give a field-level "This field is required." and no axes attempt | `login.html:18,22`; `test_missing_fields_show_field_level_required_error[3]`, `test_empty_fields_are_not_counted_as_attempts` |
| AC10 | 5th failure and any attempt during the cool-off give 429 with the localized template; success after the cool-off | `base.py:116-124`, `locked_out.html`; `test_fifth_failure_locks_even_correct_password`, `test_lockout_page_explains_the_cool_off` (EN, "15", one `<h1>`), `test_lockout_is_still_active_before_fifteen_minutes`, `test_correct_login_succeeds_after_the_cool_off`, `test_attempts_during_cool_off_have_no_side_effect`, `test_cool_off_counts_from_the_lockout_not_from_later_attempts`; manual step 10 |
| AC11 | 4 failures + success + 4 failures does not lock | `base.py:119`; `test_success_resets_failure_counter`, `test_four_failures_still_allow_the_right_password` |
| AC12 | POST logout deletes the session row and redirects to login in the current language; the next request is anonymous | `views.py:34-37`; `test_logout_requires_post_and_flushes_session`, `test_logout_redirects_to_login_in_the_current_language`, `test_next_request_after_logout_is_anonymous`, `test_logout_when_signed_out_is_harmless`; manual step 9 |
| AC13 | Templates extend base, `{% translate %}` everywhere, one `<h1>`, `<label for>`, autocomplete, no inline style/script | `templates/accounts/login.html`, `locked_out.html`; `test_templates.py` (8 tests incl. "no untranslated text" and the regex for `<style`/`<script`/`style=`/`on*=`) |
| AC14 | Fixtures `student`, `other_student`, `teacher`, `parent`, `admin_user` and four `*_client` via `force_login`; 4 factories | `tests/conftest.py:8-68`, `tests/factories/accounts.py:21-42`; `test_role_fixtures.py` (10 tests) |
| AC15 | RO + EN translations for every new msgid | both `django.po` (Story 1.2 block); `test_translations.py` (12 tests) |
| Step 1 | Tests first, covering every System-responses row | Red run recorded under Testing Summary; table coverage in Gate 3 |
| Step 2 | Hashers and validators | AC1 |
| Step 3 | Axes, sessions, headers, middleware positions, README `AXES_PROXY_COUNT` | AC2–AC5; `README.md` Configuration table |
| Step 4 | Form, views, urls, URLconf include, `PUBLIC_URL_NAMES` | AC6–AC8 |
| Step 5 | Templates with class hooks `login-card`, `form-banner`, `form-banner--error`, `field-error`; lockout `<h1>` and sentence | `login.html`, `locked_out.html`; `test_login_page_markup_is_accessible` |
| Step 6 | Factories and fixtures appended | AC14 |
| Step 7 | RO msgstrs as specified ("Autentificare", "Nume de utilizator", "Parolă", "Nume de utilizator sau parolă incorecte.") plus two lockout strings | `ro/django.po`; `test_romanian_translation_exists[6]` |
| Step 8 | migrate + all gates | Quality gates and manual output above |
| Design tokens / icons | `sign-in` 32px duotone beside the title, `lock-simple` on the lockout page, `aria-hidden` | `login.html:7`, `locked_out.html:7`; `test_login_page_markup_is_accessible`, `test_lockout_template_uses_the_lock_icon`. Colours, spacing and radius are applied by Story 1.6's CSS on these hooks (the story says the template stays unchanged) |
| Error display (UI/UX `inline+top_banner`) | Banner with `role="alert"` and inline `field-error` plus `aria-invalid`/`aria-describedby` | `login.html:10-22`; `test_failures_share_one_generic_message` (role=alert), `test_missing_fields_show_field_level_required_error` (aria-invalid) |
| Ref: architecture Security Design | Argon2id; validators; axes 5 per username+IP / 15 min; DB sessions, Secure/HttpOnly/Lax, 8 h, rotate, POST logout; CSP; headers | rows AC1–AC7, AC12 |
| Ref: architecture "lockouts written to the audit log" | Out of scope here (Story 1.8). `user_locked_out` is emitted for 1.8 to consume | `test_lockout_sends_the_user_locked_out_signal` |
| Ref: patterns §9 never-log | No password, token or username in logs | `test_axes_logs_never_contain_password_or_username`; new web code has no logger (Gate 2) |
| Ref: patterns §10 | Policy as constants, env only through `env_str` | `base.py:93-125`; Gate 2 `os.environ` grep |
| Ref: patterns §13 | `url_has_allowed_host_and_scheme`; no `csrf_exempt` | `views.py:24`; Gate 2 |
| Ref: patterns §17 | Role-access matrix extended | `test_role_access_matrix.py` POST-only row |
| QA: "What does NOT change" | Only `last_login` changes; failures create no session | `test_login_updates_only_last_login`, `test_failed_login_creates_no_session`, `test_fifth_failure_locks_even_correct_password` (0 sessions) |
| QA: hash upgrade | PBKDF2 becomes Argon2id on login | `test_pbkdf2_hash_is_upgraded_to_argon2id_on_login` |
| QA: 8 h expiry | Expired session is anonymous; expiry ≈ login + 8 h | `test_expired_session_is_anonymous`, `test_login_session_expires_eight_hours_after_sign_in`, `test_session_is_still_valid_before_expiry` |

AC rows: 15 of 15. Step rows: 8 of 8.

### Gate 2 — Negative-Space Check

| Rule | Check | Result |
|------|-------|--------|
| No `csrf_exempt`, `|safe`, `mark_safe`, TODO/FIXME, `print(` | `grep -rnE "csrf_exempt\|\|safe\|mark_safe\|TODO\|FIXME\|print\(" src tests/integration/web/accounts` | only the two assertion lines in `test_templates.py` that check for their absence |
| No inline style/script/handlers (CSP) | `grep -rnE "<style\|<script\|\sstyle=\|\son[a-z]+=" src/infrastructure/web/templates/accounts` | none |
| Env read only in `env.py` | `grep -rn "os\.environ" src` minus env.py/wsgi | none |
| Logout never via GET | `test_logout_requires_post_and_flushes_session`, `test_get_logout_keeps_the_session`; manual 405 | ✓ |
| No account enumeration | identical messages test (3 cases) | ✓ |
| No open redirect | 4 unsafe `next` variants + manual `https://evil.example/` | ✓ → `/ro/` |
| Failed attempts never create sessions | `test_failed_login_creates_no_session`, lockout test `Session.objects.count() == 0` | ✓ |
| Story 1.4 scope not built (LocaleMiddleware, setlang) | `grep -rn "LocaleMiddleware\|set_language" src` | none (test-only seam) |
| Story 1.3/1.8 scope not built | `grep -rniE "require_permission\(\|AuditPort\|audit" src --include='*.py'` | none |
| No registration, password reset or email | `grep -rniE "signup\|register\|password_reset\|PasswordReset\|EMAIL_" src` | only the pre-existing `template.Library()` register / `INSTALLED_APPS` comment |
| No CDN / external URLs in templates | `grep -rnE "https?://" src/infrastructure/web/templates` | none |
| `uv.lock`, `docs/status.md`, `docs/plans/**` untouched | `git status --porcelain \| grep -E "uv.lock\|docs/status.md\|docs/plans/"` | none |
| No new dependency | `uv lock --check` → `Resolved 48 packages` | unchanged |

### Gate 3 — Contract Consistency

| Story System-responses row | Implementation / proof | Consistent? |
|---|---|---|
| GET `/ro/accounts/login/` → 200 form | `test_login_page_is_public_in_both_languages` | ✓ |
| Valid, `preferred_language=en`, no next → `302 /en/`; key rotated; failures reset; `last_login` | `test_valid_login_redirects…[en]`, `test_login_rotates_session_key`, `test_success_resets_failure_counter`, `test_login_updates_only_last_login` | ✓ |
| Valid + `next=/ro/catalogue/` → that URL | `test_safe_next_is_honoured` | ✓ |
| Unsafe `next` → home | `test_unsafe_next_is_ignored` | ✓ |
| Repeat login → same target, key rotated again | `test_repeat_login_while_signed_in_rotates_the_key_again` (needed the explicit `cycle_key`; Django alone doesn't rotate) | ✓ |
| Wrong password / unknown / inactive → 200 + message; axes +1 | `test_failures_share_one_generic_message`, `test_each_failure_is_recorded_for_username_and_ip` | ✓ |
| Empty fields → 200 field error; no attempt | `test_missing_fields…`, `test_empty_fields_are_not_counted_as_attempts` | ✓ |
| 5th failure → 429; `user_locked_out` signal | `test_fifth_failure…`, `test_lockout_sends_the_user_locked_out_signal` | ✓ |
| Any POST during cool-off → 429, side-effect none | `test_attempts_during_cool_off_have_no_side_effect`: required `AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT=False`. The axes default would silently extend the lockout | ✓ (fixed) |
| Correct after 15 min → 302, failures reset | `test_correct_login_succeeds_after_the_cool_off` | ✓ |
| Different IP during lockout → independent | `test_lockout_is_per_username_and_ip` | ✓ |
| POST logout signed in → `302 /ro/accounts/login/`, row deleted | `test_logout_requires_post_and_flushes_session` | ✓ |
| POST logout signed out → 302 login | `test_logout_when_signed_out_is_harmless` | ✓ |
| GET logout → 405 | test + manual | ✓ |
| POST without CSRF → 403 | `test_post_without_csrf_is_rejected`, `test_logout_without_csrf_is_rejected` (strict client), manual steps 6 and 8 | ✓ (Django's default 403 view until 1.1's handler is merged) |
| `PUBLIC_URL_NAMES` ↔ URL names | `decorators.py:8` ↔ `urls.py` names; matrix test reverses them | ✓ |
| Lockout template text "15 minutes" ↔ `AXES_COOLOFF_TIME` | both 15; `test_axes_policy_constants` + `test_lockout_page_explains_the_cool_off` | ✓ (literal msgid per Step 7; change both together) |
| Route catalogue (architecture) ↔ code | login GET/POST and logout POST rows already exist; logout's "authenticated" column vs `PUBLIC_URL_NAMES`: a signed-out POST is a harmless redirect, as the story specifies | ✓ catalogue not edited |
| README env table ↔ `env_str` calls | `AXES_PROXY_COUNT` row added | ✓ (`.env.example` left for the next story that touches it, per Step 3) |

## Challenges Encountered

| Challenge | Resolution | Time Spent |
|-----------|------------|------------|
| Worktree was created from `main` (899c001), not `feature/wave-2-dev-1` | `git reset --hard 179c213` on my own (clean) branch before any work | 2 min |
| `/en/` URLs don't resolve without `LocaleMiddleware`, which belongs to Story 1.4 | Test-only autouse fixture inserts it at 1.4's fixed position; it becomes a no-op once 1.4 is merged. Settings left to 1.4 | 10 min |
| Django `login()` doesn't rotate the key for a repeat login by the same user | `form_valid` calls `cycle_key()` when already authenticated | 5 min |
| Axes default extends the lockout on attempts made during it | `AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = False` (story table: side-effect none) | 5 min |
| `axes` has no type stubs and django-stubs imports its models | mypy override for `axes.*` appended to `pyproject.toml` | 2 min |
| Seeded matrix test GETs every public name | `POST_ONLY_PUBLIC_URL_NAMES` exclusion + POST row | 3 min |

## Deviations from Plan

- **`AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = False` added**. This isn't in the Step 3 snippet, but the System-responses table requires "side-effect: none" during the cool-off.
- **`form_valid` override** in `PlatformLoginView` to honour "session key rotated again" on a repeat login.
- **Shared files outside "Files Touched"**: `tests/integration/web/test_role_access_matrix.py` (it would otherwise fail on POST-only logout), `pyproject.toml` (mypy override block) and `README.md` (requested by Step 3).
- **Known environment limitations**:
  - GNU gettext isn't installed, so the `.po` entries were written by hand and not compiled. Tests assert English text and check catalogues as text; no test depends on `.mo` files.
  - No Playwright browser is installed, so the story's screenshots weren't produced. Rendered HTML and header dumps are recorded above instead.
  - `/en/…` returns 404 on this branch alone until Story 1.4's `LocaleMiddleware` is merged.
- **`AXES_IPWARE_PROXY_COUNT`** is set as specified but only takes effect if `python-ipware` is installed (axes 8.3.1 otherwise uses `REMOTE_ADDR`). No dependency was added (`uv.lock` frozen). DevOps should add `django-axes[ipware]` when deploying behind a proxy. This is recorded in the README.
- The lockout page reuses the `login-card` and `form-banner--error` hooks, so Story 1.6 styles it with no template change.

## Lessons Learned

1. Third-party security defaults (axes' cool-off reset) can silently contradict a contract table. Write a test for every "side-effect: none" row.
2. Django's `login()` rotates the session only when the session isn't already authenticated. "Rotate on every login" needs an explicit `cycle_key()`.
3. i18n URL prefixes need `LocaleMiddleware` to resolve non-default languages. Parallel stories should plan for that seam explicitly.

## Next Steps

- [ ] Merge with 1.1 (keep `DomainErrorMiddleware` before `AxesMiddleware`), 1.4 (`LocaleMiddleware` after `SessionMiddleware`; the test seam then becomes a no-op) and 1.5 (sprite symbols `sign-in-duotone`, `lock-simple-duotone`)
- [ ] Ready for code review
- [ ] Ready for QA validation
