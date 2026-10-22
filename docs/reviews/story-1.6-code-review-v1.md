# Code Review - Story 1.6: Molecule Primitives (+ Story 1.3 review ISS-004)

**Date**: 2026-10-22
**Reviewed By**: REVIEWER Agent
**Review Number**: 1
**Review Mode**: INITIAL_REVIEW
**Status**: ⚠️ APPROVED WITH COMMENTS

---

## Review Metadata

**Previous Review**: None
**Previous Status**: N/A
**Files Changed Since Last Review**: All (first review). Reviewed at `main` @ `1a923de` (story commit `3cf8fa9`, built in one go: decompose-lead → 3 component workers → integrator)
**Severity Threshold Applied**: All

---

## Review Summary

**Components Reviewed**:
- **Template tags:** `templatetags/ui.py`, molecule section lines 181–398: `Cell`, `_href`, `_field_context`, `ui_field`, `ui_field_pair`, `ui_alert`, `ui_card`, `ui_disabled_tile`, `ui_empty_state`, `ui_page_header`, `ui_confirm_dialog`, `ui_dialog_trigger`, `_cell`, `ui_table`
- **Component templates (10):** `form_field`, `field_pair`, `alert`, `card`, `disabled_tile`, `empty_state`, `page_header`, `confirm_dialog`, `dialog_trigger`, `table`
- **Component stylesheets (8)**, plus the `--color-backdrop` token in `tokens.css`
- **`static/js/ui.js`** (54 lines)
- **Pages:** `layouts/base.html` (owner decision: component CSS links); styleguide `views.py`, `index.html`, `_molecules.html`, `styleguide.css`
- **Translations:** RO/EN catalogues
- **1.3 ISS-004:** `tests/integration/web/test_url_protection.py` (the DEBUG-only route walk)

**Lines of Code**: ~1,080 added (tags ~220, templates ~60, CSS ~330, JS 54, styleguide ~150, tests ~1,000)
**Tests Reviewed**: Yes:
- `test_molecules.py`, `test_molecules_layout.py`, `test_molecule_assets.py`
- `test_base_layout_styles.py`, `test_inline_script.py`
- the updated `test_atoms.py`, `test_styleguide.py`, `test_design_assets.py`, `test_url_protection.py`

**Coverage**: 100% overall; `ui.py` 181/181 statements, 52/52 branches

**Overall Assessment**: Strong work that goes beyond the story in the right places:
- Link targets reject `javascript:`/`data:`/`vbscript:` (including whitespace and control-character obfuscation).
- Dialog ids are validated, table rows must match the column count, and a `Cell` can't be both a link and a pill.
- The confirm dialog carries its own CSRF form.
- The integrator caught and fixed a real focus bug (the first "control" was the hidden CSRF input).
- The `<script` ban was narrowed precisely to inline scripts, with a test that 7 inline variants are still rejected.
- 1.3 ISS-004 is properly closed: the URL walk now runs under DEBUG with an explicit allow-list.

Three findings:
- `ui_field` silently produces broken label and ARIA wiring for multi-input widgets (radio and checkbox groups) or forms with `auto_id=False` (ISS-001).
- Dismissing an alert with the keyboard drops focus to `<body>` (ISS-002).
- Cards hard-code `<h2>`, which will break the heading outline on the Story 2.2 catalogue page (ISS-003).

---

## Evidence Verified (re-run by REVIEWER, 2026-10-22)

```
$ uv run ruff format --check .        → 135 files already formatted
$ uv run ruff check .                 → All checks passed!
$ uv run mypy                         → Success: no issues found in 97 source files
$ PYTHONPATH=src uv run lint-imports  → Contracts: 2 kept, 0 broken.
$ manage.py makemigrations --check --dry-run → No changes detected
$ uv run pytest -q --cov=src --cov-branch --cov-fail-under=85
src/infrastructure/web/templatetags/ui.py                   181      0     52      0   100%
TOTAL                                                       807      0    110      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
980 passed in 8.31s
File sizes: ui.py 398 lines (limit 400); largest test file 383 lines; ui.js 54 lines.
```

**Probes**: a temporary test file, deleted afterwards (working tree clean), plus a real `runserver`.

```
PROBE ui_field(answer, RadioSelect):              label for=''  help/error ids=['_help', '_error']  aria-describedby="_help _error" on 2 inputs   ← ISS-001
PROBE ui_field(tags, CheckboxSelectMultiple):     label for=''  help/error ids=['_help', '_error']                                        ← ISS-001
PROBE ui_field on a form with auto_id=False:      <label class="field__label" for="">  ids '_help', '_error'                               ← ISS-001
GET /ro/_styleguide/ -> 200; duplicate ids: 0; dialogs ['sg-dialog-student', 'sg-dialog-staff'] each with its own trigger
GET /ro/accounts/login/ -> class="login-card" present; component CSS linked from base.html
```

