# Code Review - Story 1.7: App Shell & Role Homes

> ## 🛠️ Remediation Status: ✅ Resolved
> - **Remediated**: 2026-10-23 by DEV Agent
> - **Fixed**: 3 issue(s) — 🔴 0 / 🟠 0 / 🟡 1 / 🟢 2
> - **Deferred (with user consent)**: 0
> - **Tests**: 1350/1350 passing | **Coverage**: 100% | **Linter**: clean
> - **Scenario**: Code Review

**Date**: 2026-10-23
**Reviewed By**: REVIEWER Agent
**Review Number**: 1
**Review Mode**: INITIAL_REVIEW
**Status**: ⚠️ APPROVED WITH COMMENTS

> **Independence note:** this story was implemented in the same session (DEV, one-by-one). To counter author bias, the review checks the code against the story and its Must Read references, not against the self-review, and probes the edge cases the author was most likely to have rationalised. The user was offered a fresh-agent review and chose this one.

---

## Review Metadata

**Previous Review**: None
**Previous Status**: N/A
**Files Changed Since Last Review**: All (first review). Reviewed at `main` @ `bc6c56e`
**Severity Threshold Applied**: All

---

## Review Summary

**Components Reviewed**:
- **Layout templates:** `layouts/base.html`, `_top_bar.html`, `_nav.html`, `_messages.html`
- **Home templates:** `home/{student,teacher,parent,admin}.html`, `home/_cards.html`
- **Python:** `web/home/navigation.py` (`NAV_BY_ROLE`, `available_sections`), `web/home/views.py`, `web/home/urls.py`, `templatetags/navigation.py` (`shell_user`, `shell_messages`, `alert_level`, `role_nav`, `role_home_cards`)
- **Static files:** `static/css/layout.css`, `static/js/htmx.min.js` (vendored)
- **Wiring and text:** `config/urls.py`, RO/EN catalogues
- **Tests:** the new home tests, plus the changes to Story 1.1/1.4/1.6 tests and the Story 1.1 file note

**Lines of Code**: ~330 production lines (templates, Python, CSS) + 52 KB vendored JS; ~560 test lines
**Tests Reviewed**: Yes:
- `tests/integration/web/home/`: `test_home.py`, `test_navigation.py`, `test_shell_without_database.py`, `test_root_redirect.py`
- matrix rows
- the modified `test_error_middleware.py`, `test_request_id_logging.py`, `test_parent_link_admin.py`, `test_base_layout_styles.py`

**Coverage**: 100% overall; `web/home/*` and `templatetags/navigation.py` at 100% line and branch coverage

**Overall Assessment**: The shell meets every acceptance criterion and the three binding hand-offs:
- One registry feeds both the menu and the cards, so they can't disagree.
- Links are filtered by permission and by route existence, and never error.
- The layout degrades to an anonymous shell when the database is down, so error pages keep working.
- htmx is vendored with verified integrity, and pages have no inline script or style.

The changes to earlier stories' tests are legitimate contract updates (the owner-approved `csrftoken` cookie; the full stylesheet set; external scripts only), not silent weakening:
- Each changed assertion still forbids what the original protected (sessions, inline scripts).
- Each change carries a comment explaining why.

Three findings:
- The sticky top bar has no scroll offset, so focus and in-page targets can be hidden underneath it (ISS-001).
- A leading space in a name loses the greeting (ISS-002).
- An empty navigation landmark is rendered for a corrupt role (ISS-003).

---

## Evidence Verified (re-run by REVIEWER, 2026-10-23)

```
[ruff format]  165 files already formatted
[ruff check]   All checks passed!
[mypy]         Success: no issues found in 110 source files          (--no-incremental)
[lint-imports] Contracts: 2 kept, 0 broken.
[migrations]   No changes detected
src/infrastructure/web/home/navigation.py                    31      0      6      0   100%
src/infrastructure/web/home/views.py                         11      0      0      0   100%
src/infrastructure/web/templatetags/navigation.py            40      0      4      0   100%
TOTAL                                                      1298      0    192      0   100%
1344 passed in 10.89s
```

