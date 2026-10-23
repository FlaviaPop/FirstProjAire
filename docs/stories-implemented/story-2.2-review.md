# Story 2.2 Self-Review

**Date**: 2026-10-23
**Story**: Catalogue & Subject Pages (`docs/plans/stories/epic-2-story-2.2-Catalogue-and-Subject-Pages.md`)
**Developer**: DEV Agent (STORY-AGENT, in-one-go mode, atomic story)

---

## What Was Implemented

- **Query service** (`persistence/catalogue/queries.py`): frozen `SubjectDTO` / `GradeDTO` (with `has_active`), `catalogue_overview()` (grades + prefetched subjects, both ordered by `sort_order`, exactly 2 SQL queries) and `active_subject(id)` (one `select_related` query, `is_active=True` filtered **inside** the query, `NotFound("subject")` for inactive and unknown alike).
- **Views/URLs** (`web/catalogue/`): `catalogue:index` → `GET /<lang>/catalogue/` (`@require_safe` + `@require_authenticated`), `catalogue:subject` → `GET /<lang>/subjects/<int:subject_id>/` (`@require_safe` + `@require_permission(LESSONS_VIEW)`). `can_open` and `icon_variant` come from the session user's role only. Included in `i18n_patterns` (alphabetical: accounts → catalogue → home).
- **Templates**: `catalogue/index.html` (page header "Catalogue", "Grades and subjects" lead, one `_grade_section.html` per level, or `ui_empty_state("The catalogue is not available yet.")`), `catalogue/_grade_section.html` (`<section aria-labelledby>` + `<h2>` + Pilot label + grid of `ui_card … level=3` / `ui_disabled_tile`), `catalogue/subject.html` (`ui_page_header` with breadcrumb + `ui_empty_state("No chapters are published yet.")`).
- **CSS**: `static/css/catalogue.css` (feature-local `catalogue_grid` organism, tokens only), linked from `index.html` through `{% block extra_css %}`.
- **Matrix rows** for `/ro/catalogue/` (anonymous 302, four roles 200); subject access tested in this story's module.
- **Translations**: RO + EN for the six AC 12 strings (4 new, 2 existing re-referenced); two fuzzy matches from `makemessages` corrected by hand.
- The Student "Learn" menu item and home card now appear automatically (Story 1.7 registry); other roles' menus unchanged.

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `src/infrastructure/persistence/catalogue/queries.py` | New | DTOs, `catalogue_overview()`, `active_subject()` |
| `src/infrastructure/web/catalogue/__init__.py` | New | package |
| `src/infrastructure/web/catalogue/views.py` | New | `index`, `subject` views + breadcrumb helper |
| `src/infrastructure/web/catalogue/urls.py` | New | `app_name="catalogue"`, 2 routes |
| `src/infrastructure/web/templates/catalogue/index.html` | New | catalogue page |
| `src/infrastructure/web/templates/catalogue/_grade_section.html` | New | one level (section, h2, Pilot label, grid) |
| `src/infrastructure/web/templates/catalogue/subject.html` | New | subject page (breadcrumb + empty state) |
| `src/infrastructure/web/static/css/catalogue.css` | New | grid organism, tokens only |
| `src/config/urls.py` | Modified | one include line (Story 2.2 comment) |
| `src/infrastructure/i18n/locale/ro/LC_MESSAGES/django.po` | Modified | 4 new RO entries + source refs |
| `src/infrastructure/i18n/locale/en/LC_MESSAGES/django.po` | Modified | 4 new EN entries (msgstr == msgid) + source refs |
| `tests/integration/web/test_role_access_matrix.py` | Modified | `# Story 2.2 — catalogue` rows |
| `tests/integration/web/catalogue/test_catalogue_queries.py` | New | 18 tests: query service |
| `tests/integration/web/catalogue/test_catalogue_pages.py` | New | catalogue page, all roles, AC 11 nav |
| `tests/integration/web/catalogue/test_subject_page.py` | New | subject page access, 404/403, breadcrumb |
| `tests/integration/web/catalogue/test_catalogue_translations.py` | New | AC 12 RO/EN entries + rendered RO pages |

