# Code Review - Story 1.5: Design Tokens & Atom Primitives

**Date**: 2026-10-22
**Reviewed By**: REVIEWER Agent
**Review Number**: 1
**Review Mode**: INITIAL_REVIEW
**Status**: ⚠️ APPROVED WITH COMMENTS

---

## Review Metadata

**Previous Review**: None
**Previous Status**: N/A
**Files Changed Since Last Review**: All (first review). Reviewed at `main` @ `a6705ec`; Story 1.4 later added `language_switcher.css`, which is out of scope here
**Severity Threshold Applied**: All

---

## Review Summary

**Components Reviewed**:
- `static/css/tokens.css` (140 lines)
- 7 component stylesheets: `button`, `icon`, `badge`, `status_pill`, `avatar`, `score`, `progress_meter`
- 7 component templates
- `templatetags/ui.py` (145)
- `static/fonts/` (3 woff2 files and `OFL.txt`)
- `static/icons/sprite.svg` (50 symbols) and `LICENSE`
- `web/styleguide/` (`views.py`, `urls.py`), `templates/styleguide/` (`index.html`, `_atoms.html`), `static/css/styleguide.css`
- `config/urls.py` (DEBUG-only registration)
- RO/EN catalogue entries

**Lines of Code**: ~600 production lines (CSS, templates, Python), ~810 test lines
**Tests Reviewed**: Yes:
- `tests/integration/web/ui/test_atoms.py` (299 lines)
- `tests/integration/web/ui/test_design_assets.py` (369)
- `tests/integration/web/ui/test_styleguide.py` (145)

**Coverage**: 100% overall; `templatetags/ui.py` 55/55 statements, 16/16 branches

**Overall Assessment**: An excellent foundation story:
- Every token is checked against the approved spec by a test.
- Every colour pair has a computed WCAG AA test.
- Every icon name is checked against the sprite.
- The guarantees promised as rules (no raw hex outside `tokens.css`, no `!important`, no inline style or script, no `|safe`, no external URLs) are enforced by tests, not left to convention.
- The styleguide is unreachable with `DEBUG=False`, also proven by tests.

The findings are about input handling in the tags:
- The numeric atoms silently **truncate** non-integer values: a score of 87.6 is shown as 87 (ISS-001).
- `ui_button` drops a falsy `value` such as `0` (ISS-002).
- The `hx_*` passthrough blocks `hx-on` but not HTMX's `js:` evaluation paths (ISS-003; the CSP already neutralises it).

---

## Evidence Verified (re-run by REVIEWER, 2026-10-22)

```
$ uv run ruff format --check .        → 130 files already formatted
$ uv run ruff check .                 → All checks passed!
$ uv run mypy                         → Success: no issues found in 95 source files
$ PYTHONPATH=src uv run lint-imports  → Contracts: 2 kept, 0 broken.
$ manage.py makemigrations --check --dry-run → No changes detected
$ uv run pytest -q --cov=src --cov-branch --cov-fail-under=85
src/infrastructure/web/templatetags/ui.py                    55      0     16      0   100%
TOTAL                                                       680      0     74      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
757 passed in 7.06s
$ uv run pytest -q tests/integration/web/ui   → 192 passed in 0.29s
```

**Probes**: a temporary test file, deleted afterwards. The working tree was clean after the run.

```
PROBE ui_score(87.6)            -> Score: 87 out of 100      ← ISS-001 (truncated, not rejected)
PROBE ui_score(99.9)            -> Score: 99 out of 100      ← ISS-001
PROBE ui_score(100.4)           -> Score: 100 out of 100     ← ISS-001 (outside 1–100, accepted)
PROBE ui_score(Decimal('87.6')) -> Score: 87 out of 100      ← ISS-001
PROBE ui_score(True)            -> Score: 1 out of 100       ← ISS-001
PROBE ui_score(None)            -> TypeError: int() argument must be … not 'NoneType'   (spec: ValueError)
PROBE ui_badge(2.7)             -> <span class="badge" role="img" aria-label="2 unread">2</span>
PROBE ui_badge(None)            -> TypeError
PROBE ui_progress(2.9, 3)       -> "2/3"
PROBE ui_button(value=0)        -> no value attribute        ← ISS-002 (form posts answer="")
PROBE ui_button(value='0')      -> value="0"
PROBE ui_button hx_vals='js:{a: 1}' -> hx-vals rendered     ← ISS-003 (blocked at runtime by CSP)
```

---

## Acceptance Criteria Check

