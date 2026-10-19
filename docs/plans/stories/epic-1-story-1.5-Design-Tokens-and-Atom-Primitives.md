### Story 1.5: Design Tokens & Atom Primitives

**BUILDID**: CYCLE-1 | **GitHub**: LOCAL | **AzureDevOps**: LOCAL | **Epic**: 1 - Foundation | **ID**: 1.5 | **Date**: 2026-10-19
**File**: `docs/plans/stories/epic-1-story-1.5-Design-Tokens-and-Atom-Primitives.md`
**Build Ref**: `docs/plans/builds/cycle-1/cycle-plan.md` — CYCLE-1 Foundation & Access (Workshop Day 3: tokens and primitives on `/_styleguide/`)
**Wave**: 2
**Requires**: [1.0]
**Enables**: [1.6]
**Files Touched**:
  - src/infrastructure/web/static/css/tokens.css
  - src/infrastructure/web/static/fonts/**
  - src/infrastructure/web/static/icons/**
  - src/infrastructure/web/static/css/components/button.css
  - src/infrastructure/web/static/css/components/badge.css
  - src/infrastructure/web/static/css/components/status_pill.css
  - src/infrastructure/web/static/css/components/avatar.css
  - src/infrastructure/web/static/css/components/score.css
  - src/infrastructure/web/static/css/components/progress_meter.css
  - src/infrastructure/web/templates/components/button.html
  - src/infrastructure/web/templates/components/icon.html
  - src/infrastructure/web/templates/components/badge.html
  - src/infrastructure/web/templates/components/status_pill.html
  - src/infrastructure/web/templates/components/avatar.html
  - src/infrastructure/web/templates/components/score.html
  - src/infrastructure/web/templates/components/progress_meter.html
  - src/infrastructure/web/templatetags/ui.py
  - src/infrastructure/web/styleguide/**
  - src/infrastructure/web/templates/styleguide/**
  - src/config/urls.py
  - src/infrastructure/i18n/locale/ro/LC_MESSAGES/django.po
  - src/infrastructure/i18n/locale/en/LC_MESSAGES/django.po
  - tests/integration/web/ui/test_atoms.py
  - tests/integration/web/ui/test_styleguide.py
**Roles Ref**: docs/requirements.md#roles--permissions-matrix — single-actor — no role variation (primitives look the same for every role; the student/staff *theme* is chosen by the layout in Story 1.7, not by role checks here)
**QA Candidate**: Yes — **Observable:** with `DEBUG=True`, `/ro/_styleguide/` and `/en/_styleguide/` show every atom (button variants and loading state, icon sizes and variants, badge, the six status pills, avatar, score, progress meter) in the student and staff themes. With `DEBUG=False` the styleguide doesn't exist (404). **Mechanism:** `tokens.css` turns the approved UI/UX spec into CSS custom properties, plus `@font-face` for the self-hosted Atkinson Hyperlegible Next and the theme classes `.theme-student`/`.theme-staff`. A local Phosphor SVG sprite. Inclusion tags `{% ui_button %}`, `{% ui_icon %}`, `{% ui_badge %}`, `{% ui_status_pill %}`, `{% ui_avatar %}`, `{% ui_score %}`, `{% ui_progress %}` in `templatetags/ui.py` render `components/*.html`. The styleguide URLs are registered only when `settings.DEBUG`. **Authz & preconditions:** none (pure presentation); the styleguide is reachable only in DEBUG and is never deployed. **Edge & idempotency:** unknown icon names, statuses, sizes or out-of-range scores raise `ValueError` at render, so a typo fails tests instead of shipping a blank; `ui_progress` with total 0 shows "0/0" without dividing by zero; `ui_button` accepts only `hx_*` passthrough keywords (anything else raises `TemplateSyntaxError`), and all values are autoescaped; rendering is deterministic. **Regression:** visual contrast (all pairs pre-verified at WCAG AA), status shown by text plus colour (never colour alone), focus outline on interactive atoms, Romanian diacritics in the chosen font, and that no CDN or external request is made (privacy).

---

#### 👤 User Reference

**Description**:
This story builds the platform's visual building blocks, called "atoms", and the design values everything else uses. Atoms are the smallest reusable pieces:
- buttons, with a "working…" state that also stops double clicks
- icons
- small count badges
- coloured status labels, for example "Active" or "Blocked", always with words and never colour alone
- the generic user avatar (no photo uploads, as required)
- a score display such as "87 / 100"
- a progress bar such as "6 of 8 exercises"

The design values are the approved colours, spacing, font sizes, rounded corners and shadows. There are two "themes":
- **Student:** warmer background, larger text, rounder shapes and bigger buttons for small hands and early readers.
- **Staff** (teachers, parents, administrators): calmer and more compact.

The font is chosen for easy reading and is stored on the platform's own server, as are the icons. Children's browsers never contact outside companies just to show a page.

For the team there's a private "styleguide" page, available only on developers' machines, showing every building block in both languages and both themes. It's the agreed visual reference: if something looks wrong there, it looks wrong everywhere.

**Acceptance Criteria** (plain-English):
- All colours, sizes and spacing match the approved UI/UX specification exactly.
- There are two themes, student and staff, using the same building blocks.
- Buttons come in primary, secondary, danger and link styles; while an action is in progress the button shows a small spinner and can't be clicked again.
- Status labels always show a word (in Romanian or English) as well as a colour.
- Scores display as "N / 100" and progress as "done / total" with a bar; screen readers announce both meaningfully.
- Icons come from one consistent set, stored locally; purely decorative icons are hidden from screen readers.
- The chosen font displays Romanian letters (ș ț ă â î and capitals) correctly; if it can't, the system font is used instead.
- The styleguide page shows every building block in Romanian and English, and doesn't exist on the live site.
- Nothing on these pages loads files from outside the platform.

**User Flow** (no role variation — presentation primitives are identical for all roles):

**User Journey** (developer/QA viewing the styleguide; end users meet these atoms inside feature pages):
- **Entry**: with `DEBUG=True`, open `/ro/_styleguide/` or `/en/_styleguide/`.
- **Load**: the page loads `tokens.css`, the component stylesheets and the font from `/static/`. No third-party request appears in the browser's network tab.
- **Render**: sections for Tokens (colour swatches with hex values and contrast notes, spacing, type scale with "ș ț ă â î Ș Ț Ă Â Î"), Buttons (4 variants × normal/disabled/loading, with and without icon), Icons (each icon at 20/24/32, regular and duotone), Badge, Status pills (all six states), Avatar, Score (1, 50, 100), Progress (0/0, 3/8, 8/8). Each section appears twice: once inside `.theme-student` and once inside `.theme-staff`.
- **Interact**: tabbing reaches every button with a visible 3px orange focus ring. The loading example shows the spinner, `aria-busy="true"` and `disabled`.
- **Empty/error**: in production (`DEBUG=False`) the URL returns 404. A template using an unknown icon or status fails loudly in tests.
- **Responsive**: desktop-only. The styleguide is a single 1200px column; swatches wrap in a 12-column grid.

**Flow Diagram** (display matrix — presentation-only story):

| Atom | Inputs | Renders | a11y contract | Invalid input |
|------|--------|---------|---------------|---------------|
| `ui_button` | label, variant (primary/secondary/danger/link), type, icon, `hx_*` | `<button class="button button--{variant}">` + optional icon + hidden spinner | real `<button>`; spinner `aria-hidden`; loading → `aria-busy` (set via HTMX class) | unknown variant or non-`hx_` kwarg → error |
| `ui_icon` | name, size 20/24/32, variant regular/duotone, label | `<svg><use href=sprite#name[-duotone]>` | decorative → `aria-hidden="true"`; with label → `role="img" aria-label` | unknown name/size → `ValueError` |
| `ui_badge` | value, label | `<span class="badge">` | visible number + `aria-label` with full meaning | value < 0 → `ValueError`; 0 → renders nothing |
| `ui_status_pill` | status | `<span class="pill pill--{status}">` + translated word | text always present | unknown status → `ValueError` |
| `ui_avatar` | user | generic `user-circle` icon in a circle | `role="img" aria-label=<full name>` | missing name → "User" |
| `ui_score` | value 1–100 | big number + "/ 100" | `aria-label="Score: N out of 100"` | outside 1–100 → `ValueError` |
| `ui_progress` | done, total, label | `<progress value max>` + "done/total" text | `<label>` tied to `<progress>` | done > total or negative → `ValueError`; total 0 → "0/0" |

---

#### 🤖 AI Agent Reference

**Must Read**:
- `docs/ui-ux/ui-ux-spec.md` — the approved tokens (source of truth for every value)
- `docs/ui-ux/08-visual-foundation.md` — full token detail (pill colours, elevation shadows, icon sizes, touch targets), component hierarchy
- `docs/architecture/design/01-patterns-and-standards-greenfield.md` — §11.2 UI Primitive Catalogue (locations, rules), §11.4 accessibility baseline, §13 (no CDN, no `|safe`)
- `docs/plans/stories/epic-1-story-1.0-Root-Tooling-Seed.md` — the seeded `tokens.css` and `ui.py`

**Description**:
Completes `tokens.css` with:
- `@font-face` for self-hosted Atkinson Hyperlegible Next (400/600/700 woff2, SIL OFL; licence file shipped alongside)
- base element styles: `body` font and colour, `:focus-visible` 3px `--color-focus` outline with 2px offset, `.visually-hidden`, `prefers-reduced-motion`
- the two theme classes setting the role-dependent tokens: `--font-size-base`, `--radius`, `--bg`, `--touch`, `--icon-variant`

Builds the local Phosphor icon sprite (`static/icons/sprite.svg`, MIT licence file alongside). Each needed icon is a `<symbol id="{name}">` (regular) and `<symbol id="{name}-duotone">`.

Delivers the 7 atom primitives as inclusion tags plus templates plus one CSS file each. Adds the DEBUG-only `/_styleguide/`, registered inside `i18n_patterns` only when `settings.DEBUG`.

Molecules (form field, alert, card…) are Story 1.6, which extends the same `ui.py` and styleguide.

**Design Tokens** (FE — authoritative values from the UI/UX spec):
- Colors: primary `#0E7490` · primary-hover `#155E75` · accent `#FBBF24` · focus `#C2410C` · success `#15803D` · error `#B91C1C` · warning `#B45309` · text `#1F2937` · muted `#4B5563` · border `#6B7280` · bg-student `#FFF8EC` · bg-staff `#F5F7FA` · surface `#FFFFFF` · disabled `#F3F4F6`
- Pills (bg/fg): ACTIVE `#DCFCE7`/`#14532D` · FLAGGED `#FEF3C7`/`#78350F` · BLOCKED `#FEE2E2`/`#7F1D1D` · RESUBMITTED `#CFFAFE`/`#164E63` · DRAFT `#F3F4F6`/`#1F2937` · PUBLISHED `#CFFAFE`/`#164E63`
- Spacing: 4px unit; student 8/16/24/32/48/64; staff 4/8/12/16/24/32/48
- Typography: Atkinson Hyperlegible Next → system-ui; base student 18px / staff 16px; scale 14/16/18/20/24/32/40; weights 400/600/700; line-height body 1.6, heading 1.25
- Radius: student 16px · staff 8px · pill 999px. Elevation 0–3 per `08-visual-foundation.md`.
- Touch: min 32px; student controls 44px. Icons: Phosphor, student duotone / staff regular, sizes 20/24/32.
- Buttons: primary bg `#0E7490` + white text (5.36:1), hover `#155E75`; secondary transparent + `#0E7490` text + 1px `#6B7280` border; danger bg `#B91C1C` + white (6.47:1); link `#0E7490` underlined; disabled bg `#F3F4F6` + text `#4B5563`.

**Acceptance Criteria**:
1. `tokens.css` keeps every custom property seeded by Story 1.0 (no renames) and adds:
   - pill pairs `--pill-{state}-bg`/`--pill-{state}-fg`
   - `--line-height-body: 1.6`, `--line-height-heading: 1.25`
   - `@font-face` for 400/600/700 (`font-display: swap`)
   - `.theme-student`/`.theme-staff` defining `--font-size-base`, `--radius`, `--bg`, `--touch`
   - `body { font-family: var(--font-family); font-size: var(--font-size-base); color: var(--color-text); background: var(--bg); line-height: var(--line-height-body); }`
   - `:focus-visible { outline: 3px solid var(--color-focus); outline-offset: 2px; }`
   - `.visually-hidden`
   - `@media (prefers-reduced-motion: reduce)` disabling animations
2. `static/fonts/` contains `AtkinsonHyperlegibleNext-{Regular,SemiBold,Bold}.woff2` and `OFL.txt`. Romanian glyphs ș ț ă â î Ș Ț Ă Â Î are verified to render (styleguide screenshot). If any is missing, `--font-family` falls back to `system-ui, sans-serif` and the review doc records it.
3. `static/icons/sprite.svg` contains regular and `-duotone` symbols for exactly the names in `ICON_NAMES` (single source in `ui.py`): `arrow-counter-clockwise`, `bell`, `book-open`, `caret-right`, `chalkboard-teacher`, `chart-bar`, `check-circle`, `compass`, `exam`, `flag`, `house`, `list-checks`, `lock-simple`, `pencil-simple`, `plugs`, `prohibit`, `shield-check`, `sign-in`, `sign-out`, `student`, `translate`, `user-circle`, `users`, `warning-circle`, `x-circle`. Phosphor's `LICENSE` (MIT) is next to it. Duotone symbols use `fill="currentColor"` plus an opacity-0.2 layer filled with `var(--color-accent)` via a CSS class.
4. Inclusion tags in `templatetags/ui.py`, each rendering `components/<name>.html`:
   - `ui_button(label, variant="primary", type="submit", icon=None, name=None, value=None, **hx)`: `hx` keys must start with `hx_` and render as `hx-…`; anything else raises `TemplateSyntaxError`. Output includes `<span class="button__spinner" aria-hidden="true">`.
   - `ui_icon(name, size=24, variant="regular", label="")`
   - `ui_badge(value, label)`
   - `ui_status_pill(status)`: statuses ACTIVE, FLAGGED, BLOCKED, RESUBMITTED, DRAFT, PUBLISHED, with translated labels (RO: Activ, Semnalat, Blocat, Retrimis, Ciornă, Publicat)
   - `ui_avatar(user)`
   - `ui_score(value)`
   - `ui_progress(done, total, label)`
5. Invalid input raises as specified in the display matrix (unit-tested).
6. Button loading state: `.button.htmx-request` shows the spinner and sets `pointer-events: none`. Callers add `hx-disabled-elt="this"` (passed via `hx_disabled_elt="this"`) so HTMX disables the button during the request. Under `prefers-reduced-motion` the spinner is a static ring.
7. Each atom's CSS lives in `static/css/components/<name>.css`, uses only `var(--…)` tokens (no raw hex outside `tokens.css`), and has no `!important`.
8. `/_styleguide/` (`styleguide:index`) is added to `i18n_patterns` only `if settings.DEBUG`. It renders every atom and variant in `.theme-student` and `.theme-staff` sections, and in RO/EN through the URL prefix. With `DEBUG=False`, `reverse("styleguide:index")` raises `NoReverseMatch` and `/ro/_styleguide/` returns 404.
9. No template or CSS references an external URL (`http://` or `https://`). A test greps `templates/components`, `templates/styleguide` and `static/css`.
10. All new UI strings exist in both catalogues with RO translations.

**RBAC Enforcement**:
No role-differentiated access — single actor.
- The styleguide is a development tool registered only when `DEBUG=True`. It's never present in production URL routing, so it isn't in `PUBLIC_URL_NAMES`. The URL-coverage test (Story 1.3) runs with `DEBUG=False`, where the route doesn't exist.

**System responses + error cases**:

| Trigger | Response | Side-effect |
|---------|----------|-------------|
| `GET /ro/_styleguide/` with `DEBUG=True` | `200` styleguide in Romanian | none |
| `GET /en/_styleguide/` with `DEBUG=True` | `200` in English | none |
| Same request repeated | identical `200` HTML (deterministic) | none |
| `GET /ro/_styleguide/` with `DEBUG=False` | `404` (Story 1.1 page) | none |
| Template renders `{% ui_icon "unknown" %}` | `ValueError("Unknown icon: unknown")` → test failure / 500 | error log with request id |
| `{% ui_status_pill "ARCHIVED" %}` | `ValueError` | — |
| `{% ui_score 0 %}` or `{% ui_score 101 %}` | `ValueError` | — |
| `{% ui_progress 0 0 "…" %}` | renders "0/0", `<progress value="0" max="1">` | none |
| `{% ui_progress 9 8 "…" %}` | `ValueError` | — |
| `{% ui_button "Save" onclick="x" %}` | `TemplateSyntaxError` (only `hx_*` passthrough allowed) | — |
| `{% ui_button "Send" hx_post="/x" hx_disabled_elt="this" %}` | `<button … hx-post="/x" hx-disabled-elt="this">` (values autoescaped) | none |
| `{% ui_badge 0 "…" %}` | renders nothing | none |

**QA-observable behaviour**:
- Computed styles on the styleguide match the tokens, e.g. a primary button has background `rgb(14, 116, 144)` and white text, and a student-theme button is ≥44px high while a staff one is ≥32px.
- Every pill shows its word; with CSS disabled, the words are still present.
- The browser network panel shows only same-origin requests (fonts, sprite, CSS).
- The type-scale sample line renders "ș ț ă â î Ș Ț Ă Â Î" in Atkinson Hyperlegible Next (no fallback-font glyphs).
- Keyboard focus on any button shows a 3px orange outline.
- **What does NOT change**: no database access by any atom or by the styleguide; no new public route in production; existing seeded token names keep their values.

**Prerequisites**:
- Story 1.0 merged (seeded `tokens.css`, `ui.py`, `base.html`).
- Download Atkinson Hyperlegible Next woff2 files (Braille Institute, SIL OFL 1.1) and the needed Phosphor SVGs (MIT) **once**, by hand, into `static/`. They're committed assets, never loaded from a CDN at runtime.
- GNU gettext for compiling RO strings (see Story 1.4). Tests assert EN strings or structure.

**Context**: `docs/ui-ux/ui-ux-spec.md`, `docs/ui-ux/08-visual-foundation.md`, `docs/architecture/design/01-patterns-and-standards-greenfield.md`, `src/infrastructure/web/static/css/tokens.css`, `src/infrastructure/web/templatetags/ui.py`

**Patterns**: UI Primitive Catalogue (§11.2), Templates (§11.1), Accessibility baseline (§11.4), Security — no CDN / no `|safe` (§13), Testing (§12) — see `docs/architecture/design/01-patterns-and-standards-greenfield.md`

**Steps**:

1. **Tests first:** `tests/integration/web/ui/test_atoms.py` (render each tag through `Template(...)`, including the invalid inputs) and `test_styleguide.py`.

2. **Tokens and themes** (append to `tokens.css`; seeded variables stay unchanged):
   ```css
   @font-face { font-family: 'Atkinson Hyperlegible Next'; font-weight: 400; font-display: swap;
                src: url('../fonts/AtkinsonHyperlegibleNext-Regular.woff2') format('woff2'); }
   @font-face { font-family: 'Atkinson Hyperlegible Next'; font-weight: 600; font-display: swap;
                src: url('../fonts/AtkinsonHyperlegibleNext-SemiBold.woff2') format('woff2'); }
   @font-face { font-family: 'Atkinson Hyperlegible Next'; font-weight: 700; font-display: swap;
                src: url('../fonts/AtkinsonHyperlegibleNext-Bold.woff2') format('woff2'); }

   :root {
     --pill-active-bg: #DCFCE7; --pill-active-fg: #14532D;
     --pill-flagged-bg: #FEF3C7; --pill-flagged-fg: #78350F;
     --pill-blocked-bg: #FEE2E2; --pill-blocked-fg: #7F1D1D;
     --pill-resubmitted-bg: #CFFAFE; --pill-resubmitted-fg: #164E63;
     --pill-draft-bg: #F3F4F6; --pill-draft-fg: #1F2937;
     --pill-published-bg: #CFFAFE; --pill-published-fg: #164E63;
     --line-height-body: 1.6; --line-height-heading: 1.25;
   }
   .theme-student { --font-size-base: var(--font-size-base-student); --radius: var(--radius-student);
                    --bg: var(--color-bg-student); --touch: var(--touch-student); }
   .theme-staff   { --font-size-base: var(--font-size-base-staff); --radius: var(--radius-staff);
                    --bg: var(--color-bg-staff); --touch: var(--touch-min); }
   body { margin: 0; font-family: var(--font-family); font-size: var(--font-size-base, 16px);
          line-height: var(--line-height-body); color: var(--color-text); background: var(--bg, #FFFFFF); }
   h1, h2, h3 { line-height: var(--line-height-heading); }
   :focus-visible { outline: 3px solid var(--color-focus); outline-offset: 2px; }
   .visually-hidden { position: absolute; width: 1px; height: 1px; overflow: hidden;
                      clip: rect(0 0 0 0); clip-path: inset(50%); white-space: nowrap; }
   @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important;
                                                                     transition: none !important; } }
   ```
   > `!important` is allowed **only** in this reduced-motion block (an accessibility override). AC 7 forbids it in component CSS.

3. **Icon sprite:** build `static/icons/sprite.svg` from the downloaded Phosphor SVGs, one `<symbol viewBox="0 0 256 256" id="…">` per regular and duotone variant, for exactly `ICON_NAMES`. Keep `LICENSE` next to it. The sprite starts with a comment listing the Phosphor version and the icon names.

4. **Inclusion tags** (`templatetags/ui.py`):
   ```python
   from django import template
   from django.utils.translation import gettext_lazy as _

   register = template.Library()

   ICON_NAMES = frozenset({
       "arrow-counter-clockwise", "bell", "book-open", "caret-right", "chalkboard-teacher", "chart-bar",
       "check-circle", "compass", "exam", "flag", "house", "list-checks", "lock-simple", "pencil-simple",
       "plugs", "prohibit", "shield-check", "sign-in", "sign-out", "student", "translate", "user-circle",
       "users", "warning-circle", "x-circle",
   })
   ICON_SIZES = frozenset({20, 24, 32})
   BUTTON_VARIANTS = frozenset({"primary", "secondary", "danger", "link"})
   STATUS_LABELS = {
       "ACTIVE": _("Active"), "FLAGGED": _("Flagged"), "BLOCKED": _("Blocked"),
       "RESUBMITTED": _("Resubmitted"), "DRAFT": _("Draft"), "PUBLISHED": _("Published"),
   }


   @register.inclusion_tag("components/icon.html")
   def ui_icon(name: str, size: int = 24, variant: str = "regular", label: str = "") -> dict:
       if name not in ICON_NAMES or int(size) not in ICON_SIZES or variant not in {"regular", "duotone"}:
           raise ValueError(f"Unknown icon: {name} (size={size}, variant={variant})")
       symbol = name if variant == "regular" else f"{name}-duotone"
       return {"symbol": symbol, "size": int(size), "label": label}


   @register.inclusion_tag("components/button.html")
   def ui_button(label: str, variant: str = "primary", type: str = "submit", icon: str | None = None,
                 name: str | None = None, value: str | None = None, **hx: str) -> dict:
       if variant not in BUTTON_VARIANTS:
           raise template.TemplateSyntaxError(f"Unknown button variant: {variant}")
       if bad := [key for key in hx if not key.startswith("hx_")]:
           raise template.TemplateSyntaxError(f"ui_button accepts only hx_* attributes, got {bad}")
       attrs = [(key.replace("_", "-"), val) for key, val in sorted(hx.items())]
       return {"label": label, "variant": variant, "type": type, "icon": icon,
               "name": name, "value": value, "attrs": attrs}


   @register.inclusion_tag("components/status_pill.html")
   def ui_status_pill(status: str) -> dict:
       if status not in STATUS_LABELS:
           raise ValueError(f"Unknown status: {status}")
       return {"status": status.lower(), "label": STATUS_LABELS[status]}


   @register.inclusion_tag("components/score.html")
   def ui_score(value: int) -> dict:
       if not 1 <= int(value) <= 100:
           raise ValueError(f"Score must be 1–100, got {value}")
       return {"value": int(value)}


   @register.inclusion_tag("components/progress_meter.html")
   def ui_progress(done: int, total: int, label: str) -> dict:
       if done < 0 or total < 0 or done > total:
           raise ValueError(f"Invalid progress {done}/{total}")
       return {"done": done, "total": total, "max": total or 1, "label": label}
   ```
   `ui_badge` and `ui_avatar` follow the same shape. The avatar label is `user.get_full_name() or _("User")`.

5. **Component templates** (no inline `style`; all attribute values autoescaped):
   ```django
   {# components/button.html #}
   {% load ui %}
   <button type="{{ type }}" class="button button--{{ variant }}"
           {% if name %}name="{{ name }}"{% endif %} {% if value %}value="{{ value }}"{% endif %}
           {% for attr, val in attrs %}{{ attr }}="{{ val }}" {% endfor %}>
     {% if icon %}{% ui_icon icon 20 %}{% endif %}
     <span class="button__label">{{ label }}</span>
     <span class="button__spinner" aria-hidden="true"></span>
   </button>
   ```
   ```django
   {# components/icon.html #}
   {% load static %}
   <svg class="icon icon--{{ size }}" width="{{ size }}" height="{{ size }}" focusable="false"
        {% if label %}role="img" aria-label="{{ label }}"{% else %}aria-hidden="true"{% endif %}>
     <use href="{% static 'icons/sprite.svg' %}#{{ symbol }}"></use>
   </svg>
   ```
   ```django
   {# components/score.html #}
   {% load i18n %}
   <p class="score" aria-label="{% blocktranslate %}Score: {{ value }} out of 100{% endblocktranslate %}">
     <span class="score__value" aria-hidden="true">{{ value }}</span><span class="score__max" aria-hidden="true"> / 100</span>
   </p>
   ```
   ```django
   {# components/progress_meter.html #}
   <div class="progress">
     <label class="progress__label" for="progress-{{ label|slugify }}">{{ label }}</label>
     <progress id="progress-{{ label|slugify }}" value="{{ done }}" max="{{ max }}">{{ done }}/{{ total }}</progress>
     <span class="progress__text">{{ done }}/{{ total }}</span>
   </div>
   ```

6. **Component CSS** (one file per atom; tokens only). Excerpt:
   ```css
   /* static/css/components/button.css */
   .button { display: inline-flex; align-items: center; gap: var(--space-2); min-height: var(--touch);
             padding: var(--space-2) var(--space-4); border-radius: var(--radius); border: 1px solid transparent;
             font: inherit; font-weight: var(--weight-semibold); cursor: pointer; }
   .button--primary { background: var(--color-primary); color: var(--color-surface); }
   .button--primary:hover { background: var(--color-primary-hover); }
   .button--secondary { background: transparent; color: var(--color-primary); border-color: var(--color-border); }
   .button--danger { background: var(--color-error); color: var(--color-surface); }
   .button--link { background: none; color: var(--color-primary); text-decoration: underline; padding-inline: 0; }
   .button:disabled { background: var(--color-disabled); color: var(--color-muted); cursor: not-allowed; }
   .button__spinner { display: none; width: 1em; height: 1em; border: 2px solid currentColor;
                      border-right-color: transparent; border-radius: 50%; animation: spin .8s linear infinite; }
   .button.htmx-request { pointer-events: none; }
   .button.htmx-request .button__spinner { display: inline-block; }
   @keyframes spin { to { transform: rotate(360deg); } }
   ```

7. **Styleguide** (`web/styleguide/views.py`, `urls.py` with `app_name = "styleguide"`; `templates/styleguide/index.html` and `_atoms.html`):
   ```python
   # src/infrastructure/web/styleguide/views.py
   from django.shortcuts import render


   def index(request):
       """GET /<lang>/_styleguide/ — DEBUG-only visual reference for shared primitives."""
       return render(request, "styleguide/index.html", {"themes": ["student", "staff"]})
   ```
   ```python
   # src/config/urls.py (append inside the module, after urlpatterns are built)
   from django.conf import settings

   if settings.DEBUG:
       urlpatterns += i18n_patterns(
           path("_styleguide/", include("infrastructure.web.styleguide.urls")),
           prefix_default_language=True,
       )
   ```
   `index.html` loops over `themes`, wrapping `{% include "styleguide/_atoms.html" %}` in `<section class="theme-{{ theme }}">`. Story 1.6 adds `_molecules.html` to the same loop. Include the type-scale sample "ș ț ă â î Ș Ț Ă Â Î — Matematică și explorarea mediului".

8. **Translations:** RO for the pill labels, "Score: %(value)s out of 100" ("Punctaj: … din 100"), "User" ("Utilizator") and the styleguide headings.

9. **Run all gates.** Open the styleguide in a browser for the screenshots (Evidence).

**Tests**:

```python
# tests/integration/web/ui/test_atoms.py
import pytest
from django.template import Context, Template, TemplateSyntaxError
from django.utils import translation