## Patterns Applied

| Pattern | Where Applied | Notes |
|---------|---------------|-------|
| Query services / CQRS-lite (§6.3, ADR-005) | `queries.py`; views import it directly | frozen DTOs, `Prefetch` / `select_related`, scope inside the query, no container change |
| Thin views + decorators (§7.1–7.2) | `views.py` | ≤ 13 lines each; one-line docstring naming route + permission; `@require_safe` outermost keeps `required_permissions` |
| Response conventions (§7.5, §8) | `NotFound` → `DomainErrorMiddleware` → 404; `PermissionDenied` → 403 | never caught in the view |
| Primitives & i18n (§11.2–11.3) | templates | `ui_page_header`, `ui_card`, `ui_disabled_tile`, `ui_empty_state`; names only via `{% localized %}` / `localized()` |
| Testing (§12) | `tests/integration/web/catalogue/` | AAA, behavioural names, seed-driven ids, role fixtures |

## Testing Summary

- **New tests**: 131 in `tests/integration/web/catalogue/` + 5 matrix rows = 136 (suite 1350 → 1486)
- **Full suite**: 1486 passed, 3 consecutive runs
- **Coverage**: 100.00% total (domain 100%, application 100%); `queries.py` and `web/catalogue/*` 100%

**Test Output**: see DoD Evidence.

## DoD Evidence

### TDD — red before implementation (tests written first, run, failing)

```
ERROR tests/integration/web/catalogue/test_catalogue_queries.py
E   ModuleNotFoundError: No module named 'infrastructure.persistence.catalogue.queries'
--- remaining catalogue + matrix tests (queries module ignored) ---
96 failed, 36 passed in 0.96s
```

### Full suite + coverage (`uv run pytest -q --cov=src --cov-branch --cov-fail-under=85`), 3 runs

```
run 1: TOTAL 1362 0 194 0 100%  | Required test coverage of 85% reached. Total coverage: 100.00% | 1486 passed in 12.72s
run 2: TOTAL 1362 0 194 0 100%  | Required test coverage of 85% reached. Total coverage: 100.00% | 1486 passed in 13.21s
run 3: TOTAL 1362 0 194 0 100%  | Required test coverage of 85% reached. Total coverage: 100.00% | 1486 passed in 13.79s
src/infrastructure/persistence/catalogue/queries.py          30      0      2      0   100%
src/infrastructure/web/catalogue/__init__.py                  0      0      0      0   100%
src/infrastructure/web/catalogue/urls.py                      4      0      0      0   100%
src/infrastructure/web/catalogue/views.py                    30      0      0      0   100%
src/domain/** and src/application/**: 18 files, all 100%
```

Selected verbose results (incl. the 2-query assertion and the cross-cutting tests):

```
tests/integration/web/catalogue/test_catalogue_queries.py::test_overview_uses_two_queries PASSED
tests/integration/web/catalogue/test_subject_page.py::test_inactive_and_unknown_subjects_are_identical_404s PASSED
tests/integration/web/catalogue/test_subject_page.py::test_inactive_and_unknown_404_pages_are_byte_identical PASSED
tests/integration/web/catalogue/test_subject_page.py::test_hidden_subject_404_is_logged_as_not_found PASSED
tests/integration/web/test_role_access_matrix.py::test_role_access_matrix[anonymous-/ro/catalogue/-302] PASSED
tests/integration/web/test_role_access_matrix.py::test_role_access_matrix[Student-/ro/catalogue/-200] PASSED
tests/integration/web/test_role_access_matrix.py::test_role_access_matrix[Teacher-/ro/catalogue/-200] PASSED
tests/integration/web/test_role_access_matrix.py::test_role_access_matrix[Parent/Guardian-/ro/catalogue/-200] PASSED
tests/integration/web/test_role_access_matrix.py::test_role_access_matrix[Admin-/ro/catalogue/-200] PASSED
tests/integration/web/test_url_protection.py::test_every_url_is_protected_or_public PASSED
tests/integration/web/test_url_protection.py::test_every_debug_only_url_is_protected_public_or_allow_listed PASSED
tests/integration/web/home/test_navigation.py::test_every_rendered_link_is_permitted_for_the_role[STUDENT] PASSED
tests/integration/web/home/test_navigation.py::test_menu_and_cards_list_the_same_sections[STUDENT] PASSED
tests/unit/infrastructure/test_i18n_helpers.py -k translations_complete: 1 passed
(catalogue + matrix + url_protection + home modules, -v: 249 PASSED, 0 FAILED)
```

