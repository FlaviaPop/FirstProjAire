# Story 1.5 Self-Review

**Date**: 2026-10-21
**Story**: Design Tokens & Atom Primitives (CYCLE-1, wave 2, Dev 1)
**Developer**: DEV Agent (story-agent, in-one-go wave mode)
**Branch**: `worktree-agent-af6cc2198ab13f1c6` (based on `feature/wave-2-dev-1` @ 179c213)

---

## What Was Implemented

- `tokens.css` completed. All seeded properties are kept unchanged; the additions are appended: `@font-face` ×3 (400/600/700, `font-display: swap`), the `.theme-student`/`.theme-staff` role tokens, base `body`/heading styles, a `:focus-visible` 3px focus ring, `.visually-hidden`, and the reduced-motion override.
- Self-hosted **Atkinson Hyperlegible Next** 400/600/700 woff2 files and `OFL.txt`, taken from the upstream `googlefonts/atkinson-hyperlegible-next` repo (`fonts/webfonts/`, v2.66). fontTools confirmed that all three weights map ș ț ă â î Ș Ț Ă Â Î, plus the cedilla forms ş ţ Ş Ţ, so the system-font fallback is never needed.
- Local **Phosphor 2.1.1** sprite (`static/icons/sprite.svg`) with 25 regular and 25 `-duotone` symbols for exactly `ICON_NAMES`, plus the MIT `LICENSE`.
- 7 inclusion tags in `templatetags/ui.py`: `ui_button`, `ui_icon`, `ui_badge`, `ui_status_pill`, `ui_avatar`, `ui_score`, `ui_progress`. Each has a template in `components/` and its own stylesheet in `static/css/components/`.
- A DEBUG-only `/<lang>/_styleguide/` page (`styleguide:index`) showing every atom and variant in both themes, with token swatches (hex plus computed contrast), spacing, and the type scale with the diacritics line.
- 39 new msgids, appended to both the `ro` and `en` catalogues.

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `src/infrastructure/web/static/css/tokens.css` | Modified (append only) | font faces, themes, base styles, focus, visually-hidden, reduced motion |
| `src/infrastructure/web/static/fonts/AtkinsonHyperlegibleNext-{Regular,SemiBold,Bold}.woff2`, `OFL.txt` | New | self-hosted font + SIL OFL 1.1 |
| `src/infrastructure/web/static/icons/sprite.svg`, `LICENSE` | New | Phosphor 2.1.1 sprite (50 symbols) + MIT licence |
| `src/infrastructure/web/static/css/components/{button,icon,badge,status_pill,avatar,score,progress_meter}.css` | New | one stylesheet per atom, tokens only |
| `src/infrastructure/web/static/css/styleguide.css` | New | styleguide-only layout (tokens only) |
| `src/infrastructure/web/templates/components/{button,icon,badge,status_pill,avatar,score,progress_meter}.html` | New | atom templates |
| `src/infrastructure/web/templatetags/ui.py` | Modified | catalogues + 7 inclusion tags with validation |
| `src/infrastructure/web/styleguide/{__init__,views,urls}.py` | New | DEBUG-only styleguide view |
| `src/infrastructure/web/templates/styleguide/{index,_atoms}.html` | New | styleguide page; Story 1.6 adds `_molecules.html` |
| `src/config/urls.py` | Modified (shared) | `include` added to the import, `settings` import, appended `if settings.DEBUG:` block |
| `src/infrastructure/i18n/locale/{ro,en}/LC_MESSAGES/django.po` | Modified (shared, append only) | 39 entries under `# --- Story 1.5 ---` |
| `tests/integration/web/ui/test_atoms.py` | New | 60 tests: every tag, valid and invalid input, escaping, external-URL/inline-style greps |
| `tests/integration/web/ui/test_design_assets.py` | New | 116 tests: tokens vs. spec, themes, base CSS, WCAG contrast, fonts, sprite, component CSS rules, catalogues |
| `tests/integration/web/ui/test_styleguide.py` | New | 16 tests: both themes, RO/EN, counts, determinism, no DB, 404/NoReverseMatch in prod, real root URLConf under DEBUG |
| `docs/stories-implemented/story-1.5-evidence/*.png` | New | screenshots (focus ring, typography/diacritics, staff theme) |

## Patterns Applied

