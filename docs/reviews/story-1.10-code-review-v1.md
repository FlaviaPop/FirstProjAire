# Code Review - Story 1.10: Foundation E2E Journeys

> ## 🛠️ Remediation Status: ✅ Resolved
> - **Remediated**: 2026-10-23 by DEV Agent
> - **Fixed**: 1 issue(s) — 🔴 0 / 🟠 0 / 🟡 1 / 🟢 0
> - **Deferred (with user consent)**: 0
> - **Tests**: 1497/1497 passing (default) + 17/17 e2e ×3 | **Coverage**: 100% | **Linter**: clean
> - **Scenario**: Code Review

**Date**: 2026-10-23
**Reviewed By**: REVIEWER Agent
**Review Number**: 1
**Review Mode**: INITIAL_REVIEW
**Status**: ⚠️ APPROVED WITH COMMENTS

---

## Review Metadata

**Previous Review**: None
**Previous Status**: N/A
**Files Changed Since Last Review**: All (first review). Reviewed at `main` @ `27c7f66` (story commit, Dev 1, one-by-one).
**Severity Threshold Applied**: All

---

## Review Summary

**Components Reviewed**:
- **Harness:** `tests/e2e/conftest.py` (136 lines: options hook, collection marker, `_seeded_snapshot`, `_e2e_environment`, `base_url`, console helpers, `login`/`logout`).
- **Test-only routing:** `tests/e2e/urls.py` and `tests/e2e/templates/e2e/dialog.html`.
- **Journeys:**
  - `test_admin_journey.py`, `test_role_logins.py`, `test_language.py`, `test_lockout.py`;
  - `test_access_denied.py`, `test_error_pages.py`, `test_dialog_keyboard.py`, `test_catalogue_journey.py`.
- **Docs:** `README.md` (the "End-to-end tests" section) and `docs/stories-implemented/story-1.10-review.md`.

**Lines of Code**: about 470 test lines. No production lines: `git diff c7d5644..27c7f66 -- src/ pyproject.toml` is empty.
**Tests Reviewed**: Yes. The story is tests, so this review checks that each journey can actually fail, using mutation probes.
**Coverage**: 100% for `src/` in the default run. The e2e suite isn't counted, by design.

**Overall Assessment**: A clean, well-documented harness. The journeys map one-to-one to the 13 ACs, use only role, label and text locators, and are stable and order-independent at about 7 s for the suite. The serialized-rollback fix for Playwright's per-greenlet connection is a real root-cause fix, and it is explained where it lives. Mutation probes confirmed that the CSP listener, the modal-focus check and the alert-focus check each fail when their behaviour is broken. One check doesn't: the focus-not-obscured journey (the hand-off from 1.7 ISS-001) still passes with `scroll-padding-top` removed (ISS-001).

---

## Evidence Verified (re-run by REVIEWER, 2026-10-23)

```
[e2e x3]          17 passed, 1497 deselected in 7.01s / 6.99s / 7.35s
[e2e reversed]    17 passed in 7.24s          (files in reverse order)
[e2e isolated]    catalogue 1 passed · lockout 1 passed · admin 1 passed · admin+admin+catalogue 2 passed
[default + cov]   1497 passed, 17 deselected in 13.72s | Total coverage: 100.00%
[ruff format]     187 files already formatted
[ruff check]      All checks passed!
[mypy]            Success: no issues found in 115 source files   (--no-incremental)
[lint-imports]    Contracts: 2 kept, 0 broken.
[makemigrations]  No changes detected
```

### Mutation probes

The probes were a scratch file outside the repo, loading `tests/e2e/conftest.py` as a plugin.

| Probe | Mutation | Observed | Journey would… |
|---|---|---|---|
| P1 | Inject an inline `<script>` | console: "Executing inline script violates the following Content Security Policy directive 'script-src 'self''…", matched by the `"Content Security Policy"` filter | ✅ fail (AC 11 guard works) |
| P3 | `showModal()` replaced by `show()` (non-modal) | Tab trail: dialog button → `field-1` → `field-2` … | ✅ fail (focus escapes) |
| P4 | None (real modal) | Tab trail: OK → `<body>` → Cancel → OK → `<body>` …; dialog still open | confirms the recorded deviation (document stop) |
| P6 | Focus not moved to `<main>` on alert dismissal | `activeElement` = `BODY`, id `''` | ✅ fail (1.6 ISS-002 guard works) |
| P2 | `scroll-padding-top: 0px` | Field 1 lands at y = **328.8** (with the rule: 291.8); assertion `y >= 64` still holds | ❌ **still passes**: see ISS-001 |
| P7 | Field 20 placed under the bar (y = 10), Field 21 focused, Shift+Tab | with the rule: y = **386.0**; with `0px`: y = **10.0** (hidden under the 65px banner) | ✅ would fail: the suggested fix |
| Deliberate break (self-review) | `aria-label="Account menu"` removed | 4/4 role journeys fail; trace and screenshot kept | ✅ (re-confirmed by the self-review evidence and screenshot) |

