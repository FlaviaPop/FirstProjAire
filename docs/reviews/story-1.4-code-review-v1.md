# Code Review - Story 1.4: Internationalization

> ## 🛠️ Remediation Status: ✅ Resolved
> - **Remediated**: 2026-10-22 by DEV Agent
> - **Fixed**: 3 issue(s) — 🔴 0 / 🟠 0 / 🟡 1 / 🟢 2
> - **Deferred (with user consent)**: 0
> - **Tests**: 757/757 passing | **Coverage**: 100% | **Linter**: clean
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
**Files Changed Since Last Review**: All (first review). Reviewed at `main` @ `d95f941`, which includes the later 1.2/1.8 remediations that touched `container.py` and `persistence/accounts/repositories.py`
**Severity Threshold Applied**: All

---

## Review Summary

**Components Reviewed**:
- `src/infrastructure/web/i18n_views.py` (51 lines)
- `src/application/accounts/update_preferred_language.py` (56)
- `src/infrastructure/persistence/accounts/repositories.py` (`DjangoUserPreferences`)
- `src/infrastructure/container.py` (`update_preferred_language`)
- `src/infrastructure/web/common/i18n.py` (23)
- `src/infrastructure/web/templatetags/i18n_content.py` (13)
- `src/infrastructure/web/templates/components/language_switcher.html`
- `src/infrastructure/web/static/css/components/language_switcher.css`
- `src/config/settings/base.py`, `src/config/settings/prod.py` (language cookie, middleware order)
- `src/config/urls.py`
- `src/infrastructure/web/common/decorators.py` (`PUBLIC_URL_NAMES`)
- RO/EN `django.po`, `.gitignore`, the README "Translations" section

**Lines of Code**: ~230 production lines, ~400 test lines (story commit `42aaf37`: 1,274 insertions, mostly `.po` reflow)
**Tests Reviewed**: Yes:
- `tests/unit/application/accounts/test_update_preferred_language.py`
- `tests/unit/infrastructure/test_i18n_helpers.py`
- `tests/integration/web/i18n/test_language_switch.py`
- `tests/integration/web/i18n/test_switcher_and_tag.py`
- the language-aware updates to earlier tests and `tests/conftest.py`

**Coverage**: 100% overall. Every Story 1.4 module is at 100% line and branch coverage.

**Overall Assessment**: A clean, well-layered implementation:
- The use case depends only on domain types, a Protocol port and a structural unit-of-work factory.
- The view derives the user only from the session, which closes the preference-write IDOR.
- Django's `set_language` is reused, with two documented corrections: ro/en only, and translating `next` from its own prefix.

One real defect: on the invalid-language branch, a `next` value without a leading `/` reaches `django.shortcuts.redirect`, which treats it as a URL pattern name and can raise a 500 (ISS-001). The two remaining findings are a missing test and a small design-token gap.

---

## Evidence Verified (re-run by REVIEWER, 2026-10-22)

```
$ uv run ruff format --check .        → 130 files already formatted
$ uv run ruff check .                 → All checks passed!
$ uv run mypy                         → Success: no issues found in 95 source files
$ PYTHONPATH=src uv run lint-imports  → Contracts: 2 kept, 0 broken.
$ manage.py makemigrations --check --dry-run → No changes detected
$ manage.py compilemessages --ignore=.venv   → … is already compiled and up to date.
$ uv run pytest -q --cov=src --cov-branch --cov-fail-under=85
src/application/accounts/update_preferred_language.py        23      0      4      0   100%
src/infrastructure/web/common/i18n.py                         8      0      0      0   100%
src/infrastructure/web/i18n_views.py                         34      0      8      0   100%
src/infrastructure/web/templatetags/i18n_content.py           6      0      0      0   100%
TOTAL                                                       681      0     74      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
744 passed in 7.53s
```

**Probes**: a temporary test file, deleted afterwards. The working tree was clean after the run.