| Pattern | Where Applied | Notes |
|---------|---------------|-------|
| §11.2 UI Primitive Catalogue | `components/`, `templatetags/ui.py`, `static/css/components/` | shared library locations only; styleguide under `infrastructure/web/styleguide/` |
| §11.1 Templates | component templates | no inline `style`, `<style>` or `<script>` |
| §11.3 i18n | `gettext_lazy` in Python, `{% translate %}`/`{% blocktranslate %}` in templates | English msgids, full RO translation |
| §11.4 Accessibility | focus ring, pills with words, `<button>`, labelled icons/avatar/score/progress, body ≥16px | |
| §12 Testing | `tests/integration/web/ui/` | AAA, behavioural names, written first (red run below) |
| §13 Security | autoescape everywhere; no `|safe`/`mark_safe`; local static only | `hx_on*` passthrough rejected (inline-script vector) |

## Testing Summary

- **New tests**: 192 (60 + 116 + 16), all passing. Suite total: 222 (30 existing + 192).
- **Coverage**: 100.00% overall (target 85%). `ui.py` and `config/urls.py` are both at 100% lines and branches. `styleguide/*` is omitted by the seeded coverage config (patterns §12.6). This story adds no code to `src/domain` or `src/application`.
- **TDD red run** (tests written before implementation): `54 failed, 6 passed` for `test_atoms.py`; `test_design_assets.py` and `test_styleguide.py` failed at collection (`ModuleNotFoundError: No module named 'infrastructure.web.styleguide'`).

**Test output** (`uv run pytest --cov=src --cov-branch --cov-fail-under=85`, verbatim excerpt; per-file 100% rows for files untouched by this story omitted):
```
tests/integration/persistence/accounts/test_user_model.py ........       [  3%]
tests/integration/web/test_healthz.py .........                          [  7%]
tests/integration/web/test_role_access_matrix.py .                       [  8%]
tests/integration/persistence/accounts/test_restart_persistence.py ..... [ 10%]
tests/integration/web/ui/test_atoms.py ................................. [ 25%]
tests/integration/web/ui/test_design_assets.py ......................... [ 48%]
tests/integration/web/ui/test_styleguide.py ................             [ 96%]
tests/unit/config/test_env.py .......                                    [100%]
src/config/urls.py                                        8      0      2      0   100%
src/infrastructure/web/templatetags/ui.py                55      0     16      0   100%
TOTAL                                                   125      0     22      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
============================= 222 passed in 1.70s ==============================
```

## DoD Evidence

### Quality gates (run 2026-10-21, verbatim)

```
$ uv run ruff format --check .
41 files already formatted
[exit 0]
$ uv run ruff check .
All checks passed!
[exit 0]
$ uv run mypy
Success: no issues found in 45 source files
[exit 0]
$ PYTHONPATH=src uv run lint-imports
Analyzed 37 files, 37 dependencies.
Layers point inward KEPT
Domain is framework-free KEPT
Contracts: 2 kept, 0 broken.
[exit 0]
$ uv run python manage.py makemigrations --check --dry-run
No changes detected
[exit 0]
$ uv run pytest --cov=src --cov-branch --cov-fail-under=85
Required test coverage of 85% reached. Total coverage: 100.00%
============================= 222 passed in 1.70s ==============================
[exit 0]
```

### Asset verification (verbatim)

```
$ uvx --from fonttools --with brotli python -I check_glyphs.py <3 woff2 files>   # checks șțăâîȘȚĂÂÎşţŞŢ
AtkinsonHyperlegibleNext-Regular.woff2: weight=400 glyphs=362 missing=none
AtkinsonHyperlegibleNext-SemiBold.woff2: weight=600 glyphs=362 missing=none
AtkinsonHyperlegibleNext-Bold.woff2: weight=700 glyphs=362 missing=none
$ build_sprite.py <phosphor 2.1.1 assets> static/icons/sprite.svg
25 names, 50 symbols, 24695 bytes
```

### Manual / browser checks (`DJANGO_SETTINGS_MODULE=config.settings.dev runserver`, DEBUG=True)

```
$ curl /ro/_styleguide/ → ro 200
$ curl /en/_styleguide/ → en 404     (no LocaleMiddleware until Story 1.4; see Deviations)
css/tokens.css 200 text/css
css/components/button.css 200 text/css
icons/sprite.svg 200 image/svg+xml
fonts/AtkinsonHyperlegibleNext-Regular.woff2 200 font/woff2
fonts/AtkinsonHyperlegibleNext-SemiBold.woff2 200 font/woff2
fonts/AtkinsonHyperlegibleNext-Bold.woff2 200 font/woff2
```