---

## Checklist Results

### Correctness
- [x] ✅ **Journeys follow the ACs:** each journey does what its AC says (13/13 traced below).
- [x] ✅ **Isolation:**
  - each test gets a fresh transactional DB with the seeded catalogue restored;
  - the audit triggers are present during the journey and dropped only for the flush;
  - verified by the isolated and reversed runs.
- [x] ✅ **Error paths:**
  - `_seeded_snapshot` asserts loudly when the DB wasn't serialized;
  - `logout()` is idempotent with respect to the `<details>` toggle.
- [x] ✅ **No races:** Playwright auto-wait and `expect` everywhere; no `sleep` and no `wait_for_timeout`.
- [x] ⚠️ **Hand-off 1.7 ISS-001 isn't actually guarded** (ISS-001).

### Pattern Adherence (§12.5, §12.1, §14)
- [x] ✅ **Locators:** only `get_by_role`, `get_by_label` and `get_by_text`. The two `locator("html")` and `locator("body")` calls read `lang` and the theme class, as the story's own example does; no CSS-class or XPath selectors.
- [x] ✅ **`-m e2e` and async:** journeys run against `live_server` under `-m e2e`, and `DJANGO_ALLOW_ASYNC_UNSAFE` is set only in the e2e conftest, only for e2e sessions.
- [x] ✅ **Routing:** the test-only page is only in `tests/e2e/urls.py`, and `config.urls` is untouched.
- [x] ✅ **Shared code reused:** the audit trigger SQL is imported from the migration, not copied; `PASSWORD` mirrors the factory default.
- [x] ✅ **Size:** every file is ≤ 136 lines and every function is short.
- [x] ⚠️ **Hard-coded top-bar height:** `TOP_BAR_HEIGHT = 64` mirrors the token, but the rendered banner is 65px (part of ISS-001).

### Testing
- [x] ✅ **Every AC has a journey**, and each journey has explicit assertions.
- [x] ✅ **Stable:** 3 green runs plus reversed and isolated orders.
- [x] ✅ **Default run unaffected:** 1497 passed, 17 deselected.
- [x] ✅ **Failure artefacts:** traces and screenshots are kept on failure and `test-results/` is git-ignored.
- [x] ⚠️ **One journey isn't sensitive** to the regression it targets (ISS-001).

### Documentation
- [x] ✅ **Module docstrings** name the AC or hand-off each journey covers. The non-obvious harness choices (trigger drop, greenlet connection, `<details>` toggle, admin label regex) are commented.
- [x] ✅ **README** has the install, run, `--headed` and `show-trace` commands.
- [x] ✅ **Self-review** has the AC map, the deviations and the timings.
- [x] ⚠️ **Self-review overstates one item:** it marks "Hand-off 1.7 ISS-001" as proven, which probe P2 contradicts (fix with ISS-001).

### Security
- [x] ✅ **No secrets:** the only passwords are test fixtures (`pilot-pass-123`, `Pilot-Journey-2026!`), not real values.
- [x] ✅ **CSP checked:** any CSP violation fails the journey, the lockout journey's second (admin) context is watched too, and the guard was proven by probe P1.
- [x] ✅ **Role boundaries:** 403 for the three non-admin roles on `/ro/admin/`, the anonymous redirect, and inactive subject → 404 are all exercised end to end.

### Performance
- [x] ✅ **Fast:** about 7 s in total. The serialization cost is paid once per e2e session only.

