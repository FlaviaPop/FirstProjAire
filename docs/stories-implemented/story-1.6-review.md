# Story 1.6 Self-Review

**Date**: 2026-10-22
**Story**: 1.6 — Molecule Primitives (`docs/plans/stories/epic-1-story-1.6-Molecule-Primitives.md`)
**Developer**: DEV Agent (in-one-go parallel mode: components a/b/c + integrator)
**Branch**: `feature/story-1.6-molecules`
**Also resolves**: Story 1.3 code review v1 **ISS-004** (DEBUG-only URL walk)

---

## What Was Implemented

- **9 molecule inclusion tags + `Cell`** in `templatetags/ui.py` (component a): `ui_field`, `ui_field_pair`, `ui_alert`, `ui_card`, `ui_disabled_tile`, `ui_empty_state`, `ui_page_header`, `ui_confirm_dialog`, `ui_dialog_trigger`, `ui_table`, plus the frozen `Cell(text, href=None, pill=None)` dataclass. Every Story 1.5 atom tag, constant and helper is byte-for-byte unchanged.
- **10 component templates** in `templates/components/`: the 8 molecules, plus `field_pair.html` and `dialog_trigger.html`.
- **8 molecule stylesheets** in `static/css/components/` (component b). They use tokens only, and they also style the Story 1.1/1.2 hooks `error-card`, `error-card__violations`, `error-card__ref`, `error-partial`, `login-card`, `form-banner`, `form-banner--error` and `field-error`.
- **`static/js/ui.js`** (component b): a dependency-free ES module. It handles dialog open/close/focus-return and alert dismissal through `data-*` delegation on `document`.
- **Styleguide molecules section** (integrator): `templates/styleguide/_molecules.html` is included after `_atoms.html` in both theme sections. The page links the 8 molecule stylesheets and loads `ui.js` as a same-origin module. The sample forms, alerts, cards, tile, empty state, page header, dialog and tables are built DB-free in `styleguide/views.py`.
- **Token** `--color-backdrop: rgba(31, 41, 55, .5)` in `tokens.css` (dialog backdrop).
- **Sign-in and error pages styled now** (user decision 2026-10-22, "Add the links now"). `layouts/base.html` links `icon.css`, `button.css`, `card.css`, `alert.css` and `form_field.css`.
- **Translations**: RO/EN for the 8 AC 14 strings and every new styleguide sample string (43 new msgids, 0 fuzzy, 0 empty).
- **Story 1.3 ISS-004** (component c): `test_url_protection.py` now also walks the URLConf reloaded with `DEBUG=True`, against the explicit `DEBUG_ONLY_URL_NAMES = {"styleguide:index"}`.

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `src/infrastructure/web/templatetags/ui.py` | Modified (append-only) | Molecule tags + `Cell` (lines 180–398); 398 lines, under the 400 limit |
| `src/infrastructure/web/templates/components/{form_field,field_pair,alert,card,disabled_tile,empty_state,page_header,confirm_dialog,dialog_trigger,table}.html` | New | Molecule markup per the shared class contract |
| `src/infrastructure/web/static/css/components/{form_field,alert,card,disabled_tile,empty_state,page_header,confirm_dialog,table}.css` | New | Token-only molecule styles + 1.1/1.2 hook styles |
| `src/infrastructure/web/static/js/ui.js` | New | Dialog + dismiss behaviour (CSP-safe ES module) |
| `src/infrastructure/web/styleguide/views.py` | Modified | `SampleForm`, `MoleculeSamples` per theme, molecule sample context |
| `src/infrastructure/web/templates/styleguide/index.html` | Modified | 8 molecule `<link>`s, `ui.js` module, `_molecules.html` include in both themes |
| `src/infrastructure/web/templates/styleguide/_molecules.html` | New | Molecules section |
| `src/infrastructure/web/static/css/styleguide.css` | Modified | `.sg-molecules`, `.sg-grid`, `.sg-wide` (tokens only) |
| `src/infrastructure/web/static/css/tokens.css` | Modified | `--color-backdrop` |
| `src/infrastructure/web/templates/layouts/base.html` | Modified | 5 component stylesheet links (user decision) |
| `src/infrastructure/i18n/locale/{ro,en}/LC_MESSAGES/django.po` | Modified | 43 new entries each (`.mo` compiled; gitignored) |
| `tests/integration/web/ui/test_molecules.py` | New | Story Tests block (verbatim) + field/pair/alert/card/tile edges (41) |
| `tests/integration/web/ui/test_molecules_layout.py` | New | Empty state/page header/dialog/table edges (39), split from test_molecules.py |
| `tests/integration/web/ui/test_molecule_assets.py` | New | Static CSS + ui.js assertions (55) |
| `tests/integration/web/ui/test_styleguide.py` | Modified | Molecules in both themes/languages, ui.js, links, unique ids, icon variants (34 total) |
| `tests/integration/web/ui/test_inline_script.py` | New | Inline-script detector + proof it still catches inline code (10) |
| `tests/integration/web/ui/test_base_layout_styles.py` | New | Login/404 link the component CSS; base loads no script (17) |
| `tests/integration/web/ui/test_atoms.py` | Modified | `<script` dropped from the blanket pattern (moved, narrowed) |
| `tests/integration/web/ui/test_design_assets.py` | Modified | `--color-backdrop` spec token; RO checks for the 8 AC 14 strings |
| `tests/integration/web/test_url_protection.py` | Modified | ISS-004 DEBUG-only walk (component c) |
| `docs/reviews/story-1.3-code-review-v1.md` | Modified | ISS-004 resolution; banner full-suite count 980/980 |