**Probes** (a temporary test file, deleted afterwards; working tree clean):
```
greeting for 'Ana'            -> "Hello, Ana!"
greeting for 'Ana-Maria Pop'  -> "Hello, Ana-Maria!"
greeting for '<b>Ana</b> X'   -> "Hello, &lt;b&gt;Ana&lt;/b&gt;!"      (escaped)
greeting for ''               -> "Hello!"                              (intended fallback)
greeting for '  Ana Pop'      -> "Hello!"                              ← ISS-002 (name lost)
corrupt role, 403 page nav    -> <nav class="main-nav" aria-label="Main"> <ul class="main-nav__list"> </ul> </nav>   ← ISS-003
/ro/?x=1 aria-current count   -> 1 (query string doesn't break the marker)
language switch from home     -> 302 /en/
DB down: /ro/accounts/login/  -> 200 with the shell (anonymous)
DB down: /ro/admin/, /en/     -> 500 page rendered with the shell (expected: the view itself needs the DB)
```
The real-server evidence in `docs/stories-implemented/story-1.7-review.md` was re-read and matches the code: four role homes, redirects, a DEBUG-off 404 inside the full layout, 0 inline script/style, CSP header unchanged.

---

## Acceptance Criteria Check

| AC | Result | Evidence |
|----|--------|----------|
| 1 `base.html` (lang, htmx-config, all CSS, htmx defer + ui.js module, theme + `hx-headers`, skip link first, `<main id=content tabindex=-1>`, no inline) | ✅ (see ISS-001) | `base.html:2-35`; 5 layout tests |
| 2 Messages via `ui_alert`, level mapping, consumed | ✅ | `_messages.html`, `ALERT_LEVEL`; 2 tests |
| 3 Top bar: brand, `<nav aria-label="Main">` + `aria-current`, switcher, account menu with POST sign-out | ✅ (see ISS-003) | `_top_bar.html`, `_nav.html`; 3 tests |
| 3a Anonymous: brand + switcher only | ✅ | test |
| 4 `NAV_BY_ROLE` exact and in order | ✅ | `home/navigation.py:35-96`; exact-shape test |
| 5 `available_sections` filters, invalid role `()`, never raises | ✅ | `home/navigation.py:99-115`; 6 tests |
| 6 `home:index` per role; anonymous 302; corrupt role 403; `greeting_name`, `sections` | ✅ (see ISS-002) | `home/views.py`; tests + matrix |
| 7 One `<h1>`, `ui_card` per section, `ui_empty_state` | ✅ | `home/*.html`, `_cards.html`; tests |
| 8 Matrix rows | ✅ | `test_role_access_matrix.py:37-40` |
| 9 Every rendered link permitted | ✅ | 4 role tests + staff-link test |
| 10 htmx 2.0.x vendored, version comment, no CDN | ✅ | `htmx.min.js:1` (2.0.11, 0BSD, upstream sha256; body byte-identical) |
| 11 RO/EN for all new strings | ✅ | catalogues; `test_translations_complete`; `makemessages` re-run: 0 changes, 0 fuzzy |
| Hand-offs 1.1 ISS-003, 1.4 `/`, 1.4 ISS-003 | ✅ | `test_shell_without_database.py`, `test_root_redirect.py`, switcher icon tests |

---

## Checklist Results

### Correctness
- [x] ✅ Menu and cards from one registry (tested equal for every role)
- [x] ✅ No 500 for unshipped routes; no DB writes on render (query capture)
- [x] ⚠️ Greeting with leading whitespace (ISS-002)

### Pattern Adherence
- [x] ✅ §7.4 HTMX: vendored, CSRF via `hx-headers`, `allowEval`/`allowScriptTags`/`includeIndicatorStyles` false
- [x] ✅ §11.2: reuses `ui_card`, `ui_empty_state`, `ui_alert`, `ui_avatar`, `ui_button`, `ui_icon` and the switcher; no duplicated markup
- [x] ⚠️ §11.4 accessibility: sticky-bar focus obscuring (ISS-001); empty landmark (ISS-003)
- [x] ✅ `layout.css` tokens only (raw-hex and `!important` guards pass)

### Testing
- [x] ✅ Tests first (red phase recorded); story Tests block plus registry, filtering, DB-down, redirect and matrix tests
- [x] ✅ Earlier-story test changes are scoped, commented contract updates (owner decision for `csrftoken`)
- [x] ✅ Coverage 100%