| AC | Result | Evidence |
|----|--------|----------|
| 1 `tokens.css`: seeded names kept, pills, line heights, `@font-face`, themes, base styles, focus, visually-hidden, reduced motion | ✅ | `test_design_assets.py`: `test_root_token_matches_the_approved_spec` (each token), theme, body, focus, reduced-motion and `!important` tests |
| 2 Fonts and `OFL.txt`; RO diacritics | ✅ | `test_font_file_is_a_committed_woff2`, `test_font_licence…`; the styleguide sample contains "ș ț ă â î Ș Ț Ă Â Î"; the self-review records the glyph check |
| 3 Sprite: regular and duotone for exactly `ICON_NAMES`; MIT `LICENSE`; accent layer via a class | ✅ | 50 symbols; `test_sprite_has_regular_and_duotone_symbols_for_exactly_the_icon_names`, `test_duotone_layer_is_accent_filled…` |
| 4 Seven inclusion tags | ✅ | `ui.py`; `ui_button` adds `disabled` and `loading` (additive, tested) |
| 5 Invalid input raises | ⚠️ | Unknown names, statuses, sizes and ranges raise (tested). Non-integer numbers are truncated and `None` raises `TypeError` (ISS-001) |
| 6 Loading state, `pointer-events: none`, static ring under reduced motion | ✅ | `button.css`; `test_button_loading_state…`, `test_loading_button_shows_spinner_state_busy_and_disabled` |
| 7 One CSS file per atom, tokens only, no `!important` | ✅ | `test_each_atom_has_its_own_stylesheet_built_only_on_tokens`, `test_stylesheets_outside_tokens_never_use_raw_hex` |
| 8 Styleguide only with DEBUG; 404 and `NoReverseMatch` otherwise | ✅ | `test_styleguide_returns_404_in_production`, `test_styleguide_is_not_routed…`, `test_production_routing_is_restored_after_the_debug_reload` |
| 9 No external URLs | ✅ | `test_no_component_or_css_references_external_urls`, `test_sprite_only_mentions_the_svg_namespace_url`, `test_styleguide_loads_only_same_origin_stylesheets` |
| 10 RO and EN strings | ✅ | `test_every_new_ui_string_is_in_the_catalogue` (ro, en), `test_romanian_translation_matches_the_story` |

---

## Checklist Results

### Correctness
- [x] ✅ Code does what it's supposed to
- [x] ⚠️ Edge cases: non-integer and `None` numbers (ISS-001); falsy button `value` (ISS-002)
- [x] ✅ `ui_progress` with total 0 → `max="1"`, "0/0" (no division)
- [x] ✅ Deterministic rendering (tested); the styleguide makes no DB queries (tested)

### Pattern Adherence
- [x] ✅ UI Primitive Catalogue §11.2: one template and one stylesheet per atom; validation constants (`ICON_NAMES`, `STATUS_LABELS`, `SCORE_RANGE`) declared once and reused by the styleguide
- [x] ✅ Accessibility §11.4:
  - decorative icons are `aria-hidden`
  - labelled icons are `role="img"`
  - the score is announced as one phrase
  - the progress bar is wrapped in its `<label>` (no duplicate-id risk) and has `aria-valuetext`
  - pills show a word
  - focus ring 3px, 2px offset
- [x] ✅ Security §13: no CDN, no `|safe`, no inline script or style (all enforced by tests)
- [x] ✅ Naming, file organization; every function < 30 lines

### Testing
- [x] ✅ Behavioural tests per atom, including invalid inputs and autoescaping (`test_button_label_name_and_value_are_autoescaped`)
- [x] ✅ Design-contract tests parse the real CSS and sprite, so drift from the spec fails CI
- [x] ⚠️ No tests for non-integer, `None` or falsy-value inputs (ISS-001, ISS-002)
- [x] ✅ Coverage 100%

### Documentation
- [x] ✅ Module and tag docstrings; CSS headers name the template, the tag and the contrast ratio
- [x] ✅ No TODOs or commented-out code; self-review `docs/stories-implemented/story-1.5-review.md` exists

### Security
- [x] ✅ All attribute values autoescaped; only `hx_*` keys pass, and `hx_on*` (inline handlers) is rejected
- [x] ⚠️ `hx_vals`/`hx_vars`/`hx_headers` with a `js:` prefix pass through (ISS-003); `script-src 'self'` without `unsafe-eval` blocks HTMX's `eval` at runtime
- [x] ✅ No external requests (fonts and icons self-hosted)

### Performance
- [x] ✅ One sprite request for all icons (cached); tags are pure functions with no I/O