## Patterns Applied

| Pattern | Where Applied | Notes |
|---------|---------------|-------|
| UI primitive catalogue §11.2 | `templates/components/`, `templatetags/ui.py`, `static/css/components/` | Primitives only in the shared library; all shown on `/_styleguide/` |
| No inline script/style §7.4 / §11.1 / CSP | templates, `ui.js` | External `type="module"` only; `test_inline_script.py` |
| i18n §11.3 | `{% translate "…" %}`, `gettext_lazy` | English msgids; full RO catalogue |
| A11y §11.4 | labels/`for`, `aria-describedby`, `aria-invalid`, `role`, `aria-current`, `lang`, native `<dialog>` | Status pills keep their word; focus outline kept (`card--link:focus-within`) |
| Security §13 | autoescape only; `{% csrf_token %}` in every dialog form; script-scheme URLs rejected | No `|safe`/`mark_safe`; no external URLs |
| Validate then build context (ui.py) | every molecule tag | `ValueError` for bad data, `TemplateSyntaxError` for bad variants (same as `ui_button`) |
| Testing §12 | AAA, behavioural names | Static-text tests for JS (no JS toolchain; Playwright in Story 1.10) |

## Testing Summary

- **Story 1.6 tests**: 41 + 39 (molecules) + 55 (assets) + 34 (styleguide) + 10 (inline script) + 17 (base layout) + 32 (URL protection incl. ISS-004); all pass
- **Full suite**: **980/980** passing in each of **3 consecutive runs**
- **Coverage**: **100.00%** lines + branches (target 85%); `src/domain` 100% (≥100), `src/application` 100% (≥95); `ui.py` 181 stmts / 52 branches, 100%

**Test Output** (run 1 of 3, tail):
```
src/infrastructure/web/templatetags/ui.py                   181      0     52      0   100%
-------------------------------------------------------------------------------------------
TOTAL                                                       807      0    110      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
980 passed in 8.23s
```

## DoD Evidence

### Commands and outputs

```
$ uv run pytest -q --cov=src --cov-branch --cov-fail-under=85   (x3)
run 1 exit=0: 980 passed in 8.23s | Required test coverage of 85% reached. Total coverage: 100.00%
run 2 exit=0: 980 passed in 8.11s | Required test coverage of 85% reached. Total coverage: 100.00%
run 3 exit=0: 980 passed in 7.96s | Required test coverage of 85% reached. Total coverage: 100.00%

$ uv run coverage report --include="src/domain/*" --fail-under=100
TOTAL                                     79      0      8      0   100%        (exit=0)
$ uv run coverage report --include="src/application/*" --fail-under=95
TOTAL                                                      67      0     10      0   100%   (exit=0)

$ uv run ruff format --check .
135 files already formatted                                   exit=0
$ uv run ruff check .
All checks passed!                                            exit=0
$ uv run mypy
Success: no issues found in 97 source files                   exit=0
$ PYTHONPATH=src uv run lint-imports
Layers point inward KEPT
Domain is framework-free KEPT
Contracts: 2 kept, 0 broken.
$ uv run python manage.py makemigrations --check --dry-run
No changes detected                                           exit=0
```

Translations (`PATH=~/.local/share/mamba/envs/gettext/bin:$PATH`):
```
$ uv run python manage.py makemessages -l ro -l en --no-wrap --ignore=.venv --ignore=.claude --ignore=docs --ignore=SPEC --ignore=tests
processing locale ro
processing locale en
$ uv run python manage.py compilemessages --ignore=.venv
processing file django.po in …/src/infrastructure/i18n/locale/ro/LC_MESSAGES
processing file django.po in …/src/infrastructure/i18n/locale/en/LC_MESSAGES
$ msgfmt --check --statistics -o /dev/null …/ro/LC_MESSAGES/django.po
105 translated messages.
$ grep -c "fuzzy" …/{ro,en}/LC_MESSAGES/django.po
0 / 0
```
makemessages fuzzy-matched 6 new ids per catalogue to old ones: Student←"Student theme", Status←"Status pills", Publish←"Published" (msgstr "Publicat"), Delete sample←"Delete", Disabled tile←"Disabled", Table←"Disabled". I reviewed every one, gave it the correct translation (Elev, Stare, Publică, Șterge exemplul, Dală dezactivată, Tabel) and removed the flag and the `#|` lines. A before/after diff of the RO catalogue showed **0 existing msgstr changed, 0 removed, 43 added**. The single plural entry (lockout) still has all 3 RO forms. The `.mo` files are gitignored, so they are rebuilt by `compilemessages` as before.

### Real-server check (`runserver 127.0.0.1:8766 --noreload`, `config.settings.dev`, DEBUG=True)