def render(source: str, **context) -> str:
    with translation.override("en"):
        return Template("{% load ui %}" + source).render(Context(context))


def test_primary_button_has_spinner_and_label():
    html = render('{% ui_button "Save" %}')

    assert 'class="button button--primary"' in html
    assert 'class="button__spinner" aria-hidden="true"' in html
    assert ">Save<" in html


def test_button_passes_through_only_hx_attributes_escaped():
    html = render('{% ui_button "Send" hx_post=url hx_disabled_elt="this" %}', url='/x?a="b"')

    assert 'hx-post="/x?a=&quot;b&quot;"' in html
    assert 'hx-disabled-elt="this"' in html


def test_button_rejects_non_hx_attributes():
    with pytest.raises(TemplateSyntaxError):
        render('{% ui_button "Save" onclick="alert(1)" %}')


@pytest.mark.parametrize(("label", "expected"), [("", 'aria-hidden="true"'), ("Home", 'aria-label="Home"')])
def test_icon_accessibility(label, expected):
    assert expected in render('{% ui_icon "house" 24 "regular" label %}', label=label)


def test_duotone_icon_uses_duotone_symbol():
    assert "#book-open-duotone" in render('{% ui_icon "book-open" 32 "duotone" %}')


@pytest.mark.parametrize("args", ['"nope"', '"house" 18', '"house" 24 "filled"'])
def test_icon_rejects_unknown_inputs(args):
    with pytest.raises(ValueError):
        render("{% ui_icon " + args + " %}")