Playwright driving the system Chrome (`channel="chrome"`) on `/ro/_styleguide/` (verbatim JSON):
```
"primary_bg": "rgb(14, 116, 144)", "primary_fg": "rgb(255, 255, 255)",
"student_button_height": 46.796875, "staff_button_height": 43.59375,
"student_radius": "16px", "staff_radius": "8px",
"student_bg": "rgb(255, 248, 236)", "staff_bg": "rgb(245, 247, 250)",
"body_font": "\"Atkinson Hyperlegible Next\", system-ui, sans-serif",
"loading": {"disabled": true, "busy": "true", "pointer_events": "none",
            "spinner_display": "block", "spinner_animation": "button-spin"},
"blocked_pill": {"bg": "rgb(254, 226, 226)", "fg": "rgb(127, 29, 29)", "text": "Blocked"},
"fonts": {"faces": ["400:loaded", "600:loaded", "700:loaded"], "check": true},
"focus": {"element": "button button--primary", "outline": ["solid", "3px", "rgb(194, 65, 12)", "2px"]},
"request_hosts": ["127.0.0.1:8767"],
"reduced_motion_spinner": ["none", "rgb(75, 85, 99)", "rgb(75, 85, 99)"]
```
Screenshots: `docs/stories-implemented/story-1.5-evidence/styleguide-ro-focus.png` (3px orange ring on the first primary button), `styleguide-ro-typography.png` (diacritics line at every size and weight in Atkinson Hyperlegible Next), `styleguide-ro-staff.png` (staff theme section). The network panel is represented by `request_hosts`: every request went to the same origin. The pill text reads "Blocked" on `/ro/` because the `.mo` catalogues aren't compiled (see Challenges).

### Gate 1 — Spec Echo