```
GET /ro/_styleguide/ -> 200
GET /en/_styleguide/ -> 200
GET /ro/accounts/login/ -> 200
GET /en/accounts/login/ -> 200
/ro/_styleguide/ molecules (both themes): field-pair=4 alert--error=2 card--link=2 tile--disabled=2 empty-state=4 breadcrumb-nav=2 dialog=2 data-dialog-open=2 caption=2 aria-invalid=6
  scripts: <script type="module" src="/static/js/ui.js">
/en/_styleguide/ molecules (both themes): field-pair=4 alert--error=2 card--link=2 tile--disabled=2 empty-state=4 breadcrumb-nav=2 dialog=2 data-dialog-open=2 caption=2 aria-invalid=6
  scripts: <script type="module" src="/static/js/ui.js">
RO strings: 12 (obligatoriu); 2 Este necesar JavaScript pentru a confirma această acțiune.; 2 Indisponibil; 2 aria-label="Fir de navigare"; 8 aria-label="Închide";
--- every linked CSS/JS URL (styleguide + login + 404), each fetched ---
200 text/css  /static/css/components/alert.css
200 text/css  /static/css/components/avatar.css
200 text/css  /static/css/components/badge.css
200 text/css  /static/css/components/button.css
200 text/css  /static/css/components/card.css
200 text/css  /static/css/components/confirm_dialog.css
200 text/css  /static/css/components/disabled_tile.css
200 text/css  /static/css/components/empty_state.css
200 text/css  /static/css/components/form_field.css
200 text/css  /static/css/components/icon.css
200 text/css  /static/css/components/page_header.css
200 text/css  /static/css/components/progress_meter.css
200 text/css  /static/css/components/score.css
200 text/css  /static/css/components/status_pill.css
200 text/css  /static/css/components/table.css
200 text/css  /static/css/styleguide.css
200 text/css  /static/css/tokens.css
200 text/javascript  /static/js/ui.js
--- login_ro stylesheet links ---
<link rel="stylesheet" href="/static/css/tokens.css">
<link rel="stylesheet" href="/static/css/components/icon.css">
<link rel="stylesheet" href="/static/css/components/button.css">
<link rel="stylesheet" href="/static/css/components/card.css">
<link rel="stylesheet" href="/static/css/components/alert.css">
<link rel="stylesheet" href="/static/css/components/form_field.css">
--- CSP: Content-Security-Policy: script-src 'self'; base-uri 'self'; font-src 'self'; frame-ancestors 'none'; img-src 'self' data:; form-action 'self'; default-src 'self'; style-src 'self'
```
With DEBUG=True Django serves its own technical 404 page, so the real `errors/404.html` cannot be checked on that server. I checked it on a second, temporary server instead: port 8767, a scratch settings module `from config.settings.dev import *; DEBUG = False`, and `--insecure` so static files are still served. No repo file was changed for this.
```
GET /ro/does-not-exist/ (DEBUG=False) -> 404
<link rel="stylesheet" href="/static/css/tokens.css">
<link rel="stylesheet" href="/static/css/components/icon.css">
<link rel="stylesheet" href="/static/css/components/button.css">
<link rel="stylesheet" href="/static/css/components/card.css">
<link rel="stylesheet" href="/static/css/components/alert.css">
<link rel="stylesheet" href="/static/css/components/form_field.css">
class="error-card"
<h1 id="error-title">Pagina nu a fost găsită
GET /en/does-not-exist/ (DEBUG=False) -> 404   (same 6 links, class="error-card", "Page not found")
200 text/css  /static/css/tokens.css … 200 text/css  /static/css/components/form_field.css   (all 6)
GET /ro/_styleguide/ (DEBUG=False) -> 404
```
Server logs: `server.log` had 43 lines, 0 ERROR and 0 Traceback; `server_nodebug.log` had 20 lines, 0 ERROR and 0 Traceback. The only WARNINGs are `django.request` "Not Found" entries for the deliberate 404 probes. Both servers were stopped with `pkill -f "runserver 127.0.0.1:876x"`, and `pgrep` confirmed none is left.

### Screenshots, keyboard and VoiceOver checks: not possible here (honest note)

This run had no browser, screen reader or screen capture, so the Evidence items "styleguide screenshots (open dialog, field with errors)", "restyled 404/login screenshots", "keyboard dialog step log" and "VoiceOver notes" could **not** be produced. Their equivalents:
- **Styleguide and restyled pages**: the curl output above (HTTP status, rendered molecule markers, every linked CSS/JS URL returning 200, login and 404 linking the 6 stylesheets with the `login-card`/`error-card` hooks) plus `test_base_layout_styles.py` and `test_styleguide.py`.
- **Field with errors**: rendered markup from the real server, e.g. `<input type="text" name="student-invalid-lesson" aria-invalid="true" aria-describedby="id_student-invalid-lesson_help id_student-invalid-lesson_error" required id="id_student-invalid-lesson">` followed by `<p class="field__error field-error" id="id_student-invalid-lesson_error">… This field is required.</p>`.
- **Dialog keyboard behaviour**: covered by the static `ui.js` assertions (`test_molecule_assets.py:212-257`). Runtime behaviour relies on native `showModal()`: the rest of the page goes inert so Tab stays inside, Esc fires `cancel` → `close` with no submit, and the capture-phase `close` listener returns focus. Per the story's OUT list, runtime dialog behaviour is verified by Playwright in **Story 1.10**.
- **Still open for a human with a browser before QA sign-off**: the Manual section of the story in both themes. That means opening the dialog by mouse and by Enter, Tab cycling, Esc returning focus, Confirm posting to `#`, dismissing alerts by mouse and by Enter on ×, Tab skipping the tile, a VoiceOver pass, and screenshots.

### Gate 1 — Spec Echo

**Acceptance Criteria (14/14)**