```
PROBE lang=de next='home'               -> 500 None      ← ISS-001 (NoReverseMatch in redirect())
PROBE lang=de next='login'              -> 500 None      ← ISS-001
PROBE lang=de next='set_language'       -> 302 /i18n/setlang/   (reversed as a URL name)
PROBE lang=de next='x.html'             -> 302 x.html    (relative → /i18n/x.html, 404)
PROBE lang=en next='home'               -> 302 home      (relative → /i18n/home, 404)
PROBE GET /                             -> 404           (AC 2 target home:index is Story 1.7; hand-off recorded)
PROBE signed-in switch ro→en            -> 302 /en/accounts/login/, 6 queries:
    SAVEPOINT … / SELECT preferred_language … WHERE id = 1 /
    UPDATE "accounts_user" SET "preferred_language" = 'en' WHERE "accounts_user"."id" = 1 / RELEASE
```

The signed-in probe confirms AC 6: the write is a single-column `UPDATE … WHERE id = <session user>`, inside the unit of work.

---

## Acceptance Criteria Check

| AC | Result | Evidence |
|----|--------|----------|
| 1 Middleware order and language settings | ✅ | `base.py:31`, `:80-88`; `prod.py:18`; `test_locale_middleware_sits_right_after_sessions`, `test_language_settings_and_cookie_policy` |
| 2 `/` → cookie, then `Accept-Language`, then `ro` | ⚠️ Partially verified | The language choice is proven on the unprefixed `/accounts/login/` (3 tests). `/` itself returns 404 until Story 1.7 adds `home:index`; the hand-off is in the Story 1.7 file. Not an issue against 1.4 |
| 3 Switch, cookie, translated `next`; unsafe or missing `next` → `/<lang>/` | ✅ | `test_anonymous_switch…`, `test_switch_back_to_romanian`, `test_unsafe_or_missing_next…` (3 cases) |
| 4 Invalid code → no cookie, no write | ✅ (see ISS-001 for relative `next`) | `test_invalid_language_changes_nothing` (4 codes; query capture) |
| 5 GET → 405; no CSRF → 403 | ✅ | `test_get_is_not_allowed`, `test_post_without_csrf…` |
| 6 Persists for the session user only; no write when unchanged | ✅ | `test_signed_in_switch_persists_only_for_current_user` (with forged `user_id` and `username`), `test_switching_to_the_current_preference_writes_nothing`, plus the probe above |
| 7 Use case raises `unsupported_language` | ✅ | unit test, 4 codes, no read or write before raising |
| 8 `content_language` and `localized` | ✅ | 6 mappings; fails loudly; never falls back |
| 9 `{% localized %}` autoescaped | ✅ | `test_localized_tag_autoescapes` |
| 10 Switcher markup, no JS or inline style | ✅ | 5 switcher tests |
| 11 `test_translations_complete` without gettext | ✅ | Own parser handles plurals, fuzzy and multi-line entries (parser self-tests) |
| 12 gettext installed; `.mo` gitignored; README | ✅ | `compilemessages` run above; `.gitignore:36`; README "Translations" |
| 13 Switcher strings in RO and EN | ✅ | `ro/django.po:95-104` |

---

## Checklist Results

### Correctness
- [x] ✅ Code does what it's supposed to (13/13 AC; AC 2's `/` case handed off to 1.7)
- [x] ⚠️ Edge cases handled: a bare or relative `next` is accepted (ISS-001)
- [x] ✅ Error conditions handled: an invalid code changes nothing; a DB failure happens before the response, so no cookie is set
- [x] ✅ No race conditions: the read-compare-write runs inside `DjangoUnitOfWork` (IMMEDIATE transaction)