### Documentation
- [x] ✅ Docstrings explain the why (db-safe shell, registry contract); self-review honest about the missing browser checks

### Security
- [x] ✅ Links a role lacks are never rendered; target views keep their own guards
- [x] ✅ Role and name come from the session only; output escaped
- [x] ✅ CSP unchanged; no inline script/style; htmx eval disabled
- [x] ✅ Sign-out is a POST with CSRF

### Performance
- [x] ✅ Registry filtering is in-memory `reverse()` calls; two passes per home render (menu + cards) are negligible

### SOLID / Anti-Monolith
- [x] ✅ Registry, tags, view and templates each have one job; later features plug in by shipping a route

---

## Issues Found

### ISS-001: The sticky top bar has no scroll offset, so focused elements and in-page targets can sit hidden underneath it 🟡 Medium

**Category**: Accessibility
**File**: `src/infrastructure/web/static/css/layout.css` (`.top-bar { position: sticky; top: 0; … min-height: var(--nav-height) }`; no `scroll-padding-top` anywhere in `static/css`, confirmed with grep)
**Pattern Reference**: patterns §11.4 (accessibility baseline, WCAG 2.2 AA); WCAG 2.4.11 Focus Not Obscured (Minimum); Story 1.7 "Everything works with the keyboard"

**Issue**:
The 64px top bar is `position: sticky`. When the browser scrolls to bring something into view, it aligns it to the viewport's top edge, which is underneath the bar. That happens on:
- **Shift+Tab** upwards through a long page;
- following an in-page `#fragment` link;
- `focus()` from script, for example `ui.js` moving focus to `<main>` after dismissing an alert (Story 1.6 ISS-002).

A 32–44px control (staff and student touch sizes) can end up **entirely** hidden behind the 64px bar. That fails 2.4.11 (AA). Today's pages are short, so it rarely shows. CYCLE-2's lesson, exercise and test editors are long forms, where keyboard users will hit it constantly.

**Suggested Fix** (one rule, tokens only):
```css
/* Scrolling to focus or #targets leaves room for the sticky top bar (WCAG 2.4.11). */
html { scroll-padding-top: calc(var(--nav-height) + var(--space-2)); }
```

**Suggested Test** (static, like the other CSS contract tests):
```python
def test_scroll_padding_clears_the_sticky_top_bar():
    css = finders.find("css/layout.css")
    text = open(css, encoding="utf-8").read()

    assert "position: sticky" in text
    assert re.search(r"html\s*\{[^}]*scroll-padding-top:\s*calc\(var\(--nav-height\)", text)
```
Also add a browser assertion to Story 1.10 (focus a field low on a long page with Shift+Tab; its bounding box top is ≥ the bar height).


**Resolution** (2026-10-23, DEV):
- Fix: `html { scroll-padding-top: calc(var(--nav-height) + var(--space-2)); }` (tokens only), as suggested; Story 1.10 gets the browser assertion (Shift+Tab focus stays below the 64px bar)
- Commit / change ref: `src/infrastructure/web/static/css/layout.css` (first rule); `docs/plans/stories/epic-1-story-1.10-Foundation-E2E-Journeys.md` (hand-off)
- Test evidence: `test_shell_review_fixes.py::test_scroll_padding_clears_the_sticky_top_bar` failed before the fix and passes now; real server serves `html { scroll-padding-top: calc(var(--nav-height) + var(--space-2)); }`
- Status: ✅ Resolved

---

### ISS-002: A leading space in the full name loses the greeting 🟢 Low

**Category**: Correctness
**File**: `src/infrastructure/web/home/views.py:23`

**Issue**:
`(full_name or "").split(" ")[0]` returns `""` when the name starts with a space (probe: `"  Ana Pop"` → "Hello!"). It also mishandles tabs and repeated spaces. The admin forms strip whitespace, so this mainly affects accounts created through the shell or imports, but it is the greeting a child sees first.

**Suggested Fix**:
```python
"greeting_name": next(iter((getattr(user, "full_name", "") or "").split()), ""),
```