| # | Requirement | Proof (file:line) |
|---|-------------|-------------------|
| AC 1 | `ui_field`: label `for`, Django widget, help `id=<id>_help`, error `id=<id>_error`, `aria-invalid` + `aria-describedby` (help+error), translated "(required)" | `ui.py:212-231`; `form_field.html:1-8`; tests `test_molecules.py:41,49,154,163,173,181,188,194`; RO `django.po:239-240` |
| AC 2 | `ui_field_pair`: `<fieldset>`+`<legend>` (RO label minus suffix), columns "Română"/"English", `lang` on inputs, errors per column | `ui.py:190-191,234-241`; `field_pair.html:1-8`; `form_field.html:2`; tests `test_molecules.py:60,202,219,227,237,248`; styleguide `test_styleguide.py:188` (`lang="ro" ` ×2 per theme) |
| AC 3 | `ui_alert`: 4 levels else `ValueError`; role alert/status; icon + text; close `data-dismiss` `aria-label` Close/Închide | `ui.py:182-187,244-255`; `alert.html:1-5`; tests `test_molecules.py:75,79,265,273,282`; RO `django.po:217-218`; `test_styleguide.py:242` |
| AC 4 | `ui_card`: `<article class="card">`; with `href` title is the single link; stretched link via CSS | `ui.py:258-271`; `card.html:1-6`; `card.css:30-42`; tests `test_molecules.py:292,302,313,319,324`; `test_molecule_assets.py:91` |
| AC 5 | `ui_disabled_tile`: `tile tile--disabled` `aria-disabled="true"`, `lock-simple`, "Unavailable", optional reason, no href/tabindex/interactive descendants | `ui.py:274-277`; `disabled_tile.html:1-6`; tests `test_molecules.py:84,334,346`; RO `django.po:225-226` |
| AC 6 | `ui_empty_state`: message + button-styled link only when both action args | `ui.py:287-303`; `empty_state.html:1-5`; tests `test_molecules_layout.py:23,36,42,48,52` |
| AC 7 | `ui_page_header`: `<header>`, `<h1>`, `<nav aria-label="Breadcrumb"><ol>`, `aria-current="page"` on last, action links (label,url,variant) | `ui.py:319-330`; `page_header.html:1-12`; tests `test_molecules.py:141`, `test_molecules_layout.py:60,80,88,94,99`; RO `django.po:247-248` |
| AC 8 | `ui_confirm_dialog`: `<dialog id aria-labelledby aria-describedby>` + own `<form method=post action>` + CSRF + hidden + `extra_template`; Cancel `type=button data-dialog-close`; Confirm submit; `ui_dialog_trigger` button `data-dialog-open` + `<noscript>` note | `ui.py:333-367`; `confirm_dialog.html:1-13`; `dialog_trigger.html:1-2`; tests `test_molecules.py:94,106`, `test_molecules_layout.py:107,125,134,143,149,154,159,172,177`; RO `django.po:221-222` |
| AC 9 | `ui.js`: open→`showModal`, remember trigger, focus first control; close/Esc→`close`, focus returns; dismiss removes `.alert`; idempotent; delegation on `document`; no globals/eval/inline handlers | `ui.js:15,17,25-30,37,43,49-52`; tests `test_molecule_assets.py:212,223,245,249,255` |
| AC 10 | `ui_table`: `<caption>`, `<th scope=col>`, str/int/`Cell` cells, pill → `ui_status_pill`, href → link, unknown → `ValueError("Unsupported cell…")`, empty → empty state | `ui.py:195-201,370-398`; `table.html:1-8`; tests `test_molecules.py:114,129,136`, `test_molecules_layout.py:185,200,209,214,219,226,233,238,249,257` |
| AC 11 | CSS hooks: `error-card`/`login-card` (card, centred, 560px), `error-card__violations`, `error-card__ref` (muted 14px), `error-partial` + `form-banner--error` (error alert), `field-error` | `card.css:3-13,45-53`; `alert.css:4-22,28-32`; `form_field.css:44-52`; tests `test_molecule_assets.py:62,77,83,118,136`; live on real pages: `base.html:10-14`, `test_base_layout_styles.py:24,49,56` |
| AC 12 | Styleguide shows all 8 molecules in both themes (`_molecules.html` after `_atoms.html`) and loads `ui.js` | `index.html:15-25,35-36`; `_molecules.html:1-43`; `views.py:86-161`; tests `test_styleguide.py:188,198,250,260,268,291,301`; curl above |
| AC 13 | Tokens only (no raw hex), no inline style/script, no `|safe`, no `!important` | `test_molecule_assets.py:50`; `test_design_assets.py:301`; `test_atoms.py` (style/safe rule); `test_inline_script.py:59,68`; Gate 2 greps below (all exit=1, no match) |
| AC 14 | RO/EN for "(required)", "Close", "Unavailable", "Cancel", "Breadcrumb", "Română", "English", "JavaScript is required to confirm this action." | `ro/django.po:239,217,225,48,247,230,235,221`; tests `test_design_assets.py:343` (ro+en non-empty), `:376` (exact RO), `test_styleguide.py:242` (rendered RO/EN) |

**Numbered Steps (7/7)**