### Pattern Adherence
- [x] ✅ Use case + port + UoW (patterns §5, §6.3); wired only in `container.py`
- [x] ✅ Clean Architecture: application imports only domain and stdlib; import-linter contracts kept
- [x] ✅ i18n rules §11.3: `localized` is the single way to read `_ro`/`_en` and fails loudly
- [x] ✅ UI primitive §11.2: tokens only; staff and student sizes come from the theme variables
- [x] ⚠️ Design tokens: icon variant is always `regular`; the spec wants duotone for students (ISS-003)
- [x] ✅ Naming, file organization; functions < 30 lines (`switch_language` has 18 body lines)

### Testing
- [x] ✅ Unit tests exist and are behavioural (the fake port records writes)
- [x] ✅ Integration tests cover IDOR, idempotency, invalid codes, open redirect, 405, 403 and the sign-in round trip
- [x] ⚠️ The "DB unavailable → 500, no cookie" row of the story's response table is untested (ISS-002)
- [x] ✅ Coverage 100% (≥85%)
- [x] ✅ Test isolation: the autouse `_reset_active_language` fixture; `compiled_catalogues` fails with an actionable message

### Documentation
- [x] ✅ Docstrings on every public function and class; the non-obvious `translation.override(source)` is explained
- [x] ✅ No TODOs; no commented-out code
- [x] ✅ Self-review exists: `docs/stories-implemented/story-1.4-review.md`

### Security
- [x] ✅ No secrets
- [x] ✅ IDOR: the user comes from `request.user.pk` only; forged `user_id` and `username` are ignored (tested)
- [x] ✅ Open redirect: `url_has_allowed_host_and_scheme` against the request host, with `require_https` on secure requests; `https://` and `//` are tested
- [x] ✅ CSRF enforced (403 tested); public endpoint listed in `PUBLIC_URL_NAMES`
- [x] ✅ Cookie: `SameSite=Lax`; `Secure` follows `SESSION_COOKIE_SECURE` in prod
- [x] ✅ XSS: `next` is autoescaped in the hidden input; the `localized` tag autoescapes (tested)

### Performance
- [x] ✅ Signed-in switch: one SELECT plus one conditional UPDATE; anonymous switch: no DB access

### SOLID / Anti-Monolith
- [x] ✅ SRP: view (HTTP), use case (rule), adapter (SQL), helper (content language) are separate
- [x] ✅ DIP: the use case depends on `UserPreferencePort` and a factory; the container chooses the implementations
- [x] ✅ ISP: two-method port
- [x] ✅ No new global state; no cross-context coupling

---

## Issues Found

### ISS-001: A `next` without a leading `/` is redirected as-is, and can return a 500 🟡 Medium

**Category**: Correctness
**File**: `src/infrastructure/web/i18n_views.py:20-25`, `:34`
**Pattern Reference**: `docs/architecture/design/01-patterns-and-standards-greenfield.md` §8 (a client error must not become a 5xx); story AC 4 ("302 back to the safe `next` … or `/<current>/`")

**Issue**:
`_safe_next` accepts any value that `url_has_allowed_host_and_scheme` allows, and that includes bare relative strings such as `home`, `login` or `x.html`. Two consequences:
1. On the **invalid-language** branch the value goes to `django.shortcuts.redirect()`. That function first tries `reverse(next)`, and for a value with no `/` or `.` it re-raises `NoReverseMatch`, so the response is **500**, logged at ERROR (probe: `language=de next=home` → 500). A value that happens to be a URL name is reversed instead (`next=set_language` → `/i18n/setlang/`).
2. On both branches, other relative values become a `Location` relative to `/i18n/setlang/`, for example `/i18n/home`, which is a 404.

The real switcher always posts `request.get_full_path` (an absolute path), and CSRF blocks cross-site use, so only a hand-crafted request triggers this. It is still a user-controllable 500 and an ERROR log line, which the 1.1 review treated as worth fixing (1.1 ISS-002).