### SOLID / Anti-Monolith / Maintainability
- [x] ✅ **Small, single-purpose pieces:** one file per area, shared helpers in the conftest, and no cross-journey coupling. Each journey creates its own data.
- [x] ✅ **Private Django API, but guarded:** the harness relies on Django internals (`_test_serialized_contents`, `deserialize_db_from_string`). The reliance is documented, and if the attribute disappears in a Django upgrade the `_seeded_snapshot` assertion fails loudly rather than silently.

---

## AC Verification

| AC | Verdict | Evidence |
|----|---------|----------|
| 1 Install documented; `-m e2e` only e2e; default excludes | ✅ | README; 17 selected / 1497 deselected and the reverse |
| 2 Role/label/text locators only | ✅ | all journeys (see Pattern Adherence) |
| 3 Admin: 3 accounts, link, duplicate error, audit ×3 / ×1 | ✅ | `test_admin_journey.py:44-53` (`parent_linked` ×1 also proves the duplicate wasn't saved) |
| 4 Roles: URL, theme, exact nav, full name, sign out | ✅ | `test_role_logins.py:28-36` |
| 5 EN switch persists across sign-out/in | ✅ | `test_language.py`; login redirects to `/<preferred_language>/` (`accounts/views.py:25`), so landing on `/en/` proves the stored preference |
| 6 Lockout, correct password refused, admin unlock, sign-in | ✅ | `test_lockout.py:16-36` |
| 7 Access denied ×3; anonymous → login | ✅ | `test_access_denied.py` (403 status + RO heading) |
| 8 404 RO/EN with back-home link | ✅ | `test_error_pages.py` (status, `lang`, heading, link) |
| 9 Dialog: Enter opens, Tab stays, Escape closes, focus returns | ✅ | `test_dialog_keyboard.py:10-29`; probes P3/P4 (document stop is native modal behaviour, recorded) |
| 10 Catalogue: 3 links, unavailable tile, inactive URL 404, subject shell | ✅ | `test_catalogue_journey.py` |
| 11 `console_errors` everywhere; CSP fails | ✅ | every test; probe P1 |
| 12 Trace + screenshot on failure | ✅ | `conftest.py:38-41`; deliberate-break evidence |
| 13 < 3 min, recorded | ✅ | ~7 s |
| Hand-off 1.6 ISS-002 | ✅ | `test_dialog_keyboard.py:32-41`; probe P6 |
| Hand-off 1.7 ISS-001 | ⚠️ | `test_dialog_keyboard.py:44-56` passes without the fix it guards (ISS-001) |

---

## Issues Found

### ISS-001: Focus-not-obscured journey passes even without `scroll-padding-top` 🟡 Medium

**Category**: Testing
**File**: `tests/e2e/test_dialog_keyboard.py:44-56` (and `:7`)
**Pattern Reference**:
- Story 1.10, the hand-off from Story 1.7 review v1 ISS-001 (WCAG 2.4.11);
- `docs/architecture/design/01-patterns-and-standards-greenfield.md` §12.6 ("DON'T write assertion-free tests"; by extension, tests that can't fail);
- `layout.css:5`.

**Issue**:
The journey focuses Field 40 and presses Shift+Tab 39 times up to Field 1. Field 1 sits about 329px from the top of the document. When Chromium moves keyboard focus to an off-screen element, it scrolls the page all the way up, so Field 1 ends up well below the bar whether or not the page has the `scroll-padding-top` fix.

Probe P2 measured this:
- with the rule, y = 291.8;
- with `scroll-padding-top: 0px`, y = 328.8.

Both satisfy `y >= 64`. If the 1.7 ISS-001 fix were deleted, the journey would stay green, so the WCAG 2.4.11 regression is still only guarded by the static CSS test.

There's a smaller related problem. `TOP_BAR_HEIGHT = 64` copies `--nav-height`, but the rendered banner is 65px tall (it has a bottom border). A hard-coded constant can drift from the real bar.

**Current Code**:
```python
TOP_BAR_HEIGHT = 64  # tokens.css --nav-height
...
    page.get_by_label("Field 40", exact=True).focus()  # bottom of a page taller than the viewport

    for _ in range(39):
        page.keyboard.press("Shift+Tab")

    field_1 = page.get_by_label("Field 1", exact=True)
    expect(field_1).to_be_focused()
    box = field_1.bounding_box()
    assert box is not None
    assert box["y"] >= TOP_BAR_HEIGHT, box
```

**Suggested Fix**:
Put a field inside the viewport but under the sticky bar, then move keyboard focus onto it. Only `scroll-padding-top` makes Chromium scroll it out from under the bar. Read the bar's height from the page instead of copying the token.

Probe P7 measured this version:
- with the rule, y = 386.0, so the test passes;
- with `0px`, y = 10.0, so the test fails.

```python
def test_focus_is_never_hidden_under_the_sticky_top_bar(page: Page, base_url, console_errors):
    # Story 1.7 review v1 ISS-001 (WCAG 2.4.11): a field sitting under the sticky bar must be
    # scrolled clear of it when keyboard focus reaches it (only scroll-padding-top does that).
    page.goto(f"{base_url}/en/e2e/dialog/")
    bar = page.get_by_role("banner").bounding_box()
    assert bar is not None
    page.get_by_label("Field 21", exact=True).focus()
    page.evaluate(  # put Field 20 inside the viewport, under the bar
        "window.scrollBy(0, document.getElementById('field-20').getBoundingClientRect().top - 10)"
    )

    page.keyboard.press("Shift+Tab")

    field_20 = page.get_by_label("Field 20", exact=True)
    expect(field_20).to_be_focused()
    box = field_20.bounding_box()
    assert box is not None
    assert box["y"] >= bar["y"] + bar["height"], (box, bar)
```

Optionally keep the existing long Shift+Tab walk as a second test, but don't count it as the regression guard. Also prove the new version is sensitive in the remediation evidence: set `document.documentElement.style.scrollPaddingTop = '0px'` in a scratch run, or comment the rule out locally, and show the test fails. Update the self-review row for "Hand-off 1.7 ISS-001".

**Why This Matters**: This journey is the only browser-level evidence for a WCAG 2.2 AA criterion that the CYCLE-1 sign-off relies on. Right now it would stay green through exactly the regression it was written to catch.

**Resolution** (2026-10-23, DEV):
- **Fix:** the journey was rewritten as suggested.
  - Field 21 is focused and Field 20 is scrolled to sit inside the viewport but under the bar, then Shift+Tab focuses Field 20.
  - It asserts Field 20's top is at or below the banner's bottom edge, read from `get_by_role("banner")`. `TOP_BAR_HEIGHT = 64` is removed; the banner is actually 65px tall.
  - A **precondition assertion** checks that Field 20 really is under the bar before the key press, so the test can't pass vacuously.
  - The old Field 40 → Field 1 walk was dropped, since it guarded nothing.
- **Change ref:** `tests/e2e/test_dialog_keyboard.py:43-65`. No `src/` change.
- **Test evidence:**
  - **Red, with the rule removed locally** (`layout.css:5` commented out): `AssertionError … assert 9.953125 >= (0 + 65)` → 1 failed. The CSS was restored from a backup afterwards (`git status --short src/` → empty).
  - **Green, with the rule restored:** `test_dialog_keyboard.py` 3 passed. Full e2e 17/17 ×3.
- Status: ✅ Resolved

---

## Issue Summary

| # | ID | Severity | Category | File | Status |
|---|-----|----------|----------|------|--------|
| 1 | ISS-001 | 🟡 Medium | Testing | `tests/e2e/test_dialog_keyboard.py:44-56` | Should Fix |

**Summary**:
- Blockers: 0
- High: 0
- Medium: 1
- Low: 0

---

## What Was Done Well

1. ✅ **Root-cause harness fixes, not workarounds:**
   - the trigger SQL is imported from the migration;
   - serialized rollback is made to work under Playwright's greenlet-local connection;
   - the error handlers are re-exported so the production 403 and 404 templates render.
2. ✅ **The journeys can fail:** the deliberate break plus probes P1, P3 and P6 show the CSP, modal and alert-focus checks catch real regressions.
3. ✅ **Strong assertions:**
   - exact nav lists;
   - `to_have_count(3)` for grade 2;
   - status codes on 403 and 404;
   - `parent_linked ×1`, which also proves the duplicate link was refused at the data level.
4. ✅ **Deviations recorded in the self-review:** the native-dialog document stop, the test-page URL and the EN default.
5. ✅ **Fast and stable:** about 7 s, order-independent, with nothing written to `test-results/` on a green run.

---

## Approval Status

**Decision**: ⚠️ APPROVED WITH COMMENTS

**Reason**: No blocker or high issues. One medium testing issue: the focus-not-obscured hand-off isn't really guarded. It should be fixed before the CYCLE-1 sign-off uses this suite as accessibility evidence.

**Next Steps**:
1. `aire-dev-remediate` for ISS-001: rewrite the journey as suggested, and show red with the rule removed and green with it restored.
2. CYCLE-1 demo and sign-off with `uv run pytest -m e2e --headed`.

---

## Sign-Off

**Reviewer**: REVIEWER Agent
**Date**: 2026-10-23
**Signature**: Approved with comments

---

# 🛠️ Remediation — 2026-10-23

**Developer**: DEV Agent
**Severity Scope**: 🟡 Medium (all reported issues; the user confirmed the scope)
**Scenario**: Code Review
**Stories Affected**: 1.10

## Issues Remediated

| ID | Severity | Story | File:Line | Summary | Resolution | Test Added |
|------|----------|-------|-----------|---------|------------|------------|
| ISS-001 | 🟡 Medium | 1.10 | `tests/e2e/test_dialog_keyboard.py:43-65` | Focus-not-obscured journey passed without `scroll-padding-top` | Field placed under the bar, then focused by Shift+Tab; banner edge read from the page; precondition assertion | rewritten test ✅ (red without the rule, green with it) |

## Issues Deferred (with user consent)

None.

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `tests/e2e/test_dialog_keyboard.py` | Modified | Sensitive focus-not-obscured journey; `TOP_BAR_HEIGHT` constant removed |
| `docs/stories-implemented/story-1.10-review.md` | Modified | Hand-off 1.7 ISS-001 row now cites the red/green evidence |
| `docs/reviews/story-1.10-code-review-v1.md` | Modified | Banner, resolution block, this section |
| `docs/status.md` | Modified | Remediation entry |

## Patterns Applied

| Pattern | Where Applied | Notes |
|---------|---------------|-------|
| E2E locators (§12.5) | `get_by_role("banner")`, `get_by_label("Field 20/21", exact=True)` | `page.evaluate` is used only to scroll, not to locate |
| Tests that can fail (§12.6) | precondition assertion + red run | the test fails when the behaviour it guards is removed |

## Testing Summary

- **Targeted tests changed**: 1 (rewritten)
- **Full suite**: 1497/1497 passing in the default run; e2e 17/17 in 3 consecutive runs
- **Coverage**: 100% (target ≥85%)

**Test Output**:
```
--- RED (layout.css:5 scroll-padding-top removed locally; restored afterwards, src/ unchanged)
E       AssertionError: ({'x': 262.578125, 'y': 9.953125, 'width': 153, 'height': 21}, {'x': 0, 'y': 0, 'width': 1280, 'height': 65})
E       assert 9.953125 >= (0 + 65)
FAILED tests/e2e/test_dialog_keyboard.py::test_focus_is_never_hidden_under_the_sticky_top_bar[chromium]
1 failed, 2 deselected in 0.99s
--- old test with the same CSS removed (the defect): 1 passed, 2 deselected in 0.97s
--- GREEN (rule restored)
tests/e2e/test_dialog_keyboard.py: 3 passed in 1.34s
e2e run 1: 17 passed, 1497 deselected in 6.94s
e2e run 2: 17 passed, 1497 deselected in 7.04s
e2e run 3: 17 passed, 1497 deselected in 6.94s
default:   1497 passed, 17 deselected in 12.81s | Total coverage: 100.00%
[ruff format]     187 files already formatted
[ruff check]      All checks passed!
[mypy]            Success: no issues found in 115 source files
[lint-imports]    Contracts: 2 kept, 0 broken.
[makemigrations]  No changes detected
```

## Deviations from Report Suggestions

- **Precondition assertion added:** `under_bar["y"] < bar bottom` before Shift+Tab. If the page layout changes so the field is no longer under the bar, the test fails at setup instead of passing vacuously.
- **Old walk not kept as a second test:** the report made this optional. It proves nothing beyond the new test, so it was dropped.

## Lessons Learned

1. A regression test is only proven by watching it fail without the fix. Chromium's focus scrolling moves off-screen targets fully into view, so "scroll up to the top" can't show the sticky-bar problem; "already in the viewport, under the bar" can.

## Next Steps

- [ ] Re-request code review (`aire-review-code`): optional, since no 🔴 was fixed
- [ ] CYCLE-1 demo and sign-off (`uv run pytest -m e2e --headed`)