| Step | Requirement | Proof |
|------|-------------|-------|
| 1 | Tests first in `test_molecules.py`, incl. the Tests block verbatim | `test_molecules.py:38-149` ("Story Tests block (verbatim)"); written by component a before the tags |
| 2 | Append tags to `ui.py`, 1.5 unchanged, `ALERT_LEVELS`, frozen `Cell`, no `|safe` for widget | `ui.py:180-398`; `git diff main -- ui.py \| grep "^-[^-]"` → no removed lines (Gate 2) |
| 3 | Templates per excerpts (form_field, confirm_dialog, disabled_tile normative) | `form_field.html:1-8`, `confirm_dialog.html:1-13`, `disabled_tile.html:1-6` (class names match the shared contract) |
| 4 | `ui.js` ES module per excerpt | `ui.js:1-54` |
| 5 | One CSS per molecule, tokens only, incl. hooks; card.css excerpt | 8 files in `static/css/components/`; `card.css:3-42`; `test_molecule_assets.py:50-207` |
| 6 | Styleguide `_molecules.html` (unbound+bound forms, `Cell` rows, empty table, dialog posting to `#`), after `_atoms.html`, `ui.js` loaded | `views.py:86-161`; `_molecules.html:4-42`; `index.html:25,35-36` |
| 7 | Translations, then all gates | makemessages/compilemessages output above; gates above |

**Design Tokens, constraints and Must Read references**

| Ref | Requirement | Proof |
|-----|-------------|-------|
| Story DT — Form field | label 600 (student 18 / staff 16); 1px border, radius, min-height touch, padding 8/12 staff, 12/16 student; help muted 14px; error 600 + 20px icon; invalid 2px error | `form_field.css:4-51`; `test_molecule_assets.py:144`; icon `form_field.html:7` |
| Story DT — Pair | two equal columns, 24px gap, labelled Română/English | `form_field.css:65-75` (`gap: var(--grid-gutter)`; the `.field-pair__lang` gap was added at integration); `test_molecule_assets.py:157` |
| Story DT — Alert | 4px left border + tints (info/success/warning/error), text colour, icons bell/check-circle/warning-circle, close ≥32px | `alert.css:4-27,33-49`; `ui.py:182-187`; `test_molecule_assets.py:111,125,131` |
| Story DT — Card | surface, radius, elevation-1, padding 24/32, hover elevation-2 + focus ring | `card.css:3-9,36-42`; `test_molecule_assets.py:62,70,91` |
| Story DT — Disabled tile | bg disabled, text muted, dashed 1px border, lock-simple 20, "Unavailable" | `disabled_tile.css:11-16`; `disabled_tile.html:2-4`; `test_molecule_assets.py:163` |
| Story DT — Empty state | centred, icon 32 duotone (student) / regular (staff), muted, optional primary button | `empty_state.css:2-15`; `empty_state.html:2`; `ui.py:280-284`; `test_styleguide.py:301` (student `list-checks-duotone`, staff `list-checks`) |
| Story DT — Page header | h1 32/700 student, 24/700 staff; breadcrumb 14px muted with caret-right; actions right | `page_header.css:10-44`; `page_header.html:4`; `test_molecule_assets.py:177` |
| Story DT — Dialog | surface, radius, elevation-3, max 480px, backdrop rgba(31,41,55,.5), confirm primary/danger | `confirm_dialog.css:3-14`; `tokens.css:62`; `test_design_assets.py:113` (`--color-backdrop`); `test_molecule_assets.py:188`; variants `ui.py:306-309` |
| Story DT — Table | header bg staff, 600; row border disabled; padding 8/12; caption left 16/600; full width ≤1200 | `table.css:2-26`; `test_molecule_assets.py:197` |
| Story DT — Validation | on submit; inline error + top banner `ui_alert "error"` | inline: `form_field.html:6-7`; banner: `ui_alert "error"` `role="alert"` (`alert.html:1`); styleguide shows both (`_molecules.html:6,17`) |
| Story System responses table (13 rows) | unbound no aria-invalid; bound → `aria-describedby="id_username_error"` only; pair; `"fatal"` → ValueError; dismiss / dismiss again no-op; trigger opens; trigger while open no-op; Esc closes no submit; Confirm POSTs with CSRF+hidden; empty rows → no `<table>`; dict → `ValueError("Unsupported cell")`; Tab skips tile | `test_molecules.py:41,163,60,79,84`, `test_molecules_layout.py:107,209` (message starts "Unsupported cell"); `ui.js:25,37,43` (`!dialog.open`, `?.close()`, `?.remove()`); `test_molecules.py:129` |
| Story QA-observable | `lang` on pair inputs; focus back on trigger after Esc; tile `aria-disabled`, no a/button; empty table has 0 `<table>`; error/login pages show card styling + error banner colours; nothing else changes | `test_styleguide.py:188` (markers incl. `<table` ×1 per theme); `ui.js:49-52`; `test_molecules.py:84`; `test_base_layout_styles.py:24,49,56`; curl above |
| Story RBAC | components never decide access; dialog always renders `{% csrf_token %}`; no new routes | `confirm_dialog.html:3`; `test_molecules.py:94`; Gate 2: `git diff main -- src/config/urls.py …/urls.py decorators.py` empty |
| Story Edge | no JS → trigger is `type=button` + noscript note; alert stays visible | `dialog_trigger.html:1-2`; `test_molecules.py:106`; `alert.html` (no hidden state) |
| Story Quality | ruff 0, mypy, coverage ≥85, tokens only, no inline style/script, no `|safe`, no `!important`, ui.js no globals/eval, no TODO, files ≤400, functions ≤30 | gates above; Gate 2; `ui.py` 398 lines; largest function 27 lines (`ui.py`), 26 (`views.py`) |
| Story OUT | ui.js/htmx not in `base.html`; no feature dialog content; no JS tooling; no toasts | `base.html:1-19` has no `<script`; `test_base_layout_styles.py:65` |
| Story "What does NOT change" | atoms untouched, no DB, no new routes, dialog adds no server behaviour | Gate 2 (atom template/CSS diff empty; ui.py no removed lines); `test_styleguide.py:126` (no DB queries); `test_atoms.py` green |
| ui-ux-spec `component_map` / `ux_logic` / `patterns` | forms: form_field; tables: data_table; modals: confirm_dialog; notifications: alert; `error_display: inline+top_banner`; `confirm: [test_submit, block, clear, publish]` (dialog with own form + `extra_template`); `empty_states: all_lists` (table → empty state); `editors: ro_en_side_by_side` (field pair) | `templates/components/*.html`; `ui.py:339-361` (`extra_template`); `table.html:8`; `field_pair.html` |
| ui-ux-spec `a11y` | AA contrast (pre-verified pairs reused); `focus: 3px_outline`; `aria_labels: required`; `sr: [semantic_html, aria_live, lang]`; `keyboard: dialog_trap_esc` | `test_design_assets.py:231` (contrast pairs); `card.css:37-40`; `alert.html:4`, `page_header.html:2`; alert `role` live regions `ui.py:254`; `lang` `ui.py:217`; native `showModal()` `ui.js:27` (modal → inert background, Esc → `cancel`) |
| 08-visual-foundation | molecules list (form_field, alert, card, disabled_tile, empty_state, page_header, confirm_dialog, data_table); elevation 1/2/3; icon sizes 20/24/32; grid gutter 24 | `templates/components/`; `card.css:6,36`, `confirm_dialog.css:12`; icon sizes via `ui_icon` (`ui.py:50`); `form_field.css:68` |
| Patterns §11.1 | no inline `style=`, `<style>`, `<script>` | `test_atoms.py` style/safe rule; `test_inline_script.py:59,68`; Gate 2 |
| Patterns §11.2 | primitives only in `components/` + `ui.py` + `css/components/`; styleguide shows every primitive | file locations; `test_styleguide.py:188` |
| Patterns §11.3 | every UI string via `{% translate %}`/`gettext_lazy`; English ids; full RO | `test_design_assets.py:343`; `views.py` uses `_()` (and `gettext` per request for `Cell` text) |
| Patterns §11.4 | labels on every input; status not by colour alone; focus kept; buttons `<button>`, links `<a>`; `lang` | `form_field.html:2`; pill keeps its word (`table.html:5` → `ui_status_pill`); `card.css:37-42`; `dialog_trigger.html:1`, `page_header.html:10` |
| Patterns §7.4 | no inline script, no `hx-on`, JS only as `static/js/` module, no CDN | `ui.js`; `index.html:25`; `test_inline_script.py`; `test_molecule_assets.py:212` |
| Patterns §13 | autoescape; `{% csrf_token %}` in forms; local assets only | `test_molecules.py:324`, `test_molecules_layout.py:185,200`; `confirm_dialog.html:3`; `test_atoms.py` external-URL test |
| Patterns §12 / §17 | AAA, behavioural names; ≤400 lines/file, ≤30 lines/function; no TODO/print | `test_molecules.py` split into 2 files; Gate 2 `wc -l` and TODO greps |
| Story 1.5 conventions | `TagContext` returns, `ValueError`/`TemplateSyntaxError`, reuse `BUTTON_VARIANTS`, `ICON_NAMES` fixed | `ui.py:306-309`; `test_design_assets.py:261` (sprite still exactly 25 icons) |
| Story 1.1 hooks | `error-card`, `error-card__violations`, `error-card__ref`, `error-partial` styled | `card.css:3-13,45-53`; `alert.css:4,15,19-22,28-32`; real 404 page links them (curl above) |
| Story 1.2 hooks | `login-card`, `form-banner`, `form-banner--error`, `field-error` styled | `card.css:3-13`; `alert.css:4,19-22`; `form_field.css:4-35,44-52`; `test_base_layout_styles.py:56` |
| Story 1.3 ISS-004 | DEBUG=True URLConf walk with explicit `DEBUG_ONLY_URL_NAMES = {"styleguide:index"}`; non-vacuous and stale-checked allow-list; production routing restored | `test_url_protection.py:42` (allow-list), `:54-64` (`_unprotected(..., allowed)`), `:75-121`, `:290`; review doc `docs/reviews/story-1.3-code-review-v1.md` ISS-004 Resolution (status ✅ Resolved; banner updated with 980/980) |