**Current Code**:
```python
def _safe_next(request: HttpRequest) -> str | None:
    next_url = request.POST.get("next", "")
    allowed = {request.get_host()}
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed, request.is_secure()):
        return next_url
    return None
...
        return redirect(_safe_next(request) or f"/{content_language()}/")
```

**Suggested Fix**: accept only path-absolute URLs, and never resolve URL names from request input:
```python
def _safe_next(request: HttpRequest) -> str | None:
    """`next` if it's a same-site absolute path ("/ro/x/"); anything else falls back."""
    next_url = request.POST.get("next", "")
    allowed = {request.get_host()}
    if next_url.startswith("/") and url_has_allowed_host_and_scheme(
        next_url, allowed, request.is_secure()
    ):
        return next_url
    return None
...
        return HttpResponseRedirect(_safe_next(request) or f"/{content_language()}/")
```
`//evil.example/` still fails `url_has_allowed_host_and_scheme`, so the open-redirect protection is unchanged.

**Suggested Test**:
```python
@pytest.mark.parametrize("next_url", ["home", "login", "set_language", "x.html", "ro/accounts/login/"])
@pytest.mark.parametrize(("code", "root"), [("de", "/ro/"), ("en", "/en/")])
def test_relative_next_falls_back_to_language_root(client, code, root, next_url):
    response = client.post(URL, {"language": code, "next": next_url})

    assert (response.status_code, response["Location"]) == (302, root)
```

**Why This Matters**: a crafted form value must not produce a server error, and the redirect target should come only from the validated value, never from URL-name resolution.


**Resolution** (2026-10-22, DEV):
- Fix: `_safe_next` accepts only a same-site **absolute path** (`next_url.startswith("/")` + `url_has_allowed_host_and_scheme`); the invalid-language branch uses `HttpResponseRedirect` instead of `shortcuts.redirect`, so request input is never resolved as a URL name. As suggested
- Commit / change ref: `src/infrastructure/web/i18n_views.py` (`_safe_next`, `switch_language`; `redirect` import removed)
- Test evidence: `test_language_switch.py::test_relative_next_falls_back_to_language_root` (10 cases: `home`, `login`, `set_language`, `x.html`, `ro/accounts/login/` × `de`/`en`). All 10 failed before the fix (500 or a relative `Location`); they pass now. Real server: the same values → `302 /<lang>/`, 0 ERROR log lines
- Status: ✅ Resolved

---

### ISS-002: No test for the "DB unavailable → 500, cookie not set" row 🟢 Low

**Category**: Testing
**File**: `tests/integration/web/i18n/test_language_switch.py`
**Pattern Reference**: Story 1.4 "System responses + error cases", last row; patterns §12 (error scenarios)

**Issue**:
The code is correct: `set_language` builds the response, then the preference write runs, and an exception discards the response, so no cookie is sent. No test pins this down. A future refactor that writes the preference *after* returning (for example in a `finally`, or by reordering) would set the cookie while the save failed, and nothing would catch it.

**Suggested Test**:
```python
def test_preference_write_failure_returns_500_without_cookie(client, monkeypatch):
    client.raise_request_exception = False
    client.force_login(UserFactory(preferred_language="ro"))

    def boom(self, user_id, language):
        raise DatabaseError("db down")

    monkeypatch.setattr(DjangoUserPreferences, "set_language", boom)

    response = client.post(URL, {"language": "en", "next": "/ro/"})

    assert response.status_code == 500
    assert "django_language" not in response.cookies
```


**Resolution** (2026-10-22, DEV):
- Fix: test only (the behaviour was already correct; the test pins it down)
- Commit / change ref: `tests/integration/web/i18n/test_language_switch.py::test_preference_write_failure_returns_500_without_cookie`
- Test evidence: with `DjangoUserPreferences.set_language` raising `DatabaseError`, the response is 500 and there is no `django_language` cookie. It passed before and after (a characterisation test; it fails if the save ever moves after the response)
- Status: ✅ Resolved