**Suggested Test**:
```python
@pytest.mark.parametrize("name", ["  Ana Pop", "Ana\tPop", "Ana  Pop"])
def test_greeting_ignores_surrounding_whitespace(client, name):
    client.force_login(UserFactory(role="STUDENT", full_name=name))

    assert "Hello, Ana!" in client.get("/en/").content.decode()
```


**Resolution** (2026-10-23, DEV):
- Fix: `next(iter(full_name.split()), "")`: the first word, ignoring stray spaces and tabs
- Commit / change ref: `src/infrastructure/web/home/views.py:23-24`
- Test evidence: `test_greeting_ignores_surrounding_whitespace` (`"  Ana Pop"`, `"Ana\tPop"`, `" Ana"` failed before; `"Ana  Pop"` passed before and after). Real server: a student named `"  Ana Maria Pop"` sees `Bună, Ana!`
- Status: ✅ Resolved

---

### ISS-003: A signed-in user with no available sections gets an empty "Main" navigation landmark 🟢 Low

**Category**: Accessibility
**File**: `src/infrastructure/web/templates/layouts/_nav.html`, `templatetags/navigation.py` (`role_nav`)

**Issue**:
For a corrupt role, `available_sections()` returns `()`, but `_nav.html` still renders `<nav aria-label="Main"><ul></ul></nav>` (probe). This happens on the 403 page those users get. Screen readers announce an empty "Main navigation" landmark. Every valid role always has at least Home, so only the corrupt-role path is affected today.

**Suggested Fix**:
```django
{% load i18n %}{% if items %}<nav class="main-nav" aria-label="{% translate "Main" %}">
  …
</nav>{% endif %}
```

**Suggested Test**:
```python
def test_no_empty_navigation_landmark_for_a_corrupt_role(client):
    client.force_login(UserFactory(role="WIZARD"))

    assert 'class="main-nav"' not in client.get("/en/").content.decode()
```


**Resolution** (2026-10-23, DEV):
- Fix: `_nav.html` renders the `<nav>` only when it has items; the top bar stays
- Commit / change ref: `src/infrastructure/web/templates/layouts/_nav.html`
- Test evidence: `test_no_empty_navigation_landmark_for_a_corrupt_role` failed before the fix and passes now
- Status: ✅ Resolved

---

## Issue Summary

| # | ID | Severity | Category | File | Status |
|---|-----|----------|----------|------|--------|
| 1 | ISS-001 | 🟡 Medium | Accessibility | `static/css/layout.css` | Should Fix |
| 2 | ISS-002 | 🟢 Low | Correctness | `home/views.py:23` | Optional |
| 3 | ISS-003 | 🟢 Low | Accessibility | `layouts/_nav.html` | Optional |

**Summary**:
- Blockers: 0
- High: 0
- Medium: 1
- Low: 2

---

## What Was Done Well

