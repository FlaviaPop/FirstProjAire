# Story 1.7 Self-Review

**Date**: 2026-10-23
**Story**: App Shell & Role Homes (Wave 4, Dev 1, one-by-one)
**Developer**: DEV Agent
**Status**: ✅ All 11 AC proven, the 3 binding hand-offs done, all gates green

---

## What Was Implemented

- **Full shared layout** (`layouts/base.html`):
  - `<html lang>` follows the active language.
  - A CSP-safe `htmx-config` meta (no indicator styles, no eval, no script tags).
  - `tokens.css`, **every** component stylesheet and `layout.css`.
  - Vendored `htmx.min.js` (deferred) and `ui.js` (module).
  - Theme class by role on `<body>`, with the CSRF token sent to HTMX through `hx-headers`.
  - The skip link first, and `<main id="content" tabindex="-1">`.
  - No inline script or style anywhere.
- **Top bar** (`_top_bar.html`):
  - The brand links to the home page (signed in) or the sign-in page.
  - For signed-in users, the role menu (`_nav.html`, `aria-current="page"`), plus an account menu: `<details>` with the avatar, name, translated role and a POST "Sign out" form.
  - The language switcher, with the two-tone icon in the student theme.
  - Signed-out visitors see only the brand and the switcher.
- **Flash messages** (`_messages.html`) render as `ui_alert`, with the level mapping debug/info→info, success, warning, error. They're consumed when shown.
- **Navigation registry** (`web/home/navigation.py`):
  - `NAV_BY_ROLE` exactly as AC 4 specifies.
  - `available_sections(user)` filters by permission and by whether the URL resolves; it never raises.
- **Tags** (`templatetags/navigation.py`): `role_nav` and `role_home_cards` are fed by the same registry. `shell_user`, `shell_messages` and `alert_level` make the layout safe when the database is down.
- **Home** (`home:index` at `/<lang>/`, `@require_authenticated`):
  - One template per role: a greeting by first name and an intro line.
  - A card per available section (`ui_card`), or `ui_empty_state`.
- **`layout.css`** (tokens only): the top bar, menu, account menu, skip link, theme widths and padding, and the card grid (3 columns for students, 4 for staff).
- **Translations:** 30 new RO/EN entries, each written by hand. `makemessages` fuzzy guesses were replaced, and no fuzzy entries remain.

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `src/infrastructure/web/templates/layouts/base.html` | Modified | Full layout (AC 1) |
| `src/infrastructure/web/templates/layouts/_top_bar.html` | New | Brand, role menu, switcher, account menu (AC 3/3a) |
| `src/infrastructure/web/templates/layouts/_nav.html` | New | `<nav aria-label="Main">` list with `aria-current` |
| `src/infrastructure/web/templates/layouts/_messages.html` | New | Flash messages via `ui_alert` (AC 2) |
| `src/infrastructure/web/templates/home/{student,teacher,parent,admin}.html` | New | Role homes (AC 6/7) |
| `src/infrastructure/web/templates/home/_cards.html` | New | Cards grid or empty state |
| `src/infrastructure/web/home/{__init__,navigation,views,urls}.py` | New | Registry, view, routes (AC 4–6) |
| `src/infrastructure/web/templatetags/navigation.py` | New | `role_nav`, `role_home_cards`, db-safe shell helpers |
| `src/infrastructure/web/static/css/layout.css` | New | Shell styles (tokens only) |
| `src/infrastructure/web/static/js/htmx.min.js` | New | htmx 2.0.11, vendored (AC 10) |
| `src/config/urls.py` | Modified | `home.urls` inside `i18n_patterns` after accounts |
| `src/infrastructure/i18n/locale/{ro,en}/LC_MESSAGES/django.po` | Modified | 30 new entries (AC 11) |
| `tests/integration/web/home/test_home.py` | New | 26 tests: homes, layout, messages, top bar, view |
| `tests/integration/web/home/test_navigation.py` | New | 24 tests: registry, filtering, link permissions, menu equals cards |
| `tests/integration/web/home/test_shell_without_database.py` | New | 3 tests (1.1 ISS-003 hand-off) |
| `tests/integration/web/home/test_root_redirect.py` | New | 4 tests (1.4 AC 2 hand-off) |
| `tests/integration/web/test_role_access_matrix.py` | Modified | 5 home rows (AC 8) |
| `tests/integration/web/common/test_error_middleware.py`, `test_request_id_logging.py`, `tests/integration/web/admin/test_parent_link_admin.py` | Modified | Their test URLconfs append the project routes the layout links to |
| `tests/integration/web/common/test_error_middleware.py` | Modified | Owner decision: error pages may set `csrftoken` (never a session); determinism ignores the token; inline-script check only |
| `tests/integration/web/ui/test_base_layout_styles.py` | Modified | Full stylesheet set; only external scripts |
| `docs/plans/stories/epic-1-story-1.1-Error-Handling-and-Observability.md` | Modified | Note recording the cookie decision |