| # | Requirement | Proof |
|---|-------------|-------|
| AC1 | `tokens.css` keeps every seeded property (no renames) | `git diff 179c213 -- tokens.css \| grep '^-'` → 0 removed lines (Gate 2); `test_root_token_matches_the_approved_spec` ×58 |
| AC1 | pill pairs `--pill-{state}-bg/fg`, `--line-height-body: 1.6`, `--line-height-heading: 1.25` | Already seeded at `tokens.css:20-25,51-52` with the spec values, so they weren't duplicated; asserted by `test_root_token_matches_the_approved_spec` |
| AC1 | `@font-face` 400/600/700 with `font-display: swap` | `tokens.css:74-94`; `test_font_face_is_self_hosted_with_swap[400/600/700]`; browser `faces: 400/600/700 loaded` |
| AC1 | `.theme-student`/`.theme-staff` define `--font-size-base`, `--radius`, `--bg`, `--touch` (+ `--icon-variant`) | `tokens.css:98-111`; `test_theme_class_sets_the_role_dependent_tokens` |
| AC1 | `body` font-family/size/colour/background/line-height | `tokens.css:114-121`; `test_body_uses_the_tokens_for_font_colour_background_and_line_height`; browser `body_font` |
| AC1 | `:focus-visible` 3px `--color-focus`, offset 2px | `tokens.css:123`; `test_focus_visible_is_a_3px_focus_colour_outline_with_2px_offset`; browser outline `solid 3px rgb(194, 65, 12) 2px` |
| AC1 | `.visually-hidden` | `tokens.css:124-132`; `test_visually_hidden_utility_hides_visually_but_not_from_screen_readers` |
| AC1 | reduced motion disables animations | `tokens.css:135-140`; `test_reduced_motion_disables_animations_and_transitions`; browser `reduced_motion_spinner[0] = "none"` |
| AC2 | 3 woff2 files + `OFL.txt` in `static/fonts/` | `test_font_file_is_a_committed_woff2` ×3 (magic `wOF2`), `test_font_licence_is_shipped_alongside` |
| AC2 | Romanian glyphs verified; fallback rule | fontTools `missing=none` for all weights; screenshot `styleguide-ro-typography.png`; `document.fonts.check(...) = true`. No glyph missing, so no fallback was needed; `--font-family` keeps `system-ui, sans-serif` as its tail |
| AC3 | sprite has regular + `-duotone` symbols for exactly `ICON_NAMES` (25) | `test_sprite_has_regular_and_duotone_symbols_for_exactly_the_icon_names` |
| AC3 | `LICENSE` (MIT) next to the sprite | `static/icons/LICENSE`; `test_icon_licence_is_shipped_alongside` |
| AC3 | duotone uses `fill="currentColor"` + 0.2 layer filled with `var(--color-accent)` via a CSS class | `sprite.svg:3` `<style>.icon-duotone-layer {…}</style>`; `test_duotone_layer_is_accent_filled_at_twenty_percent_via_a_class` |
| AC4 | `ui_button(label, variant, type, icon, name, value, **hx)`; `hx_` → `hx-`; other kwargs → `TemplateSyntaxError`; spinner span | `ui.py:70-105`, `button.html`; `test_button_passes_through_only_hx_attributes_escaped`, `test_button_rejects_non_hx_attributes`, `test_primary_button_has_spinner_and_label` |
| AC4 | `ui_icon(name, size=24, variant="regular", label="")` | `ui.py:62-67`; `test_icon_*` (9 tests) |
| AC4 | `ui_badge(value, label)` | `ui.py:108-112`; `test_badge_shows_number_and_full_meaning_for_screen_readers` |
| AC4 | `ui_status_pill(status)`, six statuses, RO labels Activ/Semnalat/Blocat/Retrimis/Ciornă/Publicat | `ui.py:48-55,116-120`; `test_status_pill_always_shows_a_word` ×6; `test_romanian_translation_matches_the_story` |
| AC4 | `ui_avatar(user)`, `ui_score(value)`, `ui_progress(done, total, label)` | `ui.py:124-145`; avatar/score/progress tests |
| AC5 | invalid input raises per the display matrix | unknown icon/size/variant → `ValueError` (`test_icon_rejects_unknown_inputs`); unknown variant / non-hx kwarg → `TemplateSyntaxError`; badge <0 → `ValueError`, 0 → nothing; unknown status → `ValueError`; avatar without a name → "User" (`test_avatar_without_a_name_falls_back_to_user` ×3); score outside 1–100 → `ValueError`; progress done>total or negative → `ValueError`, total 0 → "0/0" `max="1"` |
| AC6 | `.button.htmx-request` shows the spinner and sets `pointer-events: none` | `button.css:34-35`; `test_button_loading_state_shows_spinner_and_blocks_pointer`; browser `pointer_events: none`, `spinner_display: block` |
| AC6 | `hx_disabled_elt="this"` passthrough | `test_button_passes_through_only_hx_attributes_escaped` (`hx-disabled-elt="this"`) |
| AC6 | reduced motion → static ring | `button.css:38-40` (full ring) + `tokens.css:135-140` (animation none); browser `["none", rgb(75,85,99), rgb(75,85,99)]` (right border = top border, so the ring is closed) |
| AC7 | one CSS file per atom in `static/css/components/`, tokens only, no raw hex, no `!important` | 7 files; `test_each_atom_has_its_own_stylesheet_built_only_on_tokens` ×7; `test_stylesheets_outside_tokens_never_use_raw_hex`; Gate 2 greps |
| AC8 | `styleguide:index` in `i18n_patterns` only `if settings.DEBUG` | `config/urls.py:17-22`; `test_root_urlconf_registers_styleguide_when_debug_is_true[ro/en]` (reloads the real ROOT_URLCONF with DEBUG=True) |
| AC8 | renders every atom/variant in `.theme-student` and `.theme-staff`, RO/EN by prefix | `test_styleguide_renders_all_atoms_in_both_themes[ro/en]`, `test_styleguide_shows_every_variant_twice`, `test_styleguide_language_follows_the_url_prefix[ro/en]` (`<html lang>`) |
| AC8 | DEBUG=False → `NoReverseMatch` and `/ro/_styleguide/` 404 | `test_styleguide_is_not_routed_when_debug_is_false`, `test_styleguide_returns_404_in_production[ro/en]`, `test_production_routing_is_restored_after_the_debug_reload` |
| AC9 | no `http://`/`https://` in `templates/components`, `templates/styleguide`, `static/css` | `test_no_component_or_css_references_external_urls`; `test_sprite_only_mentions_the_svg_namespace_url`; Gate 2 grep |
| AC10 | every new UI string in both catalogues with RO | `test_every_new_ui_string_is_in_the_catalogue[ro/en]` (scans the templates and `_("…")` calls); `.po` tail block |
| Step 1 | tests first | red run recorded in Testing Summary |
| Step 2 | tokens & themes appended, seeded variables unchanged | `tokens.css:72-140`; AC1 rows |
| Step 3 | sprite with `viewBox="0 0 256 256"` symbols, `LICENSE`, leading version/name comment | `sprite.svg:1`; `test_sprite_starts_with_a_comment_naming_version_and_icons` |
| Step 4 | inclusion tags as specified (`ICON_NAMES`, `ICON_SIZES`, `BUTTON_VARIANTS`, `STATUS_LABELS`; avatar label `get_full_name() or _("User")`) | `ui.py:15-145` |
| Step 5 | component templates, no inline style, autoescaped | `templates/components/*.html`; `test_component_and_styleguide_templates_have_no_inline_style_script_or_safe` ×5; `test_button_label_name_and_value_are_autoescaped` |
| Step 6 | component CSS per atom (button excerpt) | `button.css:1-40` |
| Step 7 | styleguide views/urls (`app_name="styleguide"`), `index.html` loops themes and includes `_atoms.html`, diacritics sample | `styleguide/urls.py:5`, `views.py`, `index.html:21-28`; `test_styleguide_shows_the_type_scale_sample_with_diacritics` |
| Step 8 | translations: pills, "Score: %(value)s out of 100" → "Punctaj: %(value)s din 100", "User" → "Utilizator", headings | `ro/django.po` Story 1.5 block; `test_romanian_translation_matches_the_story` ×8 |
| Step 9 | all gates + browser screenshots | Quality gates + Manual/browser checks above |
| Ref: UI/UX colours (14) | exact hex values | `tokens.css:4-17`; `test_root_token_matches_the_approved_spec` |
| Ref: pills bg/fg (6 pairs), "≥ 8:1" | exact values; contrast | `tokens.css:20-25`; `test_colour_pair_meets_wcag_aa` (pill rows); styleguide shows 8.14–13.34:1 |
| Ref: spacing 4px unit, student/staff scales | `--space-1…16` | `tokens.css:28-35`; tests |
| Ref: typography (font, 18/16 base, 14–40 scale, 400/600/700, lh 1.6/1.25) | tokens + font faces | `tokens.css:38-52,74-94`; tests |
| Ref: radius 16/8/999; elevation 0–3 | tokens; theme `--radius` | `tokens.css:55-61`; browser radius 16px/8px |
| Ref: touch min 32px, student controls 44px | `--touch` per theme; `.button { min-height/min-width: var(--touch, var(--touch-min)) }` | `button.css:7-8`; browser 46.8px / 43.6px |
| Ref: icons Phosphor, local sprite, student duotone / staff regular, sizes 20/24/32 | `ICON_SIZES`; `--icon-variant` per theme | `ui.py:44`, `tokens.css:103,110`; `test_icon_accepts_each_catalogue_size` |
| Ref: a11y AA, contrast text 4.5 / UI 3 | 19 computed pairs | `test_colour_pair_meets_wcag_aa` ×19 |
| Ref: a11y focus 3px outline | see AC1 | browser outline |
| Ref: loading state = button spinner + disable | `loading=True` → `disabled`, `aria-busy`, `.htmx-request` | `test_loading_button_shows_spinner_state_busy_and_disabled`; browser |
| Ref: §11.2 Button variants incl. `disabled` | `disabled` kwarg | `test_disabled_button_is_natively_disabled_without_busy_state` |
| Ref: §11.4 status never colour alone; buttons are `<button>`; min 16px body | pill word; real `<button>`; `font-size: var(--font-size-base, 16px)` | `test_status_pill_always_shows_a_word`, `test_button_renders_each_variant_as_a_real_button` |
| Ref: §13 no CDN; no `\|safe` | local static only | `request_hosts`; Gate 2 |
| Quality line | ruff 0; mypy; coverage ≥85; no raw hex, no `!important` outside reduced motion; no inline style/script; no external URL; no `\|safe`; no TODO | gates + Gate 2 |
| QA-observable | primary `rgb(14, 116, 144)` + white; student ≥44 / staff ≥32; same-origin; diacritics in font; 3px orange focus; no DB | browser JSON; `test_styleguide_makes_no_database_queries` |