---

### ISS-003: Switcher icon is always `regular`; the spec asks for duotone in the student theme 🟢 Low

**Category**: Pattern (design tokens)
**File**: `src/infrastructure/web/templates/components/language_switcher.html:5`
**Pattern Reference**: Story 1.4 Design Tokens: "Phosphor `translate` 20px, regular for staff and duotone for student"; patterns §11.2

**Issue**:
`{% ui_icon "translate" size=20 %}` always renders the regular symbol. Duotone is a different sprite symbol, so CSS under `.theme-student` can't swap it. Nothing renders the switcher yet (Story 1.7 places it), so the impact is nil today.

**Suggested Fix**: let the includer choose, defaulting to regular:
```django
{% ui_icon "translate" size=20 variant=icon_variant|default:"regular" %}
```
Story 1.7's student layout then uses `{% include "components/language_switcher.html" with icon_variant="duotone" %}`. Add a test that the student variant references `#translate-duotone`.


**Resolution** (2026-10-22, DEV):
- Fix: `{% ui_icon "translate" size=20 variant=icon_variant|default:"regular" %}`; Story 1.7's hand-off now says to include the switcher `with icon_variant="duotone"` in the student theme and to assert it
- Commit / change ref: `templates/components/language_switcher.html:5`; `docs/plans/stories/epic-1-story-1.7-App-Shell-and-Role-Homes.md` (hand-off line)
- Test evidence: `test_switcher_and_tag.py::test_switcher_icon_variant` (default → `#translate`, `icon_variant="duotone"` → `#translate-duotone`); the duotone case failed before the fix
- Status: ✅ Resolved

---

## Issue Summary

| # | ID | Severity | Category | File | Status |
|---|-----|----------|----------|------|--------|
| 1 | ISS-001 | 🟡 Medium | Correctness | `i18n_views.py:20-25, 34` | Should Fix |
| 2 | ISS-002 | 🟢 Low | Testing | `test_language_switch.py` | Optional |
| 3 | ISS-003 | 🟢 Low | Pattern | `language_switcher.html:5` | Optional |

**Summary**:
- Blockers: 0
- High: 0
- Medium: 1
- Low: 2

---

## What Was Done Well

1. ✅ The IDOR guard is explicit and tested: the user comes from the session only, and a test posts a forged `user_id` and `username` and checks that the other user's row is unchanged.
2. ✅ Idempotency is proven at the SQL level with query capture, not only through the fake port.
3. ✅ The subtle `translate_url` gotcha (`/en/x/` with a `ro` cookie) was found, fixed and explained in a comment.
4. ✅ The translation-completeness parser has its own tests (plurals, fuzzy, multi-line), so CI cannot pass because the parser is silently broken.
5. ✅ Strong test hygiene: the autouse language reset and the actionable `compiled_catalogues` failure prevent order-dependent and environment-dependent flakes.
6. ✅ The `*.mo` build-artefact policy and gettext setup without admin rights are documented in the README.

---

## Approval Status

**Decision**: ⚠️ APPROVED WITH COMMENTS

**Reason**: no blockers and no high-severity issues. ISS-001 is a medium correctness issue that only a hand-crafted request can trigger; it should be fixed before Story 1.7 puts the switcher on every page. ISS-002 and ISS-003 are optional.

**Next Steps**:
1. `aire-dev-remediate` for ISS-001 (recommended), with ISS-002 and ISS-003 optional.
2. ISS-003 can instead be done inside Story 1.7 when the switcher is placed.

---

## Sign-Off

**Reviewer**: REVIEWER Agent
**Date**: 2026-10-22
**Signature**: Approved with comments

---

# 🛠️ Remediation — 2026-10-22

**Developer**: DEV Agent
**Severity Scope**: 🟡 ISS-001 + 🟢 ISS-002 + 🟢 ISS-003 (all findings; scope confirmed by the user)
**Scenario**: Code Review
**Stories Affected**: 1.4 (plus a hand-off line in Story 1.7)
**Branch**: `main`