### Static gates (each read from its own output line)

```
$ uv run ruff format --check .                       -> 174 files already formatted
$ uv run ruff check .                                -> All checks passed!
$ uv run mypy --no-incremental                       -> Success: no issues found in 115 source files
$ PYTHONPATH=src uv run lint-imports                 -> Layers point inward KEPT / Domain is framework-free KEPT / Contracts: 2 kept, 0 broken.
$ uv run python manage.py makemigrations --check --dry-run -> No changes detected
```

### Translations

```
$ uv run python manage.py makemessages -l ro -l en --no-wrap --ignore=.venv --ignore=.claude --ignore=docs --ignore=SPEC --ignore=tests
processing locale ro / processing locale en
-> fuzzy matches produced (both corrected by hand, fuzzy flags and "#|" lines removed):
   "Grades and subjects"                -> fuzzy "Alege o materie"                 -> "Clase și discipline"
   "The catalogue is not available yet." -> fuzzy "Un capitol nou este disponibil." -> "Catalogul nu este încă disponibil."
   new: "Available to students" -> "Disponibil pentru elevi"; "No chapters are published yet." -> "Încă nu sunt publicate capitole."
   existing, re-referenced: "Catalogue" -> "Catalog"; "Pilot" -> "Pilot"; EN msgstr == msgid for all six
$ msgfmt --check (ro, en) -> OK (only the pre-existing header-field warnings: PO-Revision-Date/Last-Translator/Language-Team)
$ grep -c fuzzy django.po -> ro 0, en 0
$ uv run python manage.py compilemessages --ignore=.venv --ignore=.claude -> processing file django.po (en, ro)
```

### Real-server check (fresh DB, `config.settings.dev`, `runserver 127.0.0.1:8770 --noreload`)

Fresh `DATABASE_PATH` in the scratchpad, `migrate`, one user per role via the shell (`stud`, `teach`, `par`, `adm`); seed: 111 subjects, active ids 22 CLR / 23 MEM / 24 EN; 50 = grade 5 LLR (inactive). Login via curl with the CSRF token, POST to `/ro/accounts/login/`.