---

## Acceptance Criteria Check

| AC | Result | Evidence |
|----|--------|----------|
| 1 `ui_field`: label/for, help/error ids, `aria-invalid`, `aria-describedby`, "(required)" | ⚠️ | Correct for single-input widgets (tests in `test_molecules.py`). Multi-input widgets and `auto_id=False` are broken (ISS-001) |
| 2 `ui_field_pair`: fieldset/legend, RO/EN columns, `lang`, per-column errors | ✅ | `ui.py` `ui_field_pair`; `field_pair.html`; language-suffix stripping tested |
| 3 `ui_alert`: 4 levels, roles, icon, close `data-dismiss` "Close/Închide" | ✅ | `test_molecules.py` (roles ×4, unknown level, close label RO via catalogue) |
| 4 `ui_card`: `<article>`, title link only, stretched-link CSS | ✅ (see ISS-003) | `card.html`; `card.css` `.card--link .card__title a::after` |
| 5 `ui_disabled_tile`: `aria-disabled`, no href/tabindex/interactive descendants, "Unavailable" | ✅ | `disabled_tile.html`; tests assert no `<a`/`<button`/`tabindex` |
| 6 `ui_empty_state`: action only with both args | ✅ | `ui.py` `show_action`; tests |
| 7 `ui_page_header`: `<header>`, `<h1>`, breadcrumb `<nav><ol>`, `aria-current` on the last item, actions | ✅ | `page_header.html`; `test_molecules_layout.py` |
| 8 Confirm dialog with its own CSRF form, hidden inputs, `extra_template`, Cancel/Confirm; trigger + `<noscript>` | ✅ | `confirm_dialog.html`, `dialog_trigger.html`; tests |
| 9 `ui.js`: showModal, remember trigger, focus first control, close/Esc → focus return, dismiss, idempotent, delegation, no globals/eval | ✅ (see ISS-002) | `ui.js:15-54`; `test_molecule_assets.py` static checks. Behaviour is browser-verified in Story 1.10 (Playwright), as the story states |
| 10 `ui_table`: caption, `th scope=col`, `str`/`Cell`, pill/link, unknown cell → `ValueError`, empty → empty state | ✅ | `_cell`, `ui_table`, `table.html`; tests |
| 11 CSS for the 1.1/1.2 hooks | ✅ | `card.css`, `alert.css`, `form_field.css`; `test_molecule_assets.py`; login page renders `login-card` with linked CSS |
| 12 Styleguide shows all 8 molecules in both themes and loads `ui.js` | ✅ | `_molecules.html`, `index.html`; real server: 200, no duplicate ids |
| 13 Tokens only, no inline style/script, no `|safe`, no `!important` | ✅ | `test_inline_script.py`, `test_design_assets.py`, `test_molecule_assets.py` |
| 14 RO/EN for the listed strings | ✅ | `test_every_new_ui_string_is_in_the_catalogue[ro,en]` |
| 1.3 ISS-004 DEBUG-only route walk | ✅ | `test_url_protection.py` (allow-list `styleguide:index`); `story-1.3-code-review-v1.md` ✅ Fully Remediated (5/5) |

---

## Checklist Results

### Correctness
- [x] ✅ All tags validate input and fail loudly (unknown level/variant/cell, script URLs, bad dialog ids, row/column mismatch)
- [x] ⚠️ `ui_field` assumes a single-input widget with an id (ISS-001)
- [x] ✅ `ui.js` is idempotent (open-when-open and double dismiss are no-ops); focus skips hidden inputs

### Pattern Adherence
- [x] ✅ §11.2: one template plus one stylesheet per molecule; Story 1.5 atom tags unchanged
- [x] ✅ §7.4/§13: external ES module, no inline script or handlers, no eval, no globals; CSP `script-src 'self'` respected
- [x] ⚠️ §11.4: focus management after alert dismissal (ISS-002); heading levels (ISS-003)
- [x] ✅ Functions < 30 lines; `ui.py` 398 lines, at the 400-line limit (the integrator already noted that new tags need a new module)

### Testing
- [x] ✅ Behavioural tests per molecule including hostile inputs; static contract tests for CSS and JS; inline-script guard proven against 7 variants
- [x] ⚠️ No test with a `RadioSelect`/`CheckboxSelectMultiple` field or `auto_id=False` (ISS-001)
- [x] ✅ Coverage 100%