@pytest.mark.parametrize(("status", "word"), [
    ("ACTIVE", "Active"), ("FLAGGED", "Flagged"), ("BLOCKED", "Blocked"),
    ("RESUBMITTED", "Resubmitted"), ("DRAFT", "Draft"), ("PUBLISHED", "Published"),
])
def test_status_pill_always_shows_a_word(status, word):
    html = render("{% ui_status_pill s %}", s=status)

    assert f"pill--{status.lower()}" in html
    assert word in html


def test_status_pill_rejects_unknown_status():
    with pytest.raises(ValueError):
        render('{% ui_status_pill "ARCHIVED" %}')


@pytest.mark.parametrize("value", [1, 50, 100])
def test_score_announces_out_of_100(value):
    assert f'aria-label="Score: {value} out of 100"' in render("{% ui_score v %}", v=value)


@pytest.mark.parametrize("value", [0, 101, -5])
def test_score_outside_range_is_rejected(value):
    with pytest.raises(ValueError):
        render("{% ui_score v %}", v=value)


def test_progress_with_zero_total_shows_zero_of_zero():
    html = render('{% ui_progress 0 0 "Exercises" %}')

    assert 'value="0" max="1"' in html
    assert "0/0" in html


def test_progress_rejects_done_greater_than_total():
    with pytest.raises(ValueError):
        render('{% ui_progress 9 8 "Exercises" %}')