AC count: the story has 10 ACs and all 10 appear above (AC1 is split across its bullets).

### Gate 2 — Negative-space checks (verbatim)

```
$ grep -rnE 'https?://' src/infrastructure/web/templates/components src/infrastructure/web/templates/styleguide src/infrastructure/web/static/css
[matches: 0]
$ grep -rnoE 'https?://[^"]+' src/infrastructure/web/static/icons/sprite.svg | sort -u
src/infrastructure/web/static/icons/sprite.svg:2:http://www.w3.org/2000/svg
[matches: 1]                                   (XML namespace identifier, never fetched)
$ grep -rnE '#[0-9a-fA-F]{3,8}\b' --include='*.css' src/infrastructure/web/static/css | grep -v 'tokens.css'
[matches: 0]
$ grep -rn '!important' src/infrastructure/web/static/css | grep -v 'tokens.css'
[matches: 0]
$ grep -n '!important' src/infrastructure/web/static/css/tokens.css
137:    animation: none !important;
138:    transition: none !important;
[matches: 2]                                   (only the reduced-motion block, as allowed)
$ grep -rnE 'style=|<style|<script' src/infrastructure/web/templates/components src/infrastructure/web/templates/styleguide
[matches: 0]
$ grep -rnE '\|\s*safe|mark_safe|format_html' src/infrastructure/web/templates src/infrastructure/web/templatetags src/infrastructure/web/styleguide
[matches: 0]
$ grep -rnE 'TODO|FIXME|print\(' src/infrastructure/web/templatetags src/infrastructure/web/styleguide tests/integration/web/ui
[matches: 0]
$ grep -rn 'styleguide' src/infrastructure/web/common/decorators.py          (not in PUBLIC_URL_NAMES)
[matches: 0]
$ grep -rnE 'objects\.|\.filter\(|connection' src/infrastructure/web/templatetags/ui.py src/infrastructure/web/styleguide   (no DB access)
[matches: 0]
$ grep -rnE 'form_field|alert|card|confirm_dialog|language_switcher|dark' src/infrastructure/web/templatetags/ui.py src/infrastructure/web/templates/components   (OUT: molecules, switcher, dark mode)
[matches: 0]
$ git diff --stat 179c213 -- docs/status.md docs/plans pyproject.toml uv.lock tests/conftest.py README.md .env.example src/config/settings docs/architecture
[matches: 0]                                   (no dependency, settings, status or plan edits)
$ git diff 179c213 -- src/infrastructure/web/static/css/tokens.css | grep '^-' | grep -v '^---'
[matches: 0]                                   (seeded tokens untouched)
```
Also out of scope and not done: no theme class on `<body>` (`layouts/base.html` unchanged), no Storybook or JS toolchain, no `.mo` compile. `test_styleguide_makes_no_database_queries` runs without the `db` fixture, so pytest-django raises on any query.

