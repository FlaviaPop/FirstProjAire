# Code Review - Story 1.2: Login & Session Security

> ## 🛠️ Remediation Status: ✅ Resolved
> - **Remediated**: 2026-10-23 by DEV Agent (deferred item; earlier passes on 2026-10-22)
> - **Fixed**: 5 issue(s) — 🔴 0 / 🟠 0 / 🟡 1 / 🟢 4 (ISS-005 in this pass: mitigated at the reverse proxy)
> - **Deferred (with user consent)**: 0
> - **Tests**: 1532/1532 passing (+17 e2e) | **Coverage**: 100% | **Linter**: clean
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
**Code reviewed at**: `feature/story-1.4-i18n` @ `42aaf37`. Story 1.2's commit `274351e` merged in `aa940e9`, plus later integration changes in shared files: CSRF failure view (BUG-003), `AXES_VERBOSE`, `LocaleMiddleware` (1.4).

---

## Review Summary

**Components Reviewed**:
- `src/infrastructure/web/accounts/{views,forms,urls}.py`
- `templates/accounts/{login,locked_out}.html`
- Story 1.2 block in `src/config/settings/base.py`
- `PUBLIC_URL_NAMES`
- `tests/conftest.py` role fixtures, `tests/factories/accounts.py`
- `tests/integration/web/accounts/*` (8 files, 102 tests)
- `docs/stories-implemented/story-1.2-review.md`