def test_zero_badge_renders_nothing():
    assert render('{% ui_badge 0 "unread" %}').strip() == ""


def test_no_component_or_css_references_external_urls():
    from pathlib import Path

    roots = ["src/infrastructure/web/templates/components", "src/infrastructure/web/templates/styleguide",
             "src/infrastructure/web/static/css"]
    offenders = [str(p) for root in roots for p in Path(root).rglob("*.*")
                 if "http://" in p.read_text(encoding="utf-8") or "https://" in p.read_text(encoding="utf-8")]

    assert offenders == []
```

```python
# tests/integration/web/ui/test_styleguide.py
import pytest
from django.urls import NoReverseMatch, include, path, reverse
from django.conf.urls.i18n import i18n_patterns

urlpatterns = i18n_patterns(path("_styleguide/", include("infrastructure.web.styleguide.urls")))


@pytest.mark.urls(__name__)
@pytest.mark.parametrize("lang", ["ro", "en"])
def test_styleguide_renders_all_atoms_in_both_themes(client, lang):
    html = client.get(f"/{lang}/_styleguide/").content.decode()

    assert html.count('class="theme-student"') == 1 and html.count('class="theme-staff"') == 1
    for marker in ("button--primary", "button--danger", "pill--blocked", "score__value", "<progress",
                   "ș ț ă â î"):
        assert marker in html