### SOLID / Anti-Monolith
- [x] ✅ Each tag has one job; the styleguide depends on the tag module's constants, not the reverse
- [x] ✅ No DB, no domain coupling; presentation-only module

---

## Issues Found

### ISS-001: Numeric atoms truncate non-integer values instead of rejecting them 🟡 Medium

**Category**: Correctness
**File**: `src/infrastructure/web/templatetags/ui.py:110, 134, 142`
**Pattern Reference**: Story 1.5 display matrix ("outside 1–100 → `ValueError`"; "a typo fails tests instead of shipping a blank or misleading element", `ui.py` module docstring); patterns §11.2

**Issue**:
`ui_score`, `ui_badge` and `ui_progress` coerce with `int(value)`, which **truncates toward zero**:
- `ui_score(87.6)` shows "87 / 100"; `ui_score(99.9)` shows 99.
- `ui_score(100.4)` is accepted, although it is outside 1–100. `True` is shown as a score of 1.
- `ui_badge(2.7)` shows "2"; `ui_progress(2.9, 3)` shows "2/3".
- `None` raises `TypeError` instead of the specified `ValueError`.

Scores are what students and parents look at (Epic 6/7). If a later story ever passes a computed percentage (`float` or `Decimal`) instead of the domain's rounded integer, the atom will silently show a different number. This is exactly the "misleading element" the module promises to prevent.

**Current Code**:
```python
if int(value) not in SCORE_RANGE:
    raise ValueError(f"Score must be 1-100, got {value}")
return {"value": int(value)}
```

**Suggested Fix**: one strict helper used by the three numeric tags. It accepts `int` and digit strings from templates, and rejects `bool`, `None`, fractions and anything else:
```python
def _whole_number(value: object, what: str) -> int:
    """Template numbers must be whole: 87.6 is a caller bug, never shown as 87."""
    if isinstance(value, bool):
        raise ValueError(f"{what} must be a whole number, got {value!r}")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value)
    if isinstance(value, Decimal | float) and value == int(value):
        return int(value)
    raise ValueError(f"{what} must be a whole number, got {value!r}")


def ui_score(value: int) -> TagContext:
    score = _whole_number(value, "Score")
    if score not in SCORE_RANGE:
        raise ValueError(f"Score must be 1-100, got {value}")
    return {"value": score}
```

**Suggested Test**:
```python
@pytest.mark.parametrize("value", [87.6, 99.9, 100.4, Decimal("87.6"), True, None, "abc"])
def test_score_rejects_values_that_are_not_whole_numbers(value):
    with pytest.raises(ValueError):
        render("{% ui_score v %}", v=value)


@pytest.mark.parametrize("value", [87, "87", 87.0, Decimal("87")])
def test_score_accepts_whole_numbers_in_any_form(value):
    assert 'aria-label="Score: 87 out of 100"' in render("{% ui_score v %}", v=value)
```
Add the same pair for `ui_badge` (2.7, `None`) and `ui_progress` (2.9/3).

**Why This Matters**: the atoms are the last line before a number reaches a child or parent. Failing loudly in tests is cheap; a silently wrong score is not.

---

### ISS-002: `ui_button` drops a falsy `name` or `value` (e.g. `value=0`) 🟢 Low

**Category**: Correctness
**File**: `src/infrastructure/web/templates/components/button.html:1`
**Pattern Reference**: Story 1.5 AC 4 (`ui_button(…, name=None, value=None, …)`: `None` means "absent", not any falsy value)

**Issue**:
`{% if value %}` treats `0`, `""` and `False` as absent. `{% ui_button "A" name="answer" value=0 %}` renders `<button name="answer">` with no value attribute, so the form posts `answer=""` instead of `answer=0`. No caller passes an integer value today. Answer-choice buttons in later epics (practice and test options indexed from 0) are the obvious first caller, and that bug would show up as a server-side validation error far from its cause.

**Current Code**:
```django
{% if name %} name="{{ name }}"{% endif %}{% if value %} value="{{ value }}"{% endif %}
```

**Suggested Fix**:
```django
{% if name is not None %} name="{{ name }}"{% endif %}{% if value is not None %} value="{{ value }}"{% endif %}
```
`test_button_without_name_or_value_omits_the_attributes` keeps passing, because the defaults are `None`.

**Suggested Test**:
```python
@pytest.mark.parametrize(("value", "expected"), [(0, 'value="0"'), ("", 'value=""')])
def test_button_keeps_a_falsy_value(value, expected):
    assert expected in render('{% ui_button "A" name="answer" value=v %}', v=value)
```