### Documentation
- [x] ✅ Docstrings on every tag; the `ui.js` header documents the data-attribute contract and CSP reasoning
- [x] ✅ Self-review `docs/stories-implemented/story-1.6-review.md` with DoD gates. Screenshots and the manual keyboard/VoiceOver walk-through are honestly marked as not done (no browser); curl/HTML evidence is given instead

### Security
- [x] ✅ All values autoescaped; script-scheme URLs rejected in every href/action; dialog form always has `{% csrf_token %}`; `extra_template` is chosen by template authors, not request data

### Performance
- [x] ✅ Five extra stylesheets on every page via `base.html` (small, cacheable); one delegated click listener

### SOLID / Anti-Monolith
- [x] ✅ Small private helpers (`_href`, `_pairs`, `_dialog_id`, `_cell`, `_icon_variant`) reused across tags; no feature coupling

---

## Issues Found

### ISS-001: `ui_field` renders broken label/ARIA wiring for radio and checkbox groups and for `auto_id=False` forms 🟡 Medium

**Category**: Correctness (accessibility)
**File**: `src/infrastructure/web/templatetags/ui.py` (`_field_context`), `src/infrastructure/web/templates/components/form_field.html:2,5-6`
**Pattern Reference**: Story 1.6 AC 1 ("label `for` = widget id … `aria-describedby` lists help and error ids"); patterns §11.4; WCAG 1.3.1 / 4.1.2

**Issue**:
`_field_context` uses `field.id_for_label` for both the label's `for` and the help/error ids. For multi-input widgets, Django returns `""` from `id_for_label`, and so does any form built with `auto_id=False`. The probe shows:
- `RadioSelect` → `<label for="">`, help/error ids `_help` / `_error`, and `aria-describedby="_help _error"` copied onto every radio input
- `CheckboxSelectMultiple` → the same
- `auto_id=False` → the same

Consequences:
- The label is associated with nothing.
- Two such fields on one page produce duplicate `_help`/`_error` ids, so screen readers announce the wrong field's error.
- A group of radios should be announced through `<fieldset><legend>`, not a `<label for>`.

Student answers (single-choice and multiple-choice exercises and tests, CYCLE-2/3) are exactly this widget type, so the first real caller will hit it silently: there's no exception and every test still passes.

**Current Code**:
```python
widget_id = field.id_for_label
described = [f"{widget_id}_help"] if help else []
```

**Suggested Fix**: fail loudly now, and give groups the right structure:
```python
_GROUP_WIDGETS = (forms.RadioSelect, forms.CheckboxSelectMultiple)

def _field_context(field, help="", legend="", lang=""):
    ...
    base_id = field.auto_id
    if not base_id:
        raise ValueError(f"ui_field needs a form with auto_id (field {field.name!r})")
    is_group = isinstance(field.field.widget, _GROUP_WIDGETS)
    described = [f"{base_id}_help"] if help else []
    ...
    return {..., "id": base_id, "is_group": is_group}
```
In `form_field.html`, when `is_group` is set, wrap the widget in `<fieldset class="field" aria-describedby="…">` with `<legend class="field__label">` instead of `<label for>`. The help and error ids come from `field.auto_id` (`id_answer_help`, `id_answer_error`), which is unique per field.

**Suggested Test**:
```python
def test_radio_group_uses_fieldset_legend_and_unique_ids():
    form = ChoiceForm(data={}); form.is_valid()
    html = render('{% ui_field f.answer help="Pick one" %}', f=form)

    assert "<fieldset" in html and "<legend" in html and 'for=""' not in html
    assert 'id="id_answer_help"' in html and 'id="id_answer_error"' in html


def test_field_without_auto_id_fails_loudly():
    with pytest.raises(ValueError, match="auto_id"):
        render("{% ui_field f.name %}", f=NameForm(auto_id=False))
```

**Why This Matters**: the molecule's whole purpose is correct label and error association. Today it is only correct for single inputs, and fails silently for the widget students will use most.

---

### ISS-002: Dismissing an alert with the keyboard drops focus to `<body>` 🟢 Low

**Category**: Accessibility
**File**: `src/infrastructure/web/static/js/ui.js:41-44`
**Pattern Reference**: Story 1.6 plain-English AC ("can be closed with the mouse or keyboard"); patterns §11.4; WCAG 2.4.3 (Focus Order)