```
anonymous /ro/catalogue/   -> 302 http://127.0.0.1:8770/ro/accounts/login/?next=/ro/catalogue/
anonymous /ro/subjects/23/ -> 302 http://127.0.0.1:8770/ro/accounts/login/?next=/ro/subjects/23/
== stud login POST /ro/accounts/login/ -> 302 http://127.0.0.1:8770/ro/
  GET /ro/catalogue/ -> 200 | subject links: [/ro/subjects/22/ /ro/subjects/23/ /ro/subjects/24/] | h1=1 h2=10 h3=3 | tiles(aria-disabled)=108 | 'Disponibil pentru elevi'=0 | pilot=1
  GET /ro/subjects/23/ -> 200 <h1 class="page-header__title">Matematică și explorarea mediului</h1>
  GET /ro/subjects/50/ -> 404 <h1 id="error-title">Pagina nu a fost găsită</h1>
  GET /ro/subjects/999999/ -> 404 <h1 id="error-title">Pagina nu a fost găsită</h1>
  GET /ro/subjects/abc/ -> 404 (DEBUG technical 404 page; DEBUG=False renders errors/404.html, proven by test_non_numeric_id_matches_no_route)
  GET /en/catalogue/ -> 200 | subject links: [/en/subjects/22/ /en/subjects/23/ /en/subjects/24/] | h1=1 h2=10 h3=3 | tiles=108 | pilot=1
  GET /en/subjects/23/ -> 200 <h1 class="page-header__title">Mathematics and Environmental Exploration</h1>
  GET /en/subjects/50/ -> 404 <h1 id="error-title">Page not found</h1>
  GET /en/subjects/999999/ -> 404 <h1 id="error-title">Page not found</h1>
  GET /en/subjects/abc/ -> 404
== teach / par / adm (identical results for each role):
  GET /ro/catalogue/ -> 200 | subject links: [] | h1=1 h2=10 h3=3 | tiles=108 | 'Disponibil pentru elevi'=3 | pilot=1
  GET /ro/subjects/23|50|999999/ -> 403 <h1 id="error-title">Acces interzis</h1>
  GET /ro/subjects/abc/ -> 404
  GET /en/catalogue/ -> 200 | subject links: [] | h1=1 h2=10 h3=3 | tiles=108 | 'Available to students'=3 | pilot=1
  GET /en/subjects/23|50|999999/ -> 403 <h1 id="error-title">Access denied</h1>
  GET /en/subjects/abc/ -> 404
Inline scripts (script tags without src) on every catalogue page: 0 (only htmx.min.js defer + ui.js module); style= : 0; <style : 0
Student RO level headings: Grădiniță|Clasa pregătitoare|Clasa I|Clasa a II-a Pilot|Clasa a III-a|…|Clasa a VIII-a
Home menus: stud [Acasă, Învață → /ro/catalogue/]; teach [Acasă]; par [Acasă]; adm [Acasă, Conturi]
/en/catalogue/ as student: <a href="/en/catalogue/" aria-current="page">Learn</a>
Server log: "level": "ERROR" lines = 0 (78 INFO, 31 WARNING = django.request 403/404 notices);
            domain_error INFO {"code": "not_found", "status": 404} for each student inactive/unknown request
Server stopped: pkill -f "runserver 127.0.0.1:8770"; healthz afterwards -> 000
```

**Not done (browser-only):** the four screenshots named in the story Evidence (Student catalogue RO, Teacher catalogue EN, subject page with breadcrumb + empty state, 404 for an inactive subject), visual check of the grid/colours, and the manual Tab walk (keyboard skips the unavailable tiles). No browser was available to this agent. The markup that makes these true is test-proven (tiles carry no `<a>`/`<button>`/`tabindex`; active cards are a single `<a>` inside `ui_card`, whose CSS draws the 3px focus ring), but the rendered look and real keyboard behaviour still need a human or Playwright pass (Story 1.10 journey / QA).

### Gate 1 — Spec Echo