---

### ISS-003: The `hx_*` passthrough allows HTMX's `js:` evaluation paths 🟢 Low

**Category**: Security (defence in depth)
**File**: `src/infrastructure/web/templatetags/ui.py:70-74`
**Pattern Reference**: patterns §13 (no inline script); the `_hx_attributes` docstring ("Only HTMX attributes pass, never inline handlers")

**Issue**:
`hx_on*` is rejected because it runs JavaScript. HTMX has other attributes that evaluate JavaScript:
- `hx-vals="js:{…}"`
- the deprecated `hx-vars`
- `hx-headers="js:{…}"`

All three pass through (probe: `hx_vals='js:{a: 1}'` renders). **Mitigation in place:** the Story 1.2 CSP sets `script-src 'self'` with no `'unsafe-eval'`, so HTMX's `eval` is refused by the browser. The risk is a future CSP relaxation combined with a template that builds `hx_vals` from user data. The guard's stated intent ("never inline handlers") is also only half-enforced.

**Suggested Fix**:
```python
_HX_SCRIPTABLE = frozenset({"hx_vars"})
_HX_JSON = frozenset({"hx_vals", "hx_headers"})


def _hx_attributes(hx: dict[str, str]) -> list[tuple[str, str]]:
    """`hx_post="/x"` -> `("hx-post", "/x")`. Only HTMX attributes pass, never script."""
    bad = sorted(
        key for key, value in hx.items()
        if not key.startswith("hx_") or key.startswith("hx_on") or key in _HX_SCRIPTABLE
        or (key in _HX_JSON and str(value).lstrip().startswith(("js:", "javascript:")))
    )
    if bad:
        raise template.TemplateSyntaxError(f"ui_button accepts only non-script hx_* attributes, got {bad}")
    return [(key.replace("_", "-"), value) for key, value in sorted(hx.items())]
```
Alternatively, or as well, Story 1.7's base layout can set `<meta name="htmx-config" content='{"allowEval": false}'>`.

**Suggested Test**:
```python
@pytest.mark.parametrize("kwarg", ['hx_vals="js:{a: 1}"', 'hx_headers="javascript:{}"', 'hx_vars="a:1"'])
def test_button_rejects_hx_attributes_that_evaluate_script(kwarg):
    with pytest.raises(TemplateSyntaxError):
        render('{% ui_button "Save" ' + kwarg + " %}")
```

---

## Issue Summary

| # | ID | Severity | Category | File | Status |
|---|-----|----------|----------|------|--------|
| 1 | ISS-001 | 🟡 Medium | Correctness | `templatetags/ui.py:110, 134, 142` | Should Fix |
| 2 | ISS-002 | 🟢 Low | Correctness | `components/button.html:1` | Optional |
| 3 | ISS-003 | 🟢 Low | Security | `templatetags/ui.py:70-74` | Optional |

**Summary**:
- Blockers: 0
- High: 0
- Medium: 1
- Low: 2

---

## What Was Done Well

1. ✅ **Design-contract tests**: tokens, theme values, the font faces, the sprite's symbol set and the duotone layer are all parsed and asserted against the spec, so a careless edit fails CI.
2. ✅ **Accessibility verified by computation**: every colour pair's WCAG ratio is computed in a test, not just claimed in a comment. Pills always carry a word.
3. ✅ **Privacy by construction**: self-hosted font and sprite; three separate tests guard against external URLs.
4. ✅ **Safe passthrough**: `hx_on*` (inline JS) is explicitly rejected beyond the story's `hx_` prefix rule, and autoescaping is proven with a hostile value.
5. ✅ **The DEBUG-only route** is tested both ways (404 and `NoReverseMatch` in production, routed with DEBUG), and the test restores production routing afterwards.
6. ✅ **Progress meter**: wrapping `<progress>` in its `<label>` avoids the duplicate-id bug the story's `slugify` example would have had with two meters sharing a label.

---

## Approval Status

**Decision**: ⚠️ APPROVED WITH COMMENTS

**Reason**: no blockers and no high-severity issues. ISS-001 should be fixed before the score and progress atoms get real callers (Epics 4, 6 and 7). ISS-002 and ISS-003 are cheap hardening.

**Next Steps**:
1. `aire-dev-remediate` for ISS-001 (recommended), with ISS-002 and ISS-003 optional.

---

## Sign-Off

**Reviewer**: REVIEWER Agent
**Date**: 2026-10-22
**Signature**: Approved with comments
