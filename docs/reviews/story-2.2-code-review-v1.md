# Code Review - Story 2.2: Catalogue & Subject Pages

**Date**: 2026-10-23
**Reviewed By**: REVIEWER Agent
**Review Number**: 1
**Review Mode**: INITIAL_REVIEW
**Status**: ⚠️ APPROVED WITH COMMENTS

---

## Review Metadata

**Previous Review**: None
**Previous Status**: N/A
**Files Changed Since Last Review**: All (first review). Reviewed at `main` @ `3d8d488` (story commit `415e3eb`, built in one go by an atomic story-agent)
**Severity Threshold Applied**: All

---

## Review Summary

**Components Reviewed**:
- `src/infrastructure/persistence/catalogue/queries.py` (78 lines: `SubjectDTO`, `GradeDTO`, `catalogue_overview`, `active_subject`)
- `src/infrastructure/web/catalogue/views.py` (70), `web/catalogue/urls.py`
- `templates/catalogue/index.html`, `_grade_section.html`, `subject.html`
- `static/css/catalogue.css`
- `config/urls.py`; RO/EN catalogues
- role-access matrix rows

**Lines of Code**: ~260 production lines, ~900 test lines
**Tests Reviewed**: Yes:
- `tests/integration/web/catalogue/`: `test_catalogue_queries.py`, `test_catalogue_pages.py`, `test_subject_page.py`, `test_catalogue_translations.py`
- matrix rows

**Coverage**: 100% overall; `queries.py` 30/30 statements, 2/2 branches; `views.py` 30/30

**Overall Assessment**: A clean, well-guarded read-only feature:
- Scope is enforced **inside** the query: an inactive subject is never loaded.
- Link permission comes only from the session role.
- Inactive and unknown subjects return the same 404.
- Every bilingual name goes through `localized()`.
- The heading outline is h1 → h2 per level → h3 per active card.
- The tests are unusually thorough: every inactive id, every active id for every role, forged query parameters, byte-identical 404s, a query count that doesn't grow with the catalogue, and the Student "Learn" entry from Story 1.7.

Two low findings:
- Student cards use the regular icon instead of the duotone the design tokens specify (ISS-001).
- Inconsistent Romanian wording for "subject" across the app (ISS-002).

---

## Evidence Verified (re-run by REVIEWER, 2026-10-23)

```
[ruff format]  174 files already formatted
[ruff check]   All checks passed!
[mypy]         Success: no issues found in 115 source files          (--no-incremental)
[lint-imports] Contracts: 2 kept, 0 broken.
[migrations]   No changes detected
src/infrastructure/persistence/catalogue/queries.py          30      0      2      0   100%
src/infrastructure/web/catalogue/views.py                    30      0      0      0   100%
TOTAL                                                      1362      0    194      0   100%
1486 passed in 12.72s
```

**Probes** (temporary test files, deleted afterwards; working tree clean):
```
Student GET /ro/subjects/<inactive>/                  -> 404
Student GET /ro/subjects/999999/                      -> 404
Student GET /ro/subjects/99999999999999999999999/     -> 404   (beyond SQLite INTEGER: no 500)
Student GET /ro/subjects/0/                           -> 404
Student GET /ro/subjects/abc/                         -> 404   (no route)
inactive vs unknown vs no-route 404 bodies: the only difference is the language switcher's
    <input type="hidden" name="next" value="/ro/subjects/<the requested id>/">
    i.e. the URL the visitor typed, so nothing about existence leaks (AC 2 holds in substance).
Catalogue page, total queries incl. session + user: 4  (the 2 catalogue queries of AC 1 + 2 auth)
Forged ?is_active=1&role=TEACHER on an inactive id -> 404; forged ?can_open=0&role=TEACHER on the catalogue -> still 3 links
```
The real-server evidence in `docs/stories-implemented/story-2.2-review.md` (4 roles × RO/EN; 3 links + 108 tiles; 10×h2, 3×h3; 404/403/302 as specified; 0 inline script/style; 0 ERROR lines) was re-read and matches the code.

---

## Acceptance Criteria Check