| # | Requirement | Proof |
|---|-------------|-------|
| AC1 | `catalogue_overview()` → tuple of GradeDTO by sort_order, subjects by sort_order, exactly 2 queries | `queries.py:38-54`; `test_catalogue_queries.py:25` (`django_assert_num_queries(2)`), `:51`, `:68`, `:83`, `:95` |
| AC2 | `active_subject()` with grade names; `NotFound` for missing **or** inactive; identical 404 | `queries.py:57-78`; `test_catalogue_queries.py:33,134,157,164,172`; `test_subject_page.py:54,144` (byte-identical `<main>`, same template) |
| AC3 | `catalogue:index` `@require_authenticated`, `catalogue:subject` `@require_permission(LESSONS_VIEW)`, both `@require_safe`, POST → 405 | `views.py:44-45,58-59`; `urls.py:8-10`; `test_subject_page.py:79` (required_permissions), `:97`; `test_catalogue_pages.py:78,118,122` |
| AC4 | 10 `<section aria-labelledby>` + localized `<h2>`; active → `ui_card` with href (lessons:view) else no href + "Available to students"; inactive → `ui_disabled_tile`; Pilot label | `_grade_section.html:2-10`; `views.py:52`; `test_catalogue_pages.py:129,144,166,173,191,205,216` |
| AC5 | No `<a>` to any inactive subject (every id) | `test_catalogue_pages.py:60` (every inactive id), `:205`, `:267` |
| AC6 | Subject page: `ui_page_header` breadcrumb [Catalogue → /lang/catalogue/, grade, subject] (last `aria-current`) + `ui_empty_state("No chapters are published yet.")` | `views.py:35-41,60-70`; `subject.html:5-7`; `test_subject_page.py:42,201,221` |
| AC7 | Empty catalogue → 200 + `ui_empty_state("The catalogue is not available yet.")` | `index.html:7-13`; `test_catalogue_pages.py:82,241`; `test_catalogue_queries.py:124` |
| AC8 | Names via `{% localized %}`; EN English, RO diacritics intact | `_grade_section.html:3,6`; `views.py:39,63`; `test_catalogue_pages.py:68,144`; `test_catalogue_queries.py:103`; `test_catalogue_translations.py:52` |
| AC9 | Matrix rows anonymous 302 + 4 roles 200 for `/ro/catalogue/` | `test_role_access_matrix.py:41-44`; 5 PASSED lines above |
| AC10 | Student active 200, inactive/unknown 404; Teacher/Parent/Admin 403; anonymous 302 | `test_subject_page.py:63,69,104,109,117,124`; real-server walk |
| AC11 | Student nav "Learn" → `/<lang>/catalogue/` (registry) | `test_catalogue_pages.py:317,325,332`; real-server home menus |
| AC12 | RO/EN for the 6 strings | `ro/django.po`, `en/django.po`; `test_catalogue_translations.py:33,38,44,52,65`; `test_translations_complete` PASSED |
| Step 1 | Tests first | red run recorded above (ModuleNotFoundError + 96 failed) |
| Step 2 | Query service per story code block | `queries.py:14-78` (Prefetch ordered by sort_order; `filter(pk=…, is_active=True)`) |
| Step 3 | views + urls + include in `i18n_patterns` (alphabetical) | `views.py`, `urls.py`; `config/urls.py:18` (between accounts and home) |
| Step 4 | Templates index / _grade_section / subject; `extra_css` link | `templates/catalogue/*`; `test_catalogue_pages.py:230` |
| Step 5 | `catalogue.css` tokens only: 3 cols/space-6, staff 4 cols/space-4, Pilot accent/text/pill | `catalogue.css:24-56`; Gate 2 grep (no hex/rgba/!important); `test_stylesheets_outside_tokens_never_use_raw_hex` PASSED |
| Step 6 | Matrix rows block | `test_role_access_matrix.py:41-44` |
| Step 7 | Translations, then gates | Translations + Static gates sections above |
| RBAC-1 | Enforcement in views (decorators) | `views.py:44-45,58-59`; `test_url_protection.py::test_every_url_is_protected_or_public` PASSED |
| RBAC-2 | `is_active` filter inside the query | `queries.py:65-67`; `test_catalogue_queries.py:150` (1 query), `:164` |
| RBAC-3 | `can_open` from session role, never request input | `views.py:48-52`; `test_catalogue_pages.py:258,267`; `test_subject_page.py:172,179` |
| RBAC-4 | Role denial 403 (before existence check) | `test_subject_page.py:63,117,124` |
| SR | Reload identical, no writes | `test_catalogue_pages.py:277`; `test_subject_page.py:228`; `test_catalogue_queries.py:184` |
| SR | Anonymous → `/ro/accounts/login/?next=/ro/catalogue/` | `test_catalogue_pages.py:104`; `test_subject_page.py:88` |
| SR | `domain_error` INFO `not_found` for inactive + unknown | `test_subject_page.py:157`; server log |
| SR | `/ro/subjects/abc/` → 404, no route | `urls.py:10` (`int` converter); `test_subject_page.py:134` |
| SR | Catalogue page queries don't grow (no N+1) | `test_catalogue_pages.py:290` |
| QA | Exactly 3 student links = CLR, MEM, EN; 0 for others | `test_catalogue_pages.py:44,53,173` |
| QA | `aria-disabled` count == inactive count; tiles not focusable | `test_catalogue_pages.py:60,205` |
| QA | h2 order K, P, 1…8; only grade 2 has Pilot | `test_catalogue_pages.py:129,144,166` |
| QA | Other roles' homes/menus unchanged except Student Learn | `test_catalogue_pages.py:332`; `tests/integration/web/home/**` all PASSED |
| Ref: requirements catalogue K–8, only grade-2 CLR/MEM/EN active, others non-interactive | `test_catalogue_queries.py:118`; `test_catalogue_pages.py:205` |
| Ref: owner decision 10 levels, K Grădiniță, P before 1 | `test_catalogue_pages.py:144` |
| Ref: lessons:view = Student only | `views.py:59`; `test_subject_page.py:117` |
| Ref: NFR RO/EN UI | `test_catalogue_translations.py:52,65` |
| Ref: route catalogue (`/catalogue/` any authenticated, `/subjects/<id>/` lessons:view, 404 if inactive) | routes match the existing table in `00-system-architecture-greenfield.md` (no doc change needed) |
| Ref: ADR-005 query services from views, no container change | `views.py:15-19`; `git diff --name-only src/infrastructure/container.py` empty |
| Ref: NotFound mapped only in middleware | `views.py:62` (no try/except) |
| Ref: CSP / no inline script, autoescape | `test_catalogue_pages.py:304`; `test_subject_page.py:239`; Gate 2 |
| Ref: §7.1 thin views + docstrings | `views.py:46-70` (both < 15 lines) |
| Ref: §11.1 extend base, partial `_name.html` | `index.html:1`, `subject.html:1`, `_grade_section.html` |
| Ref: §11.2 reuse primitives, organism feature-local | `_grade_section.html:6-8`; no change under `templates/components`, `templatetags`, `css/components` |
| Ref: §11.3 English msgids, RO full | `.po` diff; `test_translations_complete` PASSED |
| Ref: §11.4 status not by colour alone, links are `<a>` | tiles carry "Unavailable" + lock icon (`test_catalogue_pages.py:205`); Pilot is a word |
| Ref: §12 AAA, role fixtures, seed-driven ids | test modules above |
| Ref: §13 no `|safe`/mark_safe, local assets | Gate 2 |
| Ref: §16 one appended block in shared files | `config/urls.py` one line; matrix one block |
| Ref: §17 files ≤ 400, functions ≤ 30, no TODO | largest file 335 lines (test), largest function 13 lines; Gate 2 |
| Ref: design tokens (accent+text Pilot, disabled tile, focus 3px, 960/1200, 3 cols, student duotone/staff regular) | `catalogue.css`; widths from `layout.css main`; focus ring from `card.css`; empty-state icon variant `test_catalogue_pages.py:241`, `test_subject_page.py:221` |
| Ref: data (seed 10 levels / 111 subjects / 3 active; grade 2 names) | `test_catalogue_queries.py:61,118,134` |
| Ref: primitives' signatures | `_grade_section.html`, `index.html`, `subject.html`, `views.py:35-41` |