`web/common/decorators.py` (listed in the story's Files Touched) needed no change: `home:index` uses the existing `@require_authenticated`.

## Patterns Applied

| Pattern | Where Applied | Notes |
|---------|---------------|-------|
| Thin views §7.1, authorization §7.2 | `home/views.py` | `@require_authenticated`; role and name from the session only |
| HTMX §7.4 | `base.html` | Vendored htmx, CSRF via `hx-headers`, `allowEval/allowScriptTags/includeIndicatorStyles` false |
| Primitives §11.2 | homes, messages, top bar | `ui_card`, `ui_empty_state`, `ui_alert`, `ui_avatar`, `ui_button`, `ui_icon`, language switcher; no duplicated markup |
| Accessibility §11.4 | layout | Skip link first, `<main tabindex=-1>`, `aria-current`, labelled nav and account menu, POST sign-out |
| Error resilience (1.1 ISS-003) | `templatetags/navigation.py` | `DatabaseError` → anonymous shell, empty messages |

## Testing Summary

- **New tests**: 59 (57 story tests + 2 for defensive tag paths), plus 5 matrix rows
- **Full suite**: 1344/1344 passing (3 consecutive runs)
- **Coverage**: 100% total; `web/home/*` and `templatetags/navigation.py` at 100%; domain/application 18/18 modules at 100%

**Test Output** (verbatim tails):
```
src/infrastructure/web/home/navigation.py                    31      0      6      0   100%
src/infrastructure/web/home/views.py                         11      0      0      0   100%
src/infrastructure/web/templatetags/navigation.py            40      0      4      0   100%
TOTAL                                                      1298      0    192      0   100%
1344 passed in 11.41s
```

## DoD Evidence

### Red phase (tests first)
```
34 failed, 10 passed            (home, redirect, shell-without-DB, matrix; before any implementation)
ERROR tests/integration/web/home/test_navigation.py   (module infrastructure.web.home.navigation missing)
```

### Gates (each read from its own output line)
```
[ruff format]  165 files already formatted
[ruff check]   All checks passed!
[mypy]         Success: no issues found in 110 source files          (--no-incremental)
[lint-imports] Contracts: 2 kept, 0 broken.
[migrations]   No changes detected
[makemessages] catalogue changes beyond line refs/date: 0 lines; fuzzy RO 0 EN 0
msgfmt --check OK (ro, en)
```

### htmx vendoring (AC 10)
```
npm registry: latest 2.0.x = 2.0.11 (published 2026-09-22)
tarball integrity: sha512-Thx/WtpeOQqSrqBCw/A1cwG… == registry dist.integrity
body sha256 after header == upstream dist/htmx.min.js sha256 d6fdc75f204e6bdefa99b69bf1e6d4ac69b8a364f77929f45c13476b4000f717
external URLs in the file: 0
```

### Real server (fresh DB, four role accounts)
```
ana   GET /ro/ -> 200 | theme-student | h1: Bună, Ana!   | nav ['/ro/']               | cards []            | empty-state True  | inline js 0 | style= 0 | switcher icon translate-duotone
ion   GET /ro/ -> 200 | theme-staff   | h1: Bună, Ion!   | nav ['/ro/']               | cards []            | empty-state True  | inline js 0 | style= 0 | switcher icon translate
maria GET /ro/ -> 200 | theme-staff   | h1: Bună, Maria! | nav ['/ro/']               | cards []            | empty-state True  | inline js 0 | style= 0 | switcher icon translate
boss  GET /ro/ -> 200 | theme-staff   | h1: Bună, Dana!  | nav ['/ro/', '/ro/admin/'] | cards ['/ro/admin/'] | empty-state False | inline js 0 | style= 0 | switcher icon translate
GET / [no header] -> 302 /ro/ · GET / [Accept-Language: en-GB] -> 302 /en/ · GET / [cookie en] -> 302 /en/
GET /static/js/htmx.min.js -> 200 52423B · /static/js/ui.js -> 200 · /static/css/layout.css -> 200
Content-Security-Policy: … script-src 'self'; … default-src 'self'; …   (unchanged)
sign out POST -> 302 /ro/accounts/login/ · after sign out GET /ro/ -> 302 /ro/accounts/login/?next=/ro/
DEBUG off: student GET /ro/does-not-exist/ -> 404 | error-card True | top bar True | switcher True | account menu True | theme-student
ERROR lines: 0 (both servers)
```
The student's "Learn" entry and the other future sections are correctly absent: their routes (`catalogue:index`, `progress:*`, `content:*`, `moderation:*`, `reporting:*`) don't exist yet.

### Gate 1: Spec Echo

| # | Requirement | Proof |
|---|-------------|-------|
| AC 1 | `base.html`: lang, htmx-config, tokens + every component CSS + layout.css, htmx deferred + ui.js module, theme + `hx-headers` body, skip link first, `<main id=content tabindex=-1>`, no inline script/style | `base.html:2,8,9-26,28-29,31,32,35`; `test_base_links_tokens_every_component_stylesheet_and_layout`, `test_base_loads_vendored_htmx_deferred_and_ui_js_as_module`, `test_body_sends_the_csrf_token_with_htmx_requests`, `test_main_is_the_skip_target_and_lang_matches_the_prefix`, `test_layout_has_skip_link_first_and_no_inline_scripts` |
| AC 2 | Messages under the top bar via `ui_alert`, level mapping, consumed | `_messages.html:2`, `navigation.py` (tags) `ALERT_LEVEL`/`alert_level`; `test_flash_message_rendered_once`, `test_message_levels_map_to_alert_levels` |
| AC 3 | Brand link, `<nav aria-label="Main">` + `aria-current`, switcher, `<details class="user-menu">` with `aria-label="Account menu"`, name, role label, POST logout + CSRF | `_top_bar.html:3,7,9,11-16`, `_nav.html`; `test_signed_in_top_bar_has_brand_menu_switcher_and_account_menu`, `test_only_the_current_link_is_marked`, `test_sign_out_posts_and_ends_the_session` |
| AC 3a | Anonymous: brand + switcher only | `_top_bar.html:3,7,10`; `test_anonymous_top_bar_shows_only_brand_and_switcher` |
| AC 4 | `NAV_BY_ROLE` exact and in order | `home/navigation.py:35-96`; `test_registry_entries_per_role_match_the_story`, `test_every_registry_entry_is_permitted_for_its_role` |
| AC 5 | `available_sections`: permission and resolvability filter, invalid role → `()`, never raises | `home/navigation.py:99-115`; `test_available_sections_*` (5), `test_anonymous_user_has_no_sections` |
| AC 6 | `home:index` `/<lang>/`, `@require_authenticated`, `home/<role>.html`, `greeting_name`, `sections`; 200 ×4, anonymous 302, corrupt role 403 | `home/views.py:9-27`, `config/urls.py:18`; `test_each_role_gets_its_home_and_theme`, `test_anonymous_is_redirected_to_login`, `test_corrupt_role_gets_403`, `test_greeting_uses_first_name` |
| AC 7 | One `<h1>`, `ui_card` per section, `ui_empty_state` when empty | `home/*.html`, `home/_cards.html:2,4`; `test_role_without_sections_sees_empty_state`, `test_admin_home_shows_the_accounts_card`, `test_menu_and_cards_list_the_same_sections` |
| AC 8 | Matrix rows for `/ro/` | `test_role_access_matrix.py:37-40` (5 rows, passing) |
| AC 9 | Every rendered link permitted for the role | `test_every_rendered_link_is_permitted_for_the_role` (×4), `test_student_never_sees_staff_links` |
| AC 10 | htmx 2.0.x vendored with its version comment, no CDN | `static/js/htmx.min.js:1`; integrity/sha256 evidence above; `test_base_loads_vendored_htmx…` (no `https://` in head) |
| AC 11 | RO/EN for every new string | 30 entries filled; `test_translations_complete`; makemessages re-run: 0 changes, 0 fuzzy |
| Step 1 | Tests first | Red phase above |
| Steps 2–6 | Registry, tags, view/URLs, templates, layout CSS | Files above |
| Step 7 | Matrix rows | AC 8 |
| Step 8 | Translations + gates; CSP check | Gates above; CSP header unchanged and 0 inline script/style on every home. Browser console not available (see Open items) |
| Hand-off 1.1 ISS-003 | Error pages render with every DB query failing; `/healthz` 503 | `templatetags/navigation.py:30-53`; `test_shell_without_database.py` (500 localized + reference id, 404 with anonymous shell, healthz 503) |
| Hand-off 1.4 AC 2 | `/` → `/ro/`, `/en/` by Accept-Language, cookie wins | `test_root_redirect.py` (4); real server lines above |
| Hand-off 1.4 ISS-003 | Switcher in the top bar, duotone in the student theme | `_top_bar.html:9`; `test_switcher_icon_follows_the_theme` (×2); real server `translate-duotone` for the student only |
| Must Read: UI/UX tokens | 64px sticky top bar, nav sizes and current style, account panel, skip link, main widths/padding, greeting sizes, 3/4-column grids | `static/css/layout.css` (tokens only; checked by the existing raw-hex / `!important` tests) |
| Must Read: patterns §7.4 CSP | No eval, no inline script, no injected style | `base.html:8`; inline-script tests |

**AC rows: 11 + 3a = all AC in the story; every Step and hand-off has a proven row.**

### Gate 2: Negative space
- No DB writes on a home render: `test_home_render_writes_nothing` (non-SELECT queries = `[]`).
- No privilege-revealing links: AC 9 tests; the admin link appears only for Admin.
- No GET logout: sign-out is a POST form (`_top_bar.html:16`); GET `/accounts/logout/` stays 405 (existing matrix test).
- No inline script/style, no CDN: tests above plus the real-server count of 0.
- Unresolvable registry entries never 500: `test_available_sections_never_raises_for_unknown_url_names`.
- Out of scope, untouched: no notification badge, no `hx-boost`, no feature pages.

### Gate 3: Contract consistency
- Menu and cards come from one registry: `test_menu_and_cards_list_the_same_sections` (×4).
- Story 1.4's switcher contract unchanged (its 45 tests pass); Story 1.6 primitives reused unchanged.
- Story 1.1 error contract: status codes unchanged. **Changed by owner decision (2026-10-23):** error pages may set the `csrftoken` cookie (layout forms), never a session; recorded in the Story 1.1 file.

### Open items (honest)
- **Screenshots, the browser console CSP check, keyboard walk-through (skip link, account menu) and screen reader**: not possible without a browser here. The equivalent HTML/header evidence is above; Story 1.10's Playwright journeys and the pending manual browser pass cover them.

## Challenges Encountered

| Challenge | Resolution | Time Spent |
|-----------|------------|------------|
| The layout reads the session-backed user and messages, which breaks error pages when the DB is down | `shell_user` / `shell_messages` tags fall back to an anonymous shell on `DatabaseError` | 0.5 h |
| Test URLconfs without the project routes broke once the layout linked sign-in, language switch and home | Appended `config.urls` patterns after the test routes (the story's own test pattern) | 0.25 h |
| The CSRF token in the layout makes error pages set `csrftoken`, against Story 1.1's "no cookie" | Asked the owner: allow `csrftoken` only, never a session; tests and Story 1.1 file updated | 0.25 h |
| `makemessages` fuzzy-matched 10 new strings to wrong translations (e.g. "Sign out" → "Autentificare") and copied a translator comment | Every entry written by hand; fuzzy flags and the stray comment removed; `msgfmt --check` passes | 0.25 h |

## Deviations from Plan

- **htmx header**: the upstream `htmx.min.js` has no header comment, and htmx 2 is licensed **0BSD** (the story says BSD-2). One `/*! … */` line with version, licence and upstream sha256 was added; the rest of the file is byte-identical to the npm release.
- **Error-page cookie**: Story 1.1's "no cookie" became "no session; `csrftoken` allowed" (owner decision 2026-10-23).
- **Home intro lines**: each role home has one translated intro line under the greeting (not specified; content only).
- **Card icons**: shown at 32px via `layout.css` (the design token) without changing Story 1.6's `ui_card`.

## Lessons Learned

1. A shared layout is part of every error path. It must degrade (anonymous shell) rather than depend on the database.
2. Adding a site-wide frame changes contracts other stories pinned (cookies, byte-identical bodies, "no script"). Run the full suite early and settle real conflicts with the owner instead of weakening tests silently.
3. Never trust `makemessages` fuzzy matches: review every entry it touches.

## Next Steps

- [x] Ready for code review (`aire-review-code` for 1.7)
- [ ] Manual browser pass (screenshots, console CSP, keyboard, screen reader), or Story 1.10's E2E