### Gate 2 — Negative-Space Check

```
$ grep -rn "|safe\|mark_safe\|style=\|!important" templates/components templates/styleguide static/css/components static/js
exit=1 (1 = no match)
$ grep -rnE "#[0-9a-fA-F]{3,8}\b|rgba?\(" static/css/components static/css/styleguide.css
exit=1
$ grep -rn "<style" templates/components templates/styleguide templates/layouts
exit=1
$ grep -rnE "<script" src/infrastructure/web/templates        # only the external module in the styleguide
src/infrastructure/web/templates/styleguide/index.html:25:  <script type="module" src="{% static 'js/ui.js' %}"></script>
$ grep -rnE "\son[a-z]+\s*=" templates/components templates/styleguide templates/layouts
exit=1
$ grep -rnE "https?://" templates/components templates/styleguide templates/layouts static/css static/js
exit=1
$ grep -nE "eval\(|new Function|window\.|globalThis|innerHTML|^\s*import |\bvar " static/js/ui.js
exit=1
$ grep -rnE "TODO|FIXME|print\(" (ui.py, styleguide/, components, styleguide templates, molecule CSS, js, ui tests, test_url_protection.py)
exit=1
$ grep -rn "csrf_exempt\|objects\.\|connection" templatetags/ui.py styleguide/*.py
exit=1
$ git diff --stat main -- src/config/urls.py 'src/infrastructure/web/*/urls.py' src/infrastructure/web/common/decorators.py
(empty = route catalogue and PUBLIC_URL_NAMES unchanged)
$ git diff main -- src/infrastructure/web/templatetags/ui.py | grep "^-[^-]"
exit=1 (no Story 1.5 line removed or changed)
$ git diff --stat main -- templates/components/{button,icon,badge,status_pill,avatar,score,progress_meter,language_switcher}.html static/css/components/{…same}.css
(empty = atoms untouched)
$ git diff --stat main -- templates/accounts templates/errors
(empty = Story 1.1/1.2 templates untouched)
$ git diff main -- static/css/tokens.css
+  --color-backdrop: rgba(31, 41, 55, .5); /* dialog backdrop (Story 1.6 Design Tokens) */   (only addition)
$ wc -l (largest story files)
355 test_atoms.py · 383 test_design_assets.py · 398 ui.py · 347 test_molecules.py · 261 test_molecules_layout.py   (all ≤ 400)
```
Tests that fail if any rule is violated: `test_inline_script.py:49` (7 inline variants, each must be caught) and `:53` (an external module and `<noscript>` are allowed); `test_inline_script.py:68` (the only script is the same-origin ui.js module); `test_base_layout_styles.py:65` (no script in base before Story 1.7); `test_molecule_assets.py:50` (no hex, no `rgba(`, no `!important` per molecule sheet); `test_design_assets.py:301` (no raw hex in any stylesheet except tokens.css); `test_styleguide.py:126` (no DB access); `test_styleguide.py:321` (404 when DEBUG=False); `test_url_protection.py:95,102` (no unguarded DEBUG-only route except the allow-list).