**AC rows: 12 / 12. Steps: 7 / 7.**

### Gate 2 — Negative-Space Check

```
TODO/FIXME/print in new code ............................ none
|safe | mark_safe | format_html in new code ............. none
style= | <style | <script in catalogue templates ......... none
hex | rgba( | !important | http(s):// in catalogue.css ... none
direct _ro/_en in catalogue templates/views ............. none
.create( .update( .delete( .save( in catalogue code ...... none (pure read)
git diff templatetags/ components/ css/components/ layouts/ web/common/ container.py ... empty (primitives untouched)
Out of scope (chapters, teacher entry points, editing grades/subjects, search/filter): no such routes, forms or links added
  (`git status`: only the files listed in "Files Changed")
Rendered pages: 0 inline scripts, 0 style attributes (tests + real server)
```

### Gate 3 — Contract Consistency

| Producer | Consumer | Check |
|----------|----------|-------|
| `SubjectDTO(id, code, name_ro, name_en, is_active, grade_name_ro, grade_name_en)` | `_grade_section.html` (`subject.id`, `is_active`, `{% localized subject "name" %}`), `views._breadcrumbs` (`localized(subject, "grade_name")`) | every field read exists; `localized` raises on a missing field (fail loud) |
| `GradeDTO(code, name_ro, name_en, subjects, has_active)` | `_grade_section.html` (`grade.code` ids, `localized grade "name"`, `has_active`, `grade.subjects`) | matches |
| `catalogue_overview()` empty tuple | `index.html` `{% if grades %}` → empty state | `test_catalogue_pages.py:82` |
| `active_subject` → `NotFound` | `DomainErrorMiddleware` → 404 | inactive and unknown identical (`test_subject_page.py:144`) |
| view context `can_open` (bool) | template branch `subject.is_active and can_open` | both branches + tile tested for every role |
| view context `breadcrumbs` [(label, url)] | `ui_page_header` (`_pairs(…, 2)`) | 3 pairs; last has `aria-current` (`test_subject_page.py:201`) |
| URL `subjects/<int:subject_id>/` | view arg `subject_id: int` | non-int → no route (404) |
| route table (architecture doc) | `urls.py` + decorators | `/catalogue/` any authenticated; `/subjects/<id>/` lessons:view; 404 if inactive |
| `.po` msgids | template/view strings | 6 msgids referenced from `web/` sources (`test_catalogue_translations.py:44`) |