## Issues Remediated

| ID | Severity | Story | File | Summary | Resolution | Test Added |
|------|----------|-------|------|---------|------------|------------|
| ISS-001 | 🟡 Medium | 1.4 | `web/i18n_views.py` | Bare or relative `next` → 500 or relative redirect | Absolute same-site paths only; `HttpResponseRedirect` | `test_relative_next_falls_back_to_language_root` (10) ✅ |
| ISS-002 | 🟢 Low | 1.4 | `test_language_switch.py` | DB-failure row untested | Characterisation test | `test_preference_write_failure_returns_500_without_cookie` (1) ✅ |
| ISS-003 | 🟢 Low | 1.4→1.7 | `components/language_switcher.html` | Student duotone icon | `icon_variant` parameter, `regular` by default | `test_switcher_icon_variant` (2) ✅ |

## Issues Deferred (with user consent)

None.

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `src/infrastructure/web/i18n_views.py` | Modified | `_safe_next` requires a leading `/`; direct `HttpResponseRedirect` |
| `src/infrastructure/web/templates/components/language_switcher.html` | Modified | `icon_variant` (default `regular`) |
| `tests/integration/web/i18n/test_language_switch.py` | Modified | +11 tests |
| `tests/integration/web/i18n/test_switcher_and_tag.py` | Modified | +2 tests; `_render_switcher` accepts context |
| `docs/plans/stories/epic-1-story-1.7-App-Shell-and-Role-Homes.md` | Modified | Student switcher uses `icon_variant="duotone"` |

## Patterns Applied

| Pattern | Where Applied | Notes |
|---------|---------------|-------|
| Error handling §8 | `switch_language` | Client input never produces a 5xx |
| UI primitive §11.2 | switcher | Variant chosen by the includer; staff default unchanged |

## Testing Summary

- **Targeted tests added**: 13 (11 failed before the fixes; the ISS-002 characterisation test passed before and after)
- **Full suite**: 757/757 passing (3 runs)
- **Coverage**: 100% (target ≥85%)
- **Gates**: ruff format/check clean · mypy 0 issues (95 files) · import-linter 2/2 kept · `makemigrations --check` no changes

**Before the fix** (targeted):
```
FAILED test_language_switch.py::test_relative_next_falls_back_to_language_root[de-/ro/-home]
… (10 × test_relative_next_falls_back_to_language_root)
FAILED test_switcher_and_tag.py::test_switcher_icon_variant[…#translate-duotone"]
11 failed, 34 passed in 0.32s
```

**After the fix** (full suite):
```
src/infrastructure/web/i18n_views.py                         33      0      8      0   100%
TOTAL                                                       680      0     74      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
757 passed in 7.06s
```

**Real server** (`runserver`, real CSRF token):
```
POST language=de next=home                  -> 302 /ro/
POST language=de next=login                 -> 302 /ro/
POST language=de next=set_language          -> 302 /ro/
POST language=en next=home                  -> 302 /en/
POST language=en next=x.html                -> 302 /en/
POST language=en next=/ro/accounts/login/   -> 302 /en/accounts/login/
POST language=ro next=/en/accounts/login/   -> 302 /ro/accounts/login/
POST language=en next=https://evil.example/ -> 302 /en/
ERROR lines in server log: 0
```

## Deviations from Report Suggestions

None.

## Lessons Learned

1. `django.shortcuts.redirect` resolves URL names. Never pass request input to it; use `HttpResponseRedirect` with a validated path.
2. "Safe" (same host) and "well-formed" (absolute path) are separate checks for a redirect target.

## Next Steps

- [ ] Re-request code review (`aire-review-code`): optional (no 🔴 or 🟠 issues)
- [ ] Story 1.7 applies the `icon_variant="duotone"` hand-off