def test_styleguide_is_not_routed_when_debug_is_false():
    with pytest.raises(NoReverseMatch):
        reverse("styleguide:index")
```

Manual:
- With `DEBUG=True`, open `/ro/_styleguide/` and `/en/_styleguide/`. Compare swatches with `docs/ui-ux/ui-ux-spec.md`. Check the Romanian diacritics render in Atkinson Hyperlegible Next (dev tools → Fonts panel shows no fallback). Tab through the buttons and confirm the focus ring.
- In the network panel, confirm only same-origin requests.
- Enable the OS "reduce motion" setting and confirm the loading spinner no longer spins.

**Quality**: ruff 0; mypy passes; tests pass; coverage ≥85%; no raw hex outside `tokens.css`; no `!important` outside the reduced-motion block; no inline `style`/`script`; no external URLs; no `|safe`; no `TODO`.

**OUT**:
- ❌ Molecules: form field, alert, card, disabled tile, empty state, page header, confirm dialog, data table (Story 1.6).
- ❌ Applying the theme class to `<body>` per role, the top bar and the layout (Story 1.7).
- ❌ Language switcher component (Story 1.4).
- ❌ Storybook or any JS toolchain (patterns §11.2: styleguide page instead).
- ❌ Dark mode (not in the UI/UX spec).

**Evidence**: pytest output (atoms + styleguide), coverage %, screenshots of `/ro/_styleguide/` in both themes (including the diacritics line and the focused button), and a network-panel screenshot showing same-origin requests only, all recorded in `docs/stories-implemented/story-1.5-review.md` under "## DoD Evidence".