### Gate 3 — Contract Consistency

| Layer A | Layer B | Check | Result |
|---------|---------|-------|--------|
| Component markup (a) class names | Molecule CSS selectors (b) | Script: every class in the 10 molecule templates has a `.class` rule in `css/components/*.css`, and every class selector in the 8 molecule sheets appears in a template | 52 template classes, 0 without a rule (only the template-variable fragments `alert--{{ level }}` and `button--{{ variant }}`, covered by `.alert--info/success/warning/error` and button.css). 0 unused selectors except `theme-student`, which the styleguide renders as `theme-{{ theme }}` |
| Markup `data-*` hooks | `ui.js` selectors | `data-dialog-open=` (`dialog_trigger.html:1`) ↔ `[data-dialog-open]` + `dataset.dialogOpen` (`ui.js:22-24`); `data-dialog-close` (`confirm_dialog.html:9`) ↔ `ui.js:35`; `data-dismiss` in `.alert` (`alert.html:4`) ↔ `ui.js:41-43` | match |
| Molecule CSS `var(--…)` | `tokens.css` definitions | Script: tokens used by the 8 molecule sheets + styleguide.css vs `--name:` declared in tokens.css | 52 used, 0 undefined |
| Story AC tag signatures | `ui.py` signatures | `ui_field(field, help="")` :229 · `ui_field_pair(field_ro, field_en)` :235 · `ui_alert(level, message, dismissible=True)` :245 · `ui_card(title, body="", href=None, icon=None, meta="")` :259 · `ui_disabled_tile(title, reason="")` :275 · `ui_empty_state(message, action_label="", action_url="", icon="list-checks")` :288 (+context) · `ui_page_header(title, breadcrumbs=(), actions=())` :320 · `ui_confirm_dialog(dialog_id, title, body, confirm_label, action, confirm_variant="primary", hidden=None, extra_template=None)` :340 · `ui_dialog_trigger(dialog_id, label, variant)` :365 · `ui_table(columns, rows, caption, empty_message)` :384 (+context) | match. `takes_context` reads `icon_variant` only (default `regular`); no silent defaults beyond the story's |
| Invalid inputs (story) | Behaviour | unknown alert level, unknown cell type (incl. `bool`, `None`, `float`, `dict`), unknown pill, Cell with both href and pill, row width ≠ columns, bad dialog id, script-scheme URLs → `ValueError`; unknown button/action variant → `TemplateSyntaxError` (same as `ui_button`) | each has a test (`test_molecules.py:79,194,248,313,319`; `test_molecules_layout.py:52,88,94,99,143,149,154,172,177,209,214,219,226,233,249`). Nothing is silently accepted |
| Template msgids | RO/EN catalogues | `test_design_assets.py:343` globs components + styleguide templates + `ui.py` + `views.py` `_()` ids | all present, non-empty in both; 0 fuzzy |
| Story 1.1/1.2 hook markup | Linked CSS on those pages | `login.html` (`login-card`, `form-banner--error`, `field-error`, `ui_icon`, `ui_button`) and `_error.html` (`error-card`, `icon`, `error-card__violations`, `error-card__ref`) ↔ `base.html:10-14` links icon/button/card/alert/form_field | all used classes are covered by a linked sheet (`test_base_layout_styles.py:24,49,56`). `error-partial` is an HTMX fragment swapped into a page that already has `alert.css` |
| Styleguide `MOLECULE_MARKERS` (both themes) | Rendered page | `test_styleguide.py:188` exact counts per theme; `:268` all molecule ids unique and every `for`/`aria-labelledby`/`aria-describedby`/`data-dialog-open` reference resolves | pass |
| `DEBUG_ONLY_URL_NAMES` | Routes registered only under DEBUG=True | `test_url_protection.py:95,102,114` (exactly `styleguide:index`, exists only under DEBUG) | pass |