| AC | Result | Evidence |
|----|--------|----------|
| 1 `catalogue_overview` ordered DTOs in exactly 2 queries | ✅ | `queries.py:38-54`; `test_overview_uses_two_queries`, `test_query_count_stays_two_when_subjects_are_added` |
| 2 `active_subject` raises `NotFound` for unknown **or** inactive; identical 404 | ✅ | `queries.py:57-78` (filter inside the query); `test_inactive_and_unknown_raise_the_same_error`, `test_inactive_and_unknown_404_pages_are_byte_identical`; probe above |
| 3 Routes, guards, GET/HEAD only | ✅ | `views.py:44-70`, `urls.py`; method tests; URL-coverage test passes |
| 4 10 labelled sections, h2, active `ui_card` (link only with `lessons:view`, otherwise "Available to students"), inactive `ui_disabled_tile`, "Pilot" label | ✅ (see ISS-001) | `_grade_section.html`; section/heading/card/tile tests |
| 5 No `<a>` to any inactive subject | ✅ | `test_no_link_to_any_inactive_subject`, forged-param tests |
| 6 Subject page: header + breadcrumb (last `aria-current`) + empty state | ✅ | `subject.html`, `views.py:35-41`; breadcrumb tests (RO/EN) |
| 7 Empty catalogue → empty state, 200 | ✅ | `test_empty_catalogue_shows_empty_state` |
| 8 Names via `{% localized %}`; EN English, RO with diacritics | ✅ | templates; `test_names_are_localized`, translation page tests |
| 9 Matrix rows | ✅ | `test_role_access_matrix.py` |
| 10 Subject access: Student 200/404, staff 403, anonymous 302 | ✅ | `test_subject_page.py` (every active and inactive id; role denial before the existence check) |
| 11 Student "Learn" in the main navigation | ✅ | `test_student_menu_and_home_card_link_to_the_catalogue`, `test_learn_is_the_current_page_on_the_catalogue`, `test_other_roles_menus_have_no_catalogue_entry` |
| 12 RO/EN for the six strings | ✅ (see ISS-002) | `test_catalogue_translations.py` (RO text, EN = msgid, not fuzzy) |

---

## Checklist Results

### Correctness
- [x] ✅ Ordered, complete catalogue; only grade 2 CLR/MEM/EN active
- [x] ✅ Out-of-range and non-numeric ids → 404, never 500
- [x] ✅ Pure reads (write-capture tests)

### Pattern Adherence
- [x] ✅ ADR-005: read-only pages use a query service returning frozen DTOs; no ORM objects in templates
- [x] ✅ ADR-006: bilingual fields only through `localized()`
- [x] ✅ §6.3: scope inside the query
- [x] ✅ §11.2: reuses `ui_card` (level 3), `ui_disabled_tile`, `ui_page_header`, `ui_empty_state`; feature CSS tokens only, linked through `{% block extra_css %}`
- [x] ⚠️ Design token: duotone icon on student cards (ISS-001)

### Testing
- [x] ✅ Exhaustive id coverage (every active and inactive subject, every role), forged parameters, query counts, identical 404s, heading outline, menu integration
- [x] ✅ Coverage 100%

### Documentation
- [x] ✅ Docstrings state the scope and 404 rationale; the self-review records the planner decisions and the honest "no browser" gap

### Security
- [x] ✅ Role denial (403) comes before the existence check for staff, so staff can't probe existence either
- [x] ✅ Link permission from the session role only; activity only from the DB flag
- [x] ✅ No inline script/style; output escaped

### Performance
- [x] ✅ 2 queries for the whole catalogue regardless of size; 1 query for a subject page

### SOLID / Anti-Monolith
- [x] ✅ Query service, views and templates separated; CYCLE-2 extension point marked in `subject.html`

---

## Issues Found

### ISS-001: Student catalogue cards use the regular icon; the design tokens specify duotone 🟢 Low

**Category**: Pattern (design tokens)
**File**: `templates/catalogue/_grade_section.html` (the `ui_card … icon="book-open"` calls); `templatetags/ui_molecules.py` (`ui_card`); `components/card.html`
**Pattern Reference**: Story 2.2 Design Tokens ("icon Phosphor `book-open` 32px (duotone for student)"); UI/UX spec: student theme uses duotone icons