## Challenges Encountered

| Challenge | Resolution | Time Spent |
|-----------|------------|------------|
| Comparing "identical" pages: the CSRF token is re-masked per render and the language switcher's `next` echoes the requested path/query | compare `<main>` exactly and the full page with token/path normalised | short |
| `makemessages` fuzzy-matched two new msgids to unrelated old ones | rewrote both by hand, removed `#, fuzzy` and `#|` lines, verified `msgfmt --check` | short |
| `student_client` and `teacher_client` share one `client` | each test takes only one role client | short |

## Deviations from Plan

- **Planner decisions applied:** subject cards use `ui_card … level=3` (h1 → h2 → h3); the subject view builds `title` and `breadcrumbs` with `localized()`; both views set `icon_variant` like `home/views.py` (duotone for students, regular otherwise); "Grades and subjects" is the lead text of the grade list (`<p class="catalogue__lead">`), not a heading; views call the query service directly (ADR-005), no container change.
- **No `tests/integration/web/catalogue/__init__.py`:** the brief lists it, but the repo runs pytest with `--import-mode=importlib` and no other test directory has one; added none, to match the convention.
- **Extra test module `test_subject_page.py`:** subject-page tests are split from `test_catalogue_pages.py` to keep each file well under 400 lines (within `tests/integration/web/catalogue/**`).
- **Card icon is the regular variant at 32px:** `components/card.html` always renders `ui_icon icon 24` (regular). The duotone student variant would need a primitive change, which this story may not make (UI-primitives concern). `catalogue.css` sizes it to 32px as the home cards do. Flag for the primitives owner if duotone card icons are wanted.
- **Pilot label is a feature-local `<span class="catalogue__pilot">`** styled in `catalogue.css` (`ui_badge` is for counts), as the brief specifies.
- **Breadcrumb grade item has no link:** the story defines `[Catalogue → url, <grade name>, <subject name>]`, so only "Catalogue" links.
- **Screenshots/manual keyboard walk not done** (no browser available); see the DoD Evidence "Not done" note.

## Lessons Learned

1. When "identical page" is the contract, the page shell's legitimate per-request differences (CSRF mask, language-switcher `next`) have to be named and normalised explicitly, or the test proves the wrong thing.
2. `makemessages` fuzzy matching is aggressive for short new strings; review every new entry by hand, every time.

## Next Steps

- [ ] Ready for code review
- [ ] Ready for Unit test validation
- [ ] Browser pass (screenshots + Tab walk) in QA / Story 1.10 journey
