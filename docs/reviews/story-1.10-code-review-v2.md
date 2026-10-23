# Code Review - Story 1.10: Foundation E2E Journeys

**Date**: 2026-10-23
**Reviewed By**: REVIEWER Agent
**Review Number**: 2
**Review Mode**: NEW_CHANGES
**Status**: ✅ APPROVED

---

## Review Metadata

**Previous Review**: `docs/reviews/story-1.10-code-review-v1.md`
**Previous Status**: ⚠️ APPROVED WITH COMMENTS (0 🔴 · 0 🟠 · 1 🟡 · 0 🟢), remediated (ISS-001 ✅ Resolved)
**Files Changed Since Last Review**: `tests/e2e/test_dialog_keyboard.py` (remediation commit `f81299d`), plus docs. `git diff 576b808 f81299d -- src/ pyproject.toml` is empty.
**Severity Threshold Applied**: 🔴 Blocker + 🟠 High only, in the changed files. I also verified the previous issue.

---

## Review Summary

**Components Reviewed**: `test_focus_is_never_hidden_under_the_sticky_top_bar` (`tests/e2e/test_dialog_keyboard.py:43-65`) and the removal of `TOP_BAR_HEIGHT`.
**Lines of Code**: +20 / −10 test lines
**Tests Reviewed**: Yes
**Coverage**: 100% for `src/` (default run)

**Overall Assessment**: The rewrite does what v1 ISS-001 asked. The journey now puts a field inside the viewport but under the sticky bar, and moves keyboard focus onto it. It reads the bar's edge from the rendered banner and asserts a precondition, so it can't pass vacuously. I confirmed independently that it fails without `scroll-padding-top` and passes with it.

---

## Previous Issue Verification

| ID | Severity | Fix verified | Evidence |
|----|----------|--------------|----------|
| ISS-001 | 🟡 Medium | ✅ Resolved | REVIEWER red/green re-run below. Matches the suggested fix, plus a precondition assertion (a sound deviation, logged in the Remediation Section) |

### REVIEWER red/green re-run

I edited `layout.css` locally twice, restored it from a backup, and checked that `git status --short src/` was empty afterwards.

```
--- layout.css:5 rule removed
E       assert 9.953125 >= (0 + 65)
1 failed, 2 deselected in 0.98s
--- html { scroll-padding-top: 0; } (explicit)
E       assert 9.953125 >= (0 + 65)
1 failed, 2 deselected in 0.97s
--- rule restored
(full e2e run below: 17 passed)
```

### Evidence Verified (re-run by REVIEWER, 2026-10-23)

```
[e2e x3]          17 passed, 1497 deselected in 7.17s / 6.95s / 6.93s
[default + cov]   1497 passed, 17 deselected in 13.00s | Total coverage: 100.00%
[ruff format]     187 files already formatted
[ruff check]      All checks passed!
[mypy]            Success: no issues found in 115 source files   (--no-incremental)
[lint-imports]    Contracts: 2 kept, 0 broken.
[makemigrations]  No changes detected
```

---

## Checklist Results (changed file)

### Correctness
- [x] ✅ **The precondition** (`under_bar["y"] < bar bottom`) proves the scenario is set up before the key press.
- [x] ✅ **Real focus movement:** Shift+Tab moves from Field 21 to Field 20 (`expect(field_20).to_be_focused()`), so the scroll is caused by keyboard focus, not by a script.
- [x] ✅ **The bar's edge comes from the page:** `get_by_role("banner")` measures 65px. The removed constant (64) was already wrong by the 1px border.

### Pattern Adherence (§12.5, §12.6)
- [x] ✅ **Locators:** role and label only. `page.evaluate` is used only to scroll, never to locate.
- [x] ✅ **No waits:** no `sleep` and no `wait_for_timeout`.
- [x] ✅ **The test can fail:** red without the behaviour, green with it.

### Documentation
- [x] ✅ **Comment:** it explains why only `scroll-padding-top` makes the test pass, and links back to v1 ISS-001.
- [x] ✅ **Other docs:** the self-review hand-off row is corrected, and the report has its banner, resolution and Remediation Section.

### Security / Performance / SOLID
- [x] ✅ **No change in these areas:** test-only, about 1 s for the test, single-purpose.

---

## Issues Found

None at 🔴 or 🟠 in the changed files.

## Issue Summary

| # | ID | Severity | Category | File | Status |
|---|-----|----------|----------|------|--------|
| — | — | — | — | — | — |

**Summary**:
- Blockers: 0
- High: 0
- Medium / Low: not assessed (NEW_CHANGES threshold)

---

## What Was Done Well

1. ✅ **Red/green proof for a test-only fix:** the CSS was removed locally, the test failed, and the CSS was restored with `src/` verified clean.
2. ✅ **Precondition assertion:** a future layout change that moves the field out from under the bar breaks the test loudly instead of making it vacuous.
3. ✅ **Measured, not assumed:** the bar's geometry is read from the page, which removed a constant that was already wrong.

---

## Approval Status

**Decision**: ✅ APPROVED

**Reason**: No blockers or high issues. v1 ISS-001 is fixed and independently verified.

**Next Steps**:
1. CYCLE-1 demo and sign-off (`uv run pytest -m e2e --headed`).
2. Push when you're ready (the CYCLE-1 commits on `main` are local only).

---

## Sign-Off

**Reviewer**: REVIEWER Agent
**Date**: 2026-10-23
**Signature**: Approved