**Issue**:
`dismiss.closest('.alert')?.remove()` removes the element that holds focus (the × button). Per the HTML focus-fixup rule, focus falls back to `<body>`, so a keyboard or screen-reader user who presses Enter on × lands at the top of the document and has to Tab back through the whole page. Mouse users aren't affected. This is from code reading; Story 1.10's Playwright run can assert it.

**Current Code**:
```javascript
const dismiss = event.target.closest('[data-dismiss]');
if (dismiss) {
  dismiss.closest('.alert')?.remove();
}
```

**Suggested Fix**: move focus to a stable target before removing:
```javascript
const alert = dismiss.closest('.alert');
if (alert) {
  const main = document.getElementById('content');   // <main id="content"> in base.html
  if (alert.contains(document.activeElement) && main) {
    main.setAttribute('tabindex', '-1');
    main.focus();
  }
  alert.remove();
}
```
Add a static test in `test_molecule_assets.py` that `ui.js` moves focus before `remove()`, and add the browser assertion to Story 1.10's journey list.

---

### ISS-003: `ui_card` hard-codes `<h2>`, which breaks the heading outline of nested lists 🟢 Low

**Category**: Accessibility / Maintainability
**File**: `src/infrastructure/web/templates/components/card.html:3`
**Pattern Reference**: patterns §11.4 (headings in order); WCAG 1.3.1. The next consumer is Story 2.2 (catalogue: page `<h1>`, a grade section heading, then subject cards)

**Issue**:
Card titles are always `<h2>`. On the catalogue page (Story 2.2) the natural outline is `h1` Catalogue → `h2` "Clasa a II-a" → subject cards. With fixed `<h2>` cards, each subject becomes a sibling of its grade, and screen-reader heading navigation flattens the hierarchy. The component can't know its nesting depth, so the caller should choose it.

**Suggested Fix**:
```python
@register.inclusion_tag("components/card.html")
def ui_card(title, body="", href=None, icon=None, meta="", level=2):
    if level not in (2, 3, 4):
        raise ValueError(f"Card heading level must be 2-4, got {level}")
    return {..., "level": level}
```
```django
<h{{ level }} class="card__title">…</h{{ level }}>
```
Add a test that the default stays `h2` and that `level=3` renders `<h3 class="card__title">`. Because `ui.py` is at 398 lines, this is a good moment to move the molecule tags into a second module (for example `templatetags/ui_molecules.py`, registered on the same library or loaded as `{% load ui ui_molecules %}`).

---

## Issue Summary

| # | ID | Severity | Category | File | Status |
|---|-----|----------|----------|------|--------|
| 1 | ISS-001 | 🟡 Medium | Correctness (a11y) | `ui.py` `_field_context`; `form_field.html` | Should Fix |
| 2 | ISS-002 | 🟢 Low | Accessibility | `static/js/ui.js:41-44` | Optional |
| 3 | ISS-003 | 🟢 Low | Accessibility | `components/card.html:3` | Optional |

**Summary**:
- Blockers: 0
- High: 0
- Medium: 1
- Low: 2

---

## What Was Done Well

1. ✅ **Defensive tags beyond the story**: script-scheme URL rejection with obfuscation handling, dialog-id validation, row/column checks, and link-xor-pill cells. Each is tested.
2. ✅ **A real bug caught in integration**: the first focusable "control" in the dialog was the hidden CSRF input. It's fixed and the reason is documented in a comment.
3. ✅ **Precise loosening of a guard**: the `<script` ban became "inline scripts only" with a test proving 7 inline variants are still caught. It is narrower, not weaker.
4. ✅ **The styleguide has no duplicate ids** despite rendering every molecule twice (per-theme dialog ids and forms), so its own a11y is valid.
5. ✅ **1.3 ISS-004 closed properly**: the DEBUG route walk with an explicit allow-list, a proven failure before the fix, and production routing restored afterwards.
6. ✅ **Honest evidence**: the self-review states plainly that screenshots and the VoiceOver walk-through weren't possible, instead of claiming them.

---

## Approval Status

**Decision**: ⚠️ APPROVED WITH COMMENTS

**Reason**: no blockers and no high-severity issues. ISS-001 should be fixed before any form with choice widgets uses `ui_field`; the first such forms come in CYCLE-2. ISS-003 is worth doing before Story 2.2 (Wave 4) builds the catalogue grid. The manual browser checks from the story's Evidence list are still open, and QA or Story 1.10 should cover them.

**Next Steps**:
1. `aire-dev-remediate` for ISS-001 (recommended), with ISS-002 and ISS-003 optional.

---

## Sign-Off

**Reviewer**: REVIEWER Agent
**Date**: 2026-10-22
**Signature**: Approved with comments