**Issue**:
`ui_card` renders its icon with `{% ui_icon icon 24 %}`, always regular. The build agent recorded this as a deviation because the card primitive (Story 1.6) has no way to choose the variant. The views already compute `icon_variant` (duotone for students), so only the card can't use it. The same gap exists on the Story 1.7 home cards.

**Suggested Fix**: let the card take the variant, defaulting to regular:
```python
def ui_card(title, body="", href=None, icon=None, meta="", level=2, icon_variant="regular"):
    if icon_variant not in ICON_VARIANTS:
        raise ValueError(f"Unknown icon variant: {icon_variant}")
    return {..., "icon_variant": icon_variant}
```
```django
{% if icon %}{% ui_icon icon 24 icon_variant %}{% endif %}
```
Then pass `icon_variant=icon_variant` in `_grade_section.html` and in Story 1.7's `home/_cards.html`, and add a test that a student catalogue card references `#book-open-duotone` while a teacher's references `#book-open`.

---

### ISS-002: "Subject" is "materie" on the student home card but "disciplină" in the catalogue 🟢 Low

**Category**: Documentation / i18n consistency
**File**: `src/infrastructure/i18n/locale/ro/LC_MESSAGES/django.po` (`"Choose a subject"` → "Alege o materie", Story 1.7; `"Grades and subjects"` → "Clase și discipline", this story)

**Issue**:
A student reads "Alege o materie" on the "Learn" card and then lands on a page titled "Clase și discipline". Both words are correct Romanian ("disciplină" is the curriculum term, "materie" the everyday one), but switching terms between two consecutive screens is confusing for 7-year-olds, and later stories (CYCLE-2/3) will add many more "subject" strings. Note also that "Clase" doesn't strictly cover Grădiniță and Clasa pregătitoare.

**Suggested Fix**: pick one term for the student-facing UI and record it in a short glossary (for example in the i18n section of the patterns doc or the README "Translations" section), for example:
```
subject  → "materie" (student/parent UI), "disciplină" only in admin/teacher curriculum contexts
grade/level → "nivel" when K and P are included ("Niveluri și materii"), "clasă" for 1–8
```
Then align `"Grades and subjects"` (and any future entries) with it. This is a product wording decision, so confirm with the owner.

---

## Issue Summary

| # | ID | Severity | Category | File | Status |
|---|-----|----------|----------|------|--------|
| 1 | ISS-001 | 🟢 Low | Pattern | `_grade_section.html` / `ui_card` | Optional |
| 2 | ISS-002 | 🟢 Low | i18n | `ro/django.po` | Optional (owner wording decision) |

**Summary**:
- Blockers: 0
- High: 0
- Medium: 0
- Low: 2

---

## What Was Done Well

1. ✅ **Scope in the query**: `filter(pk=…, is_active=True)`, so an inactive subject is never even loaded, and inactive and unknown subjects raise the very same error.
2. ✅ **No existence oracle**: staff get 403 before any lookup; for students the 404 pages are byte-identical apart from the requested URL itself.
3. ✅ **Robust routing**: the `int` converter keeps non-numeric ids out, and an id beyond SQLite's integer range still gives a clean 404.
4. ✅ **Exhaustive tests**: every seeded id is tested for every role, plus forged parameters, write capture, query growth and heading outline.
5. ✅ **Seamless integration**: the Student "Learn" entry appeared through Story 1.7's registry with no change to the shell, and it is marked as the current page on the catalogue.

---

## Approval Status

**Decision**: ⚠️ APPROVED WITH COMMENTS

**Reason**: no blockers and no high- or medium-severity issues. ISS-001 is a small primitive extension (it also benefits Story 1.7's home cards). ISS-002 needs an owner wording decision. Screenshots and the manual Tab walk remain open, as the self-review states.

**Next Steps**:
1. Optional `aire-dev-remediate` for ISS-001 (and ISS-002 once the wording is chosen); otherwise continue with the CI pipeline and Wave 5.

---

## Sign-Off

**Reviewer**: REVIEWER Agent
**Date**: 2026-10-23
**Signature**: Approved with comments