## Challenges Encountered

| Challenge | Resolution | Time Spent |
|-----------|------------|------------|
| `test_atoms.py` banned every `<script`, but AC 12 needs an external module | Narrowed the rule to inline code: a script without `src`, a script body, an unclosed tag, or an `on*=` handler. A proof test shows 7 inline variants are still caught. The only script allowed is the same-origin `ui.js` module | 0.3 h |
| `test_styleguide_is_deterministic` broke: the dialog's `{% csrf_token %}` is re-masked on every response | The test now normalises only the `csrfmiddlewaretoken` value. Everything else must still be byte-identical | 0.1 h |
| Atom count tests (`button--primary` ×12, pills ×2) were inflated by molecules that reuse atoms | `without_molecules()` strips the `.sg-molecules` blocks for the atom counts. Molecules have their own exact per-theme counts | 0.2 h |
| makemessages fuzzy-matched 6 new ids (e.g. "Publish" → "Publicat") | Reviewed each and corrected it, removed the flags and `#|` lines, and confirmed no existing msgstr changed | 0.2 h |
| `Cell.text: str` vs a lazy translation (mypy) | Table rows are built per request with `gettext` | 0.1 h |
| DEBUG=True dev server shows Django's technical 404 | Verified `errors/404.html` on a temporary DEBUG=False server (scratch settings module, `--insecure`), with no repo change | 0.1 h |

## Deviations from Plan

1. **USER DECISION (2026-10-22) "Add the links now"**: `layouts/base.html` (not in Files Touched, owned by Story 1.7) now links `icon.css`, `button.css`, `card.css`, `alert.css` and `form_field.css`. These are exactly the sheets the sign-in, lockout and error pages use, so those pages are styled today (QA observable "error pages and sign-in page now look styled"). It is one commented block; Story 1.7 builds the full layout on top. `ui.js` is **not** in base.html (story OUT: Story 1.7).
2. **New token** `--color-backdrop: rgba(31, 41, 55, .5)` in `tokens.css` (Story Design Tokens: dialog backdrop). Added to `SPEC_TOKENS` in `test_design_assets.py` with its source.
3. **`test_atoms.py` script rule refined** (see Challenges). The narrowed rule and its proof tests live in the new `tests/integration/web/ui/test_inline_script.py`, which keeps `test_atoms.py` at 355 lines (≤400). The style, `|safe` and `mark_safe` rules are unchanged.
4. **Extra test files** beyond Files Touched: `test_molecule_assets.py` (component b, so a and b had disjoint file sets), `test_molecules_layout.py` (integration split of component a's 588-line `test_molecules.py` at its `# --- ui_empty_state` section boundary, keeping both under the §17 400-line limit; all 80 tests unchanged), `test_inline_script.py` and `test_base_layout_styles.py`.
5. **Extra component templates**: `field_pair.html` and `dialog_trigger.html` (separate inclusion tags need separate templates).
6. **Component validation stricter than the story** (component a): script-scheme `href`/`action`/`Cell.href` rejected; dialog id pattern; unknown variants raise; row/column count; `Cell` is a link xor a pill. All styleguide samples respect these.
7. **`test_styleguide_is_deterministic`** now normalises the per-response CSRF token (see Challenges).
8. **Integration fixes in component files** (each small):
   - `static/js/ui.js:28-30`: the first-focus call skipped nothing, and the first `input` in every confirm dialog is the hidden CSRF input. `.focus()` on that is a no-op, so the code's explicit focus never ran; only native `showModal()` focused Cancel. Hidden inputs are now skipped. The selector literal `input, textarea, select, button` is kept, as `test_molecule_assets.py` asserts.
   - `static/css/components/form_field.css:72`: `.field-pair__lang { margin-left: var(--space-2) }`, a gap between the label text and the language name.
   - `form_field.css:1`: header comment tag name fixed (`{% ui_form_field %}` → `{% ui_field %}`).
9. **ISS-004 (Story 1.3 review)** resolved here: `tests/integration/web/test_url_protection.py` and `docs/reviews/story-1.3-code-review-v1.md` (component c). The banner and addendum now carry the full-suite count 980/980.
10. **Styleguide-only a11y notes (not changed)**: the page-header sample renders a second `<h1>` per theme. This is unavoidable when showing the real component. Also, the Story 1.5 atom progress samples share `id="progress-exercises"` (6×). That id comes from the atom's own markup, and "atom output untouched" applies. The new duplicate-id test therefore covers molecule ids only (`test_styleguide.py:268`). Suggest a follow-up in Story 1.7/1.10 if desired.
11. **Evidence**: no screenshots, keyboard step log or VoiceOver notes. This run had no browser, so curl/HTML evidence and tests stand in (see DoD Evidence). The Manual checks remain for a human before QA sign-off.

## Lessons Learned

1. Determinism tests over pages with forms must account for CSRF masking. A future feature page snapshot test needs the same normalisation.
2. Counting atom markers on a page that also renders molecules needs scoping. Composite primitives reuse atoms by design.
3. Always review makemessages fuzzy matches by hand. "Publish" silently inherited "Publicat" ("Published").

## Next Steps

- [ ] Ready for code review (`aire-review-code`)
- [ ] Manual browser pass (both themes): dialog keyboard flow, alert dismissal, Tab skipping the tile, VoiceOver, screenshots
- [ ] Ready for Unit test validation
