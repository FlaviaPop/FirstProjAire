# Code Review - Story 1.2: Login & Session Security

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

---

### ISS-002: Lockout message hard-codes the cool-off duration 🟢 Low

**Category**: Maintainability
**File**: `src/infrastructure/web/templates/accounts/locked_out.html:10`; `base.py` `AXES_COOLOFF_TIME`

**Issue**: "Try again in 15 minutes" is a translated literal, while the duration is the setting `AXES_COOLOFF_TIME = timedelta(minutes=15)`. Changing the policy would leave the message wrong in both languages.

**Suggested Fix**: Pass `cooloff_minutes` to the template (axes' `AXES_LOCKOUT_TEMPLATE` context includes `cooloff_time`; or compute `int(settings.AXES_COOLOFF_TIME.total_seconds() // 60)`) and use `{% blocktranslate count minutes=cooloff_minutes %}…{{ minutes }} minute…{% plural %}…{{ minutes }} minutes…{% endblocktranslate %}`. Update the `.po` entries with `makemessages --no-wrap`.

---

### ISS-003: Hand-written username input drops `maxlength` 🟢 Low

**Category**: Correctness (input validation hint)
**File**: `src/infrastructure/web/templates/accounts/login.html:16-18`

**Issue**: The form field has `max_length=150` (Django's `AuthenticationForm`), which Django renders as `maxlength="150"`. The hand-written `<input>` omits it (probe: `maxlength on username input: False`). Server-side validation still applies, so this is only a missing client-side hint and a small parity gap with Django's widget.

**Suggested Fix**: Add `maxlength="{{ form.username.field.max_length }}"`, or render the field's widget attributes once Story 1.6's `form_field` primitive exists.

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

---

### ISS-005: Per-username+IP lockout doesn't slow password spraying 🟢 Low (design note)

**Category**: Security (defence in depth)
**File**: `base.py` `AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]`

**Issue**: As specified by the architecture ("per username+IP"), one IP can try one or two common passwords against every username without ever reaching 5 failures for any single pair. This is a known limit of username+IP keying, not a deviation from the story.

**Suggested Fix** (DevOps / future story, no code change now): add an IP-level request rate limit at the reverse proxy for `POST /*/accounts/login/`, and/or an additional axes parameter set (`[["ip_address"]]` with a higher limit) after an architecture decision. Record it in `aire-devops-discover`.

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