1. ✅ **One registry, two views**: the menu and the cards are proven identical for every role, so a privilege-revealing link can't appear in one but not the other.
2. ✅ **Self-healing navigation**: unshipped features are skipped by route resolution, so later stories need no change here (2.2's "Learn" appears automatically).
3. ✅ **Database-safe shell**: the 1.1 hand-off is solved at the right layer (the layout tags), with real failure-injection tests for the 500, 404 and `/healthz` paths.
4. ✅ **Supply-chain care**: htmx came from the npm registry, its integrity was checked against the published hash, and the vendored body is byte-identical with its provenance recorded in the header.
5. ✅ **Contract conflicts surfaced, not hidden**: the `csrftoken`-on-error-pages conflict with Story 1.1 went to the owner, and the decision is recorded in the 1.1 story file and in the test comments.
6. ✅ **Translations reviewed by hand**: fuzzy guesses such as "Sign out" → "Autentificare" were caught and replaced.

---

## Approval Status

**Decision**: ⚠️ APPROVED WITH COMMENTS

**Reason**: no blockers and no high-severity issues. ISS-001 should be fixed before CYCLE-2's long editor pages; it's a one-line CSS rule. ISS-002 and ISS-003 are optional. The manual browser pass (screenshots, console CSP, keyboard, screen reader) remains open, as the self-review states.

**Next Steps**:
1. `aire-dev-remediate` for ISS-001 (recommended), with ISS-002 and ISS-003 optional.

---

## Sign-Off

**Reviewer**: REVIEWER Agent
**Date**: 2026-10-23
**Signature**: Approved with comments

---

# 🛠️ Remediation — 2026-10-23

**Developer**: DEV Agent
**Severity Scope**: 🟡 ISS-001 + 🟢 ISS-002 + 🟢 ISS-003 (all findings; scope confirmed by the user)
**Scenario**: Code Review
**Stories Affected**: 1.7 (plus a hand-off line in Story 1.10)
**Branch**: `main`

## Issues Remediated

| ID | Severity | Story | File | Summary | Resolution | Test Added |
|------|----------|-------|------|---------|------------|------------|
| ISS-001 | 🟡 Medium | 1.7→1.10 | `static/css/layout.css` | Sticky bar could hide focus | `scroll-padding-top` on `html`; 1.10 browser check | 1 ✅ |
| ISS-002 | 🟢 Low | 1.7 | `home/views.py` | Leading space lost the greeting | `split()` first word | 4 ✅ |
| ISS-003 | 🟢 Low | 1.7 | `layouts/_nav.html` | Empty nav landmark | Render only with items | 1 ✅ |

## Issues Deferred (with user consent)

None.

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `src/infrastructure/web/static/css/layout.css` | Modified | `html { scroll-padding-top }` |
| `src/infrastructure/web/home/views.py` | Modified | Whitespace-safe first name |
| `src/infrastructure/web/templates/layouts/_nav.html` | Modified | `{% if items %}` around `<nav>` |
| `tests/integration/web/home/test_shell_review_fixes.py` | New | 6 tests |
| `docs/plans/stories/epic-1-story-1.10-Foundation-E2E-Journeys.md` | Modified | Focus-not-obscured browser assertion |

## Patterns Applied

| Pattern | Where Applied | Notes |
|---------|---------------|-------|
| Accessibility §11.4 (WCAG 2.2 AA) | layout CSS, nav | Focus never hidden under the sticky bar; no empty landmarks |
| Tokens only (Story 1.5 rule) | `layout.css` | Offset from `--nav-height` + `--space-2` |

## Testing Summary

- **Targeted tests added**: 6 (5 failed before the fixes; 1 guards behaviour that already worked)
- **Full suite**: 1350/1350 passing (3 runs)
- **Coverage**: 100% (target ≥85%)
- **Gates** (each read from its own output line): `[ruff format] 166 files already formatted` · `[ruff check] All checks passed!` (after splitting the docstring and using `Path.read_text` in the new test) · `[mypy] Success: no issues found in 110 source files` · `[lint-imports] Contracts: 2 kept, 0 broken.` · `[migrations] No changes detected`

**Before the fix** (targeted):
```
FAILED test_shell_review_fixes.py::test_scroll_padding_clears_the_sticky_top_bar
FAILED test_shell_review_fixes.py::test_greeting_ignores_surrounding_whitespace[  Ana Pop]
FAILED test_shell_review_fixes.py::test_greeting_ignores_surrounding_whitespace[Ana\tPop]
FAILED test_shell_review_fixes.py::test_greeting_ignores_surrounding_whitespace[ Ana]
FAILED test_shell_review_fixes.py::test_no_empty_navigation_landmark_for_a_corrupt_role
5 failed, 1 passed in 0.20s
```

**After the fix** (full suite):
```
src/infrastructure/web/home/views.py                         11      0      0      0   100%
TOTAL                                                      1298      0    192      0   100%
1350 passed in 11.46s
```

**Real server**:
```
student "  Ana Maria Pop" → <h1 class="home__greeting">Bună, Ana!
GET /static/css/layout.css → html { scroll-padding-top: calc(var(--nav-height) + var(--space-2)); }
ERROR lines: 0
```

## Deviations from Report Suggestions

None.

## Lessons Learned

1. A sticky header needs a matching `scroll-padding-top`, or focus and `#targets` scroll under it.
2. `str.split()` without arguments is the safe "first word": `split(" ")` treats leading or repeated spaces as empty words.

## Next Steps

- [ ] Re-request code review (`aire-review-code`): optional (no 🔴 or 🟠 issues)
- [ ] Story 1.10 adds the focus-not-obscured browser assertion