### Gate 3 — Contract consistency

| Producer | Consumer | Check |
|----------|----------|-------|
| `ICON_NAMES` (ui.py) | `sprite.svg` symbol ids | Set equality, regular plus `-duotone` (`test_sprite_has_regular_and_duotone_symbols_for_exactly_the_icon_names`); an unknown name raises, so there's never a blank `<use>` |
| `ui_icon(variant)` | sprite `{name}` / `{name}-duotone` | `test_duotone_icon_uses_duotone_symbol`; an unknown variant raises |
| `STATUS_LABELS` keys | `.pill--{status}` in `status_pill.css`, `--pill-{state}-*` tokens | 6 statuses ↔ 6 CSS rules ↔ 6 token pairs; each status asserted to render `pill--<lower>` + word |
| `BUTTON_VARIANTS` | `.button--{variant}` CSS | 4 ↔ 4 rules; unknown → `TemplateSyntaxError` |
| `ui_button(**hx)` | rendered `hx-*` attributes | `hx_a_b` → `hx-a-b`, values autoescaped; non-`hx_` and `hx_on*` → `TemplateSyntaxError` (never silently dropped) |
| `ui_button(type)` | `<button type>` | only submit/button/reset; anything else → `TemplateSyntaxError` |
| `ui_button(loading)` | `.button.htmx-request` CSS | `loading=True` renders the same class HTMX adds in flight, plus `disabled` and `aria-busy="true"` |
| `ui_progress(total=0)` | `<progress max>` | `max = total or 1`; text keeps "0/0" |
| Styleguide `SWATCHES` hex | `tokens.css` values | `test_swatch_hex_values_match_tokens_css` |
| `.po` msgids | `{% translate %}` / `_()` / `{% blocktranslate %}` sources | `test_every_new_ui_string_is_in_the_catalogue[ro/en]` |
| `config/urls.py` DEBUG branch | `reverse("styleguide:index")` | DEBUG=True → `/ro/_styleguide/`, `/en/_styleguide/` 200; DEBUG=False → `NoReverseMatch` + 404 |
| Theme `--touch` | `.button` min-height | outside any theme, `var(--touch, var(--touch-min))` still gives 32px (no silent `auto`) |