**Lines of Code**: ~60 production Python + 2 templates + ~60 settings lines; ~900 test lines
**Tests Reviewed**: Yes (102 in the story's files, all passing)
**Coverage**: 100% for `web/accounts/*` (statements + branches), re-run by the reviewer

**Overall Assessment**: A careful, well-tested security story:
- Argon2 first, with upgrade-on-login fallbacks.
- Axes lockout per username+IP, configured so cool-off attempts don't extend the lockout.
- A single generic error for wrong password, unknown user and inactive account.
- The session key is rotated even on a repeat sign-in.
- Safe-`next` handling, a strict CSP, and headers on every response.

Open-redirect, XSS-reflection and enumeration probes all behaved correctly. No blockers or high issues. The comments cover reusing Story 1.5's UI primitives (now merged), a hard-coded cool-off duration, a dropped `maxlength`, a small redundancy, and a design-level note on password spraying.

### Evidence verification (re-run by reviewer)

```
$ uv run pytest -q tests/integration/web/accounts          → 102 passed in 0.67s
$ uv run pytest -q --cov=src --cov-branch                  → 659 passed
src/infrastructure/web/accounts/forms.py          4      0      0      0   100%
src/infrastructure/web/accounts/urls.py           4      0      0      0   100%
src/infrastructure/web/accounts/views.py         20      0      4      0   100%
$ uv run ruff check src/infrastructure/web/accounts          → All checks passed!
$ uv run mypy                                                → Success: no issues found in 91 source files

Probes (reviewer script, config.settings.test, real views):
next 'https://evil.example/'    -> 302 /ro/
next '//evil.example/'          -> 302 /ro/
next 'javascript:alert(1)'      -> 302 /ro/
next '/en/accounts/login/'      -> 302 /en/accounts/login/
hidden next rendered: ['/ro/&quot;&gt;&lt;script&gt;x&lt;/script&gt;']   (escaped)
maxlength on username input: False
AXES_COOLOFF_TIME: 0:15:00
unknown user 2 ms vs wrong password 2 ms   (same code path; ModelBackend hashes for unknown users)
accounts templates use no ui primitives
```
Real-server behaviour (sign-in, sign-out, lockout 429, CSRF 403) was also exercised during the Story 1.8 and 1.4 manual checks and the 2026-10-21 regression run.

---

## Checklist Results

### Correctness
- [x] ✅ AC 1–15 covered by tests (hashers, validators, axes config and behaviour, sessions, headers, routes, safe `next`, generic errors, lockout/cool-off/reset, logout flush, templates, fixtures, translations)
- [x] ✅ Repeat sign-in rotates the session key (Django's `login()` doesn't for the same user; the `form_valid` override does)
- [x] ✅ Cool-off attempts don't restart the 15 minutes (`AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = False`, tested)
- [x] ⚠️ The lockout text hard-codes "15 minutes" while the duration lives in `AXES_COOLOFF_TIME` (ISS-002)

### Pattern Adherence
- [x] ✅ Thin views (§7.1); policy values as constants in `base.py` (§10); only the proxy count from env
- [x] ⚠️ UI primitives (§11.2): templates hand-write the icon `<svg>` and button classes instead of Story 1.5's `{% ui_icon %}` / `{% ui_button %}` (ISS-001)
- [x] ✅ Naming, file sizes, function sizes

### Testing
- [x] ✅ 102 meaningful tests (strict-CSRF clients, lockout timing via aged attempts, session-row assertions, header checks on the 429 page)
- [x] ✅ Coverage 100%
- [x] ✅ No `Client.login()` (correctly avoided with axes); `force_login` with an explicit backend

### Documentation
- [x] ✅ Docstrings name route and access; comments explain *why* (axes default, key rotation)
- [x] ✅ README: `AXES_PROXY_COUNT` and a lockout troubleshooting row
- [x] ✅ No TODO/FIXME

### Security
- [x] ✅ Argon2id first; validators min 8 / common / numeric
- [x] ✅ Generic "Incorrect username or password." for all three failure kinds; timing path identical
- [x] ✅ Open-redirect safe (`url_has_allowed_host_and_scheme`, probes above); `next` reflection escaped
- [x] ✅ Session: DB backend, 8 h, HttpOnly, SameSite=Lax; Secure in prod; CSRF cookie HttpOnly
- [x] ✅ CSP `default-src 'self'` … `frame-ancestors 'none'`, `X-Frame-Options: DENY`, `nosniff`, `same-origin`
- [x] ✅ No `csrf_exempt`; logout is POST-only
- [x] ⚠️ Lockout keyed on username+IP doesn't slow password spraying across many usernames from one IP (ISS-005, design-level)

### Performance
- [x] ✅ Argon2 cost is per login only; axes adds one indexed lookup per attempt

### SOLID / Anti-Monolith
- [x] ✅ Extends Django's `LoginView`/`LogoutView`/`AuthenticationForm` with small overrides; no duplication of auth logic
- [x] ✅ No global state

---

## Issues Found

### ISS-001: Templates bypass the shared UI primitives from Story 1.5 🟡 Medium

**Category**: Pattern
**File**: `src/infrastructure/web/templates/accounts/login.html:6-8,24`; `accounts/locked_out.html:6-8`
**Pattern Reference**: patterns §11.2 UI Primitive Catalogue ("Shared primitives reused"); §17 checklist

**Issue**:
Both templates inline the icon markup (`<svg class="icon icon--32" … <use href="…#sign-in-duotone">`) and hand-assemble the button (`class="button button--primary"`). Stories 1.2 and 1.5 were built in parallel, so the primitives didn't exist on 1.2's branch. Now that both are merged, the duplicated markup drifts from the primitives:
- `{% ui_icon %}` validates icon names and sizes and sets `focusable`/`aria-hidden` consistently.
- `{% ui_button %}` owns variants, the disabled/loading states and the touch-target CSS.

**Current Code**:
```django
<svg class="icon icon--32" width="32" height="32" focusable="false" aria-hidden="true"><use href="{% static 'icons/sprite.svg' %}#sign-in-duotone"></use></svg>
…
<button type="submit" class="button button--primary">{% translate "Sign in" %}</button>
```

**Suggested Fix**:
```django
{% load i18n ui %}
{% ui_icon "sign-in" size=32 variant="duotone" %}
…
{% translate "Sign in" as sign_in %}{% ui_button sign_in type="submit" variant="primary" %}
```
(Use the exact `ui_button` signature from `templatetags/ui.py`; the existing template tests assert the rendered attributes, so they'll catch any difference.)

**Why This Matters**: The primitive catalogue is the single place for accessibility and styling rules. Copies don't receive later fixes, such as Story 1.6's focus or loading changes.


**Resolution** (2026-10-22, DEV):
- Fix: both templates use `{% ui_icon "sign-in"/"lock-simple" size=32 variant="duotone" %}`; the submit button is `{% translate "Sign in" as sign_in %}{% ui_button sign_in type="submit" variant="primary" %}`; no raw `<svg>` or `<button>` left in either template
- Commit / change ref: `templates/accounts/login.html:2,7,26`; `templates/accounts/locked_out.html:2,7`
- Test evidence: `tests/integration/web/accounts/test_templates_review_v1.py` (source uses primitives, no raw markup; rendered `button button--primary` with `button__label`; rendered `icon icon--32` with `aria-hidden`) — failed before the fix; all 102 original Story 1.2 tests still pass. `test_lockout_template_uses_the_lock_icon` was updated to assert the primitive call instead of raw markup
- Status: ✅ Resolved

---

### ISS-002: Lockout message hard-codes the cool-off duration 🟢 Low

**Category**: Maintainability
**File**: `src/infrastructure/web/templates/accounts/locked_out.html:10`; `base.py` `AXES_COOLOFF_TIME`

**Issue**: "Try again in 15 minutes" is a translated literal, while the duration is the setting `AXES_COOLOFF_TIME = timedelta(minutes=15)`. Changing the policy would leave the message wrong in both languages.

**Suggested Fix**: Pass `cooloff_minutes` to the template (axes' `AXES_LOCKOUT_TEMPLATE` context includes `cooloff_time`; or compute `int(settings.AXES_COOLOFF_TIME.total_seconds() // 60)`) and use `{% blocktranslate count minutes=cooloff_minutes %}…{{ minutes }} minute…{% plural %}…{{ minutes }} minutes…{% endblocktranslate %}`. Update the `.po` entries with `makemessages --no-wrap`.


**Resolution** (2026-10-22, DEV):
- Fix: the lockout sentence is a `{% blocktranslate trimmed count minutes=cooloff_timedelta|minutes %}` plural message. `cooloff_timedelta` comes from axes' lockout context and therefore from `AXES_COOLOFF_TIME`; the new `durations.minutes` filter converts it. Catalogues gained `Plural-Forms` headers (RO: 3 forms *minut / minute / de minute*; EN: 2), and the fuzzy auto-match left by `makemessages` was replaced by real translations
- Commit / change ref: `templates/accounts/locked_out.html:2,10`; `src/infrastructure/web/templatetags/durations.py`; both `django.po` (header + plural entry)
- Test evidence: `test_lockout_message_uses_the_configured_cool_off[15|30|1 × en|ro]` (6 cases; the 30/1-minute and RO cases failed before the fix); `tests/unit/infrastructure/test_durations.py` (6); `test_translations.py::test_lockout_message_has_three_romanian_plural_forms`, `…_two_english_plural_forms`; real server RO "peste 15 minute", EN "in 15 minutes"
- Status: ✅ Resolved

---

### ISS-003: Hand-written username input drops `maxlength` 🟢 Low

**Category**: Correctness (input validation hint)
**File**: `src/infrastructure/web/templates/accounts/login.html:16-18`

**Issue**: The form field has `max_length=150` (Django's `AuthenticationForm`), which Django renders as `maxlength="150"`. The hand-written `<input>` omits it (probe: `maxlength on username input: False`). Server-side validation still applies, so this is only a missing client-side hint and a small parity gap with Django's widget.

**Suggested Fix**: Add `maxlength="{{ form.username.field.max_length }}"`, or render the field's widget attributes once Story 1.6's `form_field` primitive exists.


**Resolution** (2026-10-22, DEV):
- Fix: `maxlength="{{ form.username.field.max_length }}"` on the username input (renders `150`)
- Commit / change ref: `templates/accounts/login.html:18`
- Test evidence: `test_username_input_has_maxlength_150` (failed before the fix); real server `maxlength="150"` on `/ro/` and `/en/`
- Status: ✅ Resolved

---

### ISS-004: `get_success_url` re-validates what `get_redirect_url` already validated 🟢 Low

**Category**: Maintainability (DRY)
**File**: `src/infrastructure/web/accounts/views.py:22-31`

**Issue**: `LoginView.get_redirect_url()` already returns `""` unless `url_has_allowed_host_and_scheme(...)` passes (the inline comment says so). The second identical check is dead in practice and duplicates security logic in two places.

**Suggested Fix**:
```python
def get_success_url(self) -> str:
    # LoginView.get_redirect_url() returns "" unless next is same-host and safe.
    return self.get_redirect_url() or f"/{self.request.user.preferred_language}/"
```
Keep the existing open-redirect tests, which already cover it.


**Resolution** (2026-10-22, DEV):
- Fix: `get_success_url` returns `self.get_redirect_url() or f"/{preferred_language}/"`; the duplicate `url_has_allowed_host_and_scheme` call and its import are removed, and a comment names the single place the check lives
- Commit / change ref: `src/infrastructure/web/accounts/views.py:21-25`
- Test evidence: refactor; the existing open-redirect tests (`test_login.py -k "next or redirect"`: 9 passed) prove behaviour is unchanged; `views.py` 100% statements + branches
- Status: ✅ Resolved

---

### ISS-005: Per-username+IP lockout doesn't slow password spraying 🟢 Low (design note)

**Category**: Security (defence in depth)
**File**: `base.py` `AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]`

**Issue**: As specified by the architecture ("per username+IP"), one IP can try one or two common passwords against every username without ever reaching 5 failures for any single pair. This is a known limit of username+IP keying, not a deviation from the story.

**Suggested Fix** (DevOps / future story, no code change now): add an IP-level request rate limit at the reverse proxy for `POST /*/accounts/login/`, and/or an additional axes parameter set (`[["ip_address"]]` with a higher limit) after an architecture decision. Record it in `aire-devops-discover`.


**Deferral** (2026-10-22, DEV): deferred with user consent to `aire-devops-discover` (IP-level rate limit at the reverse proxy) or a future architecture decision on an extra axes parameter set. This is a design question, not a code defect. Still open.

**Resolution** (2026-10-23, DEV): user decision: close as mitigated at the proxy, with no extra axes IP-only rule.
- Fix: no application change. The IP-level limit the report suggests is delivered by DevOps in PR #1, `nginx/conf.d/00-http-context.conf`: `limit_req_zone $login_limit_key zone=login:10m rate=5r/m` keyed on POST only, applied with `limit_req zone=login burst=5 nodelay; limit_req_status 429;` on the sign-in location (`nginx/templates/app.conf.template:45-46`). Axes sees the same client address (`X-Forwarded-For $remote_addr`, `AXES_PROXY_COUNT=1`).
- Commit / change ref: none in `src/`. Takes effect when PR #1 is merged and deployed.
- Test evidence: not testable in the application test suite (Nginx configuration); the config is reviewed and validated with PR #1.
- Status: ✅ Resolved

---

## Issue Summary

| # | ID | Severity | Category | File | Status |
|---|-----|----------|----------|------|--------|
| 1 | ISS-001 | 🟡 Medium | Pattern | `templates/accounts/login.html`, `locked_out.html` | Should Fix |
| 2 | ISS-002 | 🟢 Low | Maintainability | `locked_out.html:10` | Optional |
| 3 | ISS-003 | 🟢 Low | Correctness (hint) | `login.html:16-18` | Optional |
| 4 | ISS-004 | 🟢 Low | Maintainability | `views.py:22-31` | Optional |
| 5 | ISS-005 | 🟢 Low | Security (design) | `base.py` axes parameters | Defer to DevOps / architecture |

**Summary**:
- Blockers: 0
- High: 0
- Medium: 1
- Low: 4

---

## What Was Done Well

1. ✅ The axes cool-off subtlety (`AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT`) was noticed from the story's "no side effect" row and pinned by a test.
2. ✅ Session-key rotation on a repeat sign-in fills a real gap in Django's `login()`.
3. ✅ One generic error for three failure modes, with the same timing path: no account enumeration.
4. ✅ Headers are asserted on the 429 lockout page too, not just on normal pages.
5. ✅ Tests use strict-CSRF clients for login/logout, which matches what the Story 1.0 review learned.

---

## Approval Status

**Decision**: ⚠️ APPROVED WITH COMMENTS

**Reason**: No blockers or high issues. ISS-001 should be fixed so the sign-in page uses the shared primitives before Story 1.6/1.7 style them. The Low items are optional; ISS-005 belongs to DevOps/architecture.

**Next Steps**:
1. `aire-dev-remediate` for ISS-001 (and optionally ISS-002–ISS-004)
2. Record ISS-005 for `aire-devops-discover`

---

## Sign-Off

**Reviewer**: REVIEWER Agent
**Date**: 2026-10-22
**Signature**: Approved with comments

---

# 🛠️ Remediation — 2026-10-22

**Developer**: DEV Agent
**Severity Scope**: 🟡 Medium + 🟢 Low ISS-002/003/004 (no 🔴/🟠); scope confirmed by the user
**Scenario**: Code Review
**Stories Affected**: 1.2
**Branch**: `feature/wave-2-dev-1` (after merging `feature/story-1.4-i18n` in `a5ce928`; wave 2 fully integrated)

## Issues Remediated

| ID | Severity | Story | File:Line | Summary | Resolution | Test Added |
|------|----------|-------|-----------|---------|------------|------------|
| ISS-001 | 🟡 Medium | 1.2 | `login.html:7,26`, `locked_out.html:7` | Bypassed UI primitives | `ui_icon` / `ui_button` | `test_templates_review_v1.py` (4) ✅ |
| ISS-002 | 🟢 Low | 1.2 | `locked_out.html:10`, `durations.py` | Hard-coded cool-off | Plural message from `AXES_COOLOFF_TIME`; RO 3 / EN 2 plural forms | 6 render cases + 6 filter unit + 2 catalogue ✅ |
| ISS-003 | 🟢 Low | 1.2 | `login.html:18` | Missing `maxlength` | From the form field (150) | 1 ✅ |
| ISS-004 | 🟢 Low | 1.2 | `views.py:21-25` | Duplicate `next` check | Single check via `get_redirect_url()` | existing open-redirect tests (9) ✅ |

## Issues Deferred (with user consent)

| ID | Severity | Story | Reason |
|----|----------|-------|--------|
| ISS-005 | 🟢 Low | 1.2 | Password spraying across usernames: proxy rate limit (DevOps) or an architecture decision |

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `src/infrastructure/web/templates/accounts/login.html` | Modified | Primitives; `maxlength` |
| `src/infrastructure/web/templates/accounts/locked_out.html` | Modified | Icon primitive; plural, setting-driven message |
| `src/infrastructure/web/templatetags/durations.py` | New | `minutes` filter |
| `src/infrastructure/web/accounts/views.py` | Modified | ISS-004 |
| `src/infrastructure/i18n/locale/{ro,en}/LC_MESSAGES/django.po` | Modified | `Plural-Forms` headers; plural lockout entry (regenerated with `--no-wrap`) |
| `tests/integration/web/accounts/test_templates_review_v1.py` | New | 12 tests |
| `tests/unit/infrastructure/test_durations.py` | New | 6 tests |
| `tests/integration/web/accounts/test_templates.py` | Modified | `blocktranslate` bodies count as translated; lock-icon check asserts the primitive |
| `tests/integration/web/accounts/test_translations.py` | Modified | Lockout sentence checked as a plural entry (RO 3 / EN 2 forms) |

## Patterns Applied

| Pattern | Where Applied | Notes |
|---------|---------------|-------|
| UI Primitive Catalogue §11.2 | sign-in and lockout pages | The single source for icon/button accessibility and styling |
| i18n §11.3 | lockout message | Proper plural forms instead of a fixed number |
| Configuration §10 | lockout text ← `AXES_COOLOFF_TIME` | The policy constant drives the UI |

## Testing Summary

- **Targeted tests added**: 18 (12 template/render, 6 filter) + 2 catalogue tests replacing one hard-coded entry
- **Full suite**: 677/677 passing (3 runs)
- **Coverage**: 100% (target ≥85%); domain 100%; application 100%
- **Gates**: ruff format/check clean · mypy 0 issues (92 files) · import-linter 2/2 kept · `makemigrations --check` no changes · `msgfmt --check`: 62/62 translated per language

**Test Output** (verbatim, filtered):
```
collected 677 items
tests/integration/web/accounts/test_templates_review_v1.py ............  [ 26%]
tests/integration/web/accounts/test_translations.py ............         [ 55%]
tests/unit/infrastructure/test_durations.py ......                       [ 97%]
src/infrastructure/web/accounts/views.py                     16      0      2      0   100%
src/infrastructure/web/templatetags/durations.py              8      0      2      0   100%
TOTAL                                                       637      0     68      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
============================= 677 passed in 6.92s ==============================
```

**Real server** (`runserver`, real CSRF tokens):
```
/ro/ login button: Autentificare          username input: maxlength="150"
/en/ login button: Sign in                username input: maxlength="150"
/ro/ 5th failure -> 429: Prea multe încercări eșuate. Încearcă din nou peste 15 minute sau cere ajutorul administratorului.   #lock-simple-duotone
/en/ 5th failure -> 429: Too many failed attempts. Try again in 15 minutes or ask the administrator.   #lock-simple-duotone
```

## Deviations from Report Suggestions

- ISS-002: `makemessages` fuzzy-matched the new plural entry to the old sentence (copying "15") and flagged it `fuzzy`. That entry was replaced by hand with correct plural forms, never left fuzzy. Two Story 1.2 tests that encoded the old single sentence or raw icon markup were updated to assert the same requirement in its new form.

## Lessons Learned

1. After changing a msgid, check `makemessages` output for `#, fuzzy`: gettext's similarity matching can carry a stale translation (here a hard-coded number) into the new entry.
2. Romanian needs three plural forms. Declaring `Plural-Forms` in the header is what makes `blocktranslate count` pick the right one.

## Next Steps

- [ ] Re-request code review (`aire-review-code`): optional (no 🔴 fixed)
- [ ] ISS-005 in `aire-devops-discover`

---

# 🛠️ Remediation — 2026-10-23

**Developer**: DEV Agent
**Severity Scope**: 🟢 Low (ISS-005, the previously deferred design note)
**Scenario**: Code Review
**Stories Affected**: 1.2
**Branch**: `main`

Combined pass: the four DevOps-deferred review items (1.0 ISS-004, 1.1 ISS-004, 1.2 ISS-005, 1.8 ISS-004) were remediated together on `main`, scope confirmed by the user.

## Issues Remediated

| ID | Severity | Story | File:Line | Summary | Resolution | Test Added |
|------|----------|-------|-----------|---------|------------|------------|
| ISS-005 | 🟢 Low | 1.2 | `base.py` axes parameters | Per username+IP lockout doesn't slow spraying | Mitigated at the proxy: Nginx login `limit_req` (PR #1); no app change by user decision | n/a: proxy config (non-testable in app) |

## Issues Deferred (with user consent)

None.

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| — | — | No application or test change for this item (see Resolution) |

## Testing Summary

- No targeted test: the mitigation is proxy configuration. The full suite below confirms the combined pass broke nothing.

**Test Output** (whole combined pass):
```
[full suite x3]  1532 passed, 17 deselected (13.87s / 14.30s / 14.58s) | Total coverage: 100.00%
[e2e]            17 passed, 1532 deselected in 7.11s
[ruff format]    193 files already formatted
[ruff check]     All checks passed!
[mypy]           Success: no issues found in 119 source files   (--no-incremental)
[lint-imports]   Contracts: 2 kept, 0 broken.
[makemigrations] No changes detected
```

**Dependency**: until PR #1 is merged and deployed, the limit isn't active in any environment.

## Deviations from Report Suggestions

- The report's optional second idea (an extra axes `[["ip_address"]]` parameter set) was not taken, by user decision.

## Lessons Learned

1. A defence that lives in another layer still needs a closing record in the review that raised it, pointing at the exact config.

## Next Steps

- [ ] Re-request code review (`aire-review-code`) — optional (no 🔴 fixed)
- [ ] DevOps (PR #1): add the new env names to `docs/deployment/pipeline-secrets.md` / compose env, and schedule `manage.py purge_audit_log` daily (systemd timer)