## Challenges Encountered

| Challenge | Resolution | Time Spent |
|-----------|------------|------------|
| The worktree was created at `main` (899c001), not at the wave base | Reset the clean worktree branch to `179c213` (`feature/wave-2-dev-1`) before starting | 5 min |
| No browser could be downloaded for Playwright | Used the installed system Chrome via `channel="chrome"`; nothing was downloaded | 10 min |
| GNU gettext missing (**known environment limitation**) | `.po` entries were added by hand and nothing was compiled; tests assert EN output and parse the `.po` text. RO strings show on screen only once Story 1.4 installs gettext and compiles | — |
| `/en/` 404 without `LocaleMiddleware` | Language activation is Story 1.4's job (Story 1.0 OUT list; `MIDDLEWARE` is shared). `test_styleguide.py` installs `LocaleMiddleware` after `SessionMiddleware` (the order fixed in Story 1.2) through an autouse fixture | 15 min |
| A document stylesheet can't style the inside of an external `<use>` reference | The duotone class rule lives in a `<style>` inside `sprite.svg`, and `var(--color-accent)` inherits through the `<use>` shadow tree. `icon.css` repeats the rule for inlined copies | 10 min |

## Deviations from Plan

1. **`ui_button` gained `disabled=False` and `loading=False`.** `disabled` is required by the patterns §11.2 catalogue ("`type`, `disabled`, optional `hx-*`"). `loading` renders the in-flight state (`htmx-request`, `aria-busy`, `disabled`) so the styleguide can show it statically. The `**hx` restriction is unchanged.
2. **`hx_on*` keys are rejected** in addition to non-`hx_` keys. `hx-on` runs inline JavaScript, which is the same vector as the `onclick` the story bans (§11.1/§13).
3. **The button `type` is validated** (submit/button/reset) so a bad value is never silently accepted (Gate 3).
4. **The progress meter uses implicit labelling** (`<label>` wraps the `<progress>`) instead of a `for`/`id` derived from `label|slugify`. Slug ids would duplicate whenever the same label appears twice on a page, as it does in the two styleguide theme sections. `aria-valuetext="N of M"` was added so screen readers announce "3 of 8" rather than a percentage.
5. **`role="img"` was added** to `score` (`<p aria-label>`) and `badge`, so their `aria-label` is actually announced.
6. **Extra files:** `static/css/components/icon.css`, as AC7 requires for every atom, and `static/css/styleguide.css` for the styleguide layout and swatch classes (inline styles are forbidden). Neither is in the story's Files Touched list.
7. **`config/urls.py` import line:** `include` was added to the existing `from django.urls import …` line, because ruff/isort forbids a second import from the same module. Story 1.2 most likely makes the identical edit, which git merges cleanly.
8. **The styleguide is a standalone document** and doesn't extend `layouts/base.html`. That avoids editing the shared base layout (Story 1.7) just to add a stylesheet block.
9. **The pill tokens and line-heights** from Step 2 were already seeded by Story 1.0 with identical values, so they were not redeclared.
10. **`body` background** is `var(--bg, var(--color-surface))` instead of `var(--bg, #FFFFFF)`. The value is the same, written token-only.

## Lessons Learned

1. Check the worktree base against the brief before doing anything. The harness created this worktree from `main`.
2. Styling external SVG sprites: document CSS doesn't reach the content behind `<use>`, but custom properties inherit into it. Put the class rule inside the sprite and drive it with tokens.
3. Language-prefixed routes need `LocaleMiddleware` to resolve any prefix other than the default one. A test fixture can stand in for an unmerged sibling story without touching shared settings.

## Next Steps

- [ ] After Story 1.4 merges (LocaleMiddleware + gettext): compile the catalogues and re-check `/en/_styleguide/` on a dev server, and RO pill words on `/ro/`.
- [ ] Watch for duplicate msgids when the other wave-2 `.po` blocks merge (`msgfmt` rejects duplicates).
- [ ] Ready for code review
- [ ] Ready for QA validation
