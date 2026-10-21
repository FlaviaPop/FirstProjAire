# Story 1.1 Self-Review

**Date**: 2026-10-21
**Story**: Error Handling & Observability (CYCLE-1, wave 2, Dev 1)
**Developer**: DEV Agent (story-agent, in-one-go wave mode)
**Branch**: `worktree-agent-a33ec163559d54af0` (based on `feature/wave-2-dev-1` @ `179c213`)

---

## What Was Implemented

- Domain primitives (`src/domain/common/`, stdlib only): the `DomainError` → `NotFound` / `ConflictError` / `PolicyViolation` hierarchy with stable codes, the frozen `Violation(code, params)` value object, the `Clock` port, and the `Language` StrEnum with `DEFAULT_LANGUAGE = Language.RO`
- `SystemClock` adapter (aware UTC via `django.utils.timezone.now`)
- One place that maps domain errors to HTTP: `DomainErrorMiddleware` (404/422/409/400, most specific first)
- `render_error`, which picks the full page `errors/<status>.html` or the HTMX partial `errors/_partial.html` and resolves the message from `ERROR_MESSAGES` (falling back to the generic text for the status). `handler400/403/404/500` reuse it.
- `is_htmx()`, the only HTMX detector in the codebase
- Error templates for 400/403/404/409/422/500, a shared `_error.html` body (icon, `<h1>`, message, violations list, the 500 reference, "Back to home") and `_partial.html` (`role="alert"`). There is no CSS: the class hooks are styled by Story 1.6.
- JSON-lines logging on stdout: `JsonFormatter`, a `RequestContextFilter` that adds `request_id` / `user_id` / `role`, and a `StdoutHandler`
- `RequestIdMiddleware` (first middleware): accepts a valid incoming `X-Request-ID` or generates `uuid4().hex`, sets the response header, and logs one `request.completed` line (method, path without the query string, status, duration_ms)
- RO and EN `.po` entries for all 14 new message ids (written by hand; not compiled, see Known limitations)

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `src/domain/common/__init__.py`, `errors.py`, `clock.py`, `language.py` | New | Domain errors, Violation, Clock port, Language |
| `src/infrastructure/system_clock.py` | New | `SystemClock` adapter |
| `src/infrastructure/logging/__init__.py`, `request_context.py`, `json_formatter.py`, `stdout_handler.py` | New | Context variables and filter, JSON formatter, stdout handler |
| `src/infrastructure/web/common/htmx.py` | New | `is_htmx()` |
| `src/infrastructure/web/common/errors.py` | New | `GENERIC_BY_STATUS`, `ERROR_MESSAGES`, `render_error`, `handle_400/403/404/500` |
| `src/infrastructure/web/common/middleware.py` | New | `RequestIdMiddleware`, `DomainErrorMiddleware` |
| `src/infrastructure/web/templates/errors/{_error,_partial,400,403,404,409,422,500}.html` | New | Error pages and the HTMX partial |
| `src/config/settings/base.py` | Modified (shared) | `RequestIdMiddleware` inserted first and `DomainErrorMiddleware` appended last in `MIDDLEWARE`. The seed's console `LOGGING` dict is replaced by the JSON config. No other lines touched. |
| `src/config/urls.py` | Modified (shared) | Appended a block with `handler400/403/404/500` |
| `src/infrastructure/i18n/locale/{ro,en}/LC_MESSAGES/django.po` | Modified (shared) | Appended one block of 14 msgids headed `# --- Story 1.1: error pages ---` |
| `tests/unit/domain/common/test_errors.py`, `test_language.py`, `test_clock.py` | New | 15 tests |
| `tests/unit/infrastructure/test_system_clock.py`, `test_htmx.py`, `logging/test_json_formatter.py`, `logging/test_stdout_handler.py` | New | 18 tests |
| `tests/integration/web/common/test_error_middleware.py` | New | 50 tests: status mapping, pages, partials, messages, 500 reference, no session |
| `tests/integration/web/common/test_request_id_logging.py` | New | 30 tests: request id, JSON logs, privacy, user context, LOG_LEVEL |
| `tests/integration/web/common/test_error_wiring.py` | New | 15 tests: real settings and URLConf wiring, bad Host, catalogue completeness |
| `docs/stories-implemented/story-1.1-review.md` | New | This document |

Shared files **not** touched: `pyproject.toml`, `uv.lock` (no new dependency), `tests/conftest.py`, `README.md` (the `LOG_LEVEL` row already exists), `.env.example` (`LOG_LEVEL` already present), `.gitignore`, and the route catalogue (no new route; error handlers are not routes).

## Patterns Applied

| Pattern | Where Applied | Notes |
|---------|---------------|-------|
| Domain pattern §4 (+ story refinement) | `domain/common/errors.py` | `PolicyViolation` carries `Violation` objects; stdlib only |
| Response conventions §7.5 | `errors.py`, templates | Full page vs HTMX partial with the same status |
| Error handling §8 | `middleware.py:19-24,83-88` | One mapping table; non-domain exceptions return `None` |
| Logging §9 | `logging/*`, `middleware.py:47-55` | Event names plus IDs only; never-log list enforced by tests |
| Templates and i18n §11.1/§11.3 | `templates/errors/*`, `.po` | `{% translate %}`; English msgids; no inline style or script |
| Testing §12 | `tests/**` | Tests written first (red runs recorded below), AAA, behavioural names |

## Testing Summary

- **Unit tests**: 33 new (40 including Story 1.0's 7), all passing
- **Integration tests**: 95 new (118 including Story 1.0's 23), all passing
- **Total**: 158 passed, 0 failed
- **Coverage**: 100.00% overall (target 85%); `src/domain` 100%

TDD trail (red runs): domain tests failed with `ModuleNotFoundError: No module named 'domain.common.clock'`; logging/htmx tests failed on collection; integration tests failed with `No module named 'infrastructure.web.common.errors'`; the catalogue tests failed with `KeyError: 'Request could not be processed'`; and the late-log correlation tests failed (4 failed) before the fix described under Challenges.

**Test output**: see "Quality gates" below (verbatim).

## DoD Evidence

### Quality gates (Step 9), run 2026-10-21

```
$ uv run ruff format --check .
57 files already formatted
$ uv run ruff check .
All checks passed!
$ uv run mypy
Success: no issues found in 50 source files
$ PYTHONPATH=src uv run lint-imports

Layers point inward KEPT
Domain is framework-free KEPT

Contracts: 2 kept, 0 broken.
$ uv run python manage.py makemigrations --check --dry-run
No changes detected
$ uv run pytest --cov=src --cov-branch --cov-fail-under=85
============================= test session starts ==============================
django: version: 5.2.18, settings: config.settings.test (from ini)
testpaths: tests
collected 158 items

tests/integration/persistence/accounts/test_user_model.py ........       [  5%]
tests/integration/web/common/test_error_middleware.py .................. [ 16%]
................................                                         [ 36%]
tests/integration/web/common/test_error_wiring.py ...............        [ 46%]
tests/integration/web/common/test_request_id_logging.py ................ [ 56%]
..............                                                           [ 65%]
tests/integration/web/test_healthz.py .........                          [ 70%]
tests/integration/web/test_role_access_matrix.py .                       [ 71%]
tests/integration/persistence/accounts/test_restart_persistence.py ..... [ 74%]
                                                                         [ 74%]
tests/unit/config/test_env.py .......                                    [ 79%]
tests/unit/domain/common/test_clock.py .                                 [ 79%]
tests/unit/domain/common/test_errors.py ............                     [ 87%]
tests/unit/domain/common/test_language.py ..                             [ 88%]
tests/unit/infrastructure/logging/test_json_formatter.py ............    [ 96%]
tests/unit/infrastructure/logging/test_stdout_handler.py .               [ 96%]
tests/unit/infrastructure/test_htmx.py ....                              [ 99%]
tests/unit/infrastructure/test_system_clock.py .                         [100%]

================================ tests coverage ================================
Name                                                  Stmts   Miss Branch BrPart  Cover
---------------------------------------------------------------------------------------
src/config/urls.py                                        9      0      0      0   100%
src/domain/common/clock.py                                3      0      0      0   100%
src/domain/common/errors.py                              22      0      2      0   100%
src/domain/common/language.py                             5      0      0      0   100%
src/infrastructure/logging/json_formatter.py             13      0      2      0   100%
src/infrastructure/logging/request_context.py            13      0      2      0   100%
src/infrastructure/logging/stdout_handler.py              7      0      0      0   100%
src/infrastructure/system_clock.py                        5      0      0      0   100%
src/infrastructure/web/common/errors.py                  24      0      0      0   100%
src/infrastructure/web/common/health.py                  27      0      4      0   100%
src/infrastructure/web/common/htmx.py                     3      0      0      0   100%
src/infrastructure/web/common/middleware.py              50      0      4      0   100%
---------------------------------------------------------------------------------------
TOTAL                                                   218      0     14      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
============================= 158 passed in 1.74s ==============================
$ uv run coverage report --include="src/domain/*" --fail-under=100
src/domain/common/clock.py          3      0      0      0   100%
src/domain/common/errors.py        22      0      2      0   100%
src/domain/common/language.py       5      0      0      0   100%
TOTAL                              30      0      2      0   100%
```
(The coverage table omits the 0-statement `__init__.py` rows and Story 1.0 files at 100%.)

### Manual checks: real `runserver`, `DEBUG=False`

These ran against scratch-only settings and URLs outside the repo. `manual_settings` imports `config.settings.dev`, sets `DEBUG=False`, inserts `LocaleMiddleware` to simulate Story 1.4, and adds temporary views raising `PolicyViolation` (2 violations), `ConflictError` and `RuntimeError`. The `.mo` files were compiled in the scratchpad by a small Python script, because GNU `msgfmt` is missing. Nothing from this setup was committed.

```
$ curl -s localhost:8771/ro/does-not-exist
<!doctype html>
<html lang="ro">
  <title>Pagina nu a fost găsită</title>
  <svg class="icon icon--32" aria-hidden="true"><use href="/static/icons/sprite.svg#compass"></use></svg>
  <h1 id="error-title">Pagina nu a fost găsită</h1>
  <p>Nu am găsit această pagină.</p>
  <a href="/">Înapoi la pagina principală</a>
### EN 404
<html lang="en">
  <h1 id="error-title">Page not found</h1>
  <p>We could not find this page.</p>
  <a href="/">Back to home</a>
### EN 422 (2 violations)
HTTP/1.1 422 Unprocessable Entity
  <h1 id="error-title">Please check your input</h1>
  <p>Please fix the following:</p>
    <ul class="error-card__violations"><li>Total points is 95; it must be 100</li><li>There are 9 questions; there must be 10</li></ul>
### RO 409
HTTP/1.1 409 Conflict
  <h1 id="error-title">Deja finalizat</h1>
  <p>Această acțiune a fost deja efectuată și nu poate fi repetată.</p>
### EN 500  (curl -H "X-Request-ID: qa-ref-0001" "/en/boom/?password=secret")
HTTP/1.1 500 Internal Server Error
X-Request-ID: qa-ref-0001
  <h1 id="error-title">Something went wrong</h1>
  <p>Something went wrong on our side. Please try again later.</p>
  <p class="error-card__ref">Reference: qa-ref-0001</p>
### RO 500
  <p class="error-card__ref">Cod de referință: 69931cf0c71c4426bd9fa196e6e314e9</p>
### HTMX 404 partial (curl -H "HX-Request: true" /ro/does-not-exist)
HTTP/1.1 404 Not Found
Content-Type: text/html; charset=utf-8
X-Request-ID: 5666e10ac24147a0939cb923a7500d95

<div class="error-partial" role="alert">
  <p>Nu am găsit această pagină.</p>
</div>
### invalid incoming id (X-Request-ID: <script>)
X-Request-ID: e2d0359a1abc4a34ae59967962ec04dd
### bad host (Host: evil.example)
HTTP/1.1 400 Bad Request
  <h1 id="error-title">Cererea nu a putut fi procesată</h1>
```

Server stdout after the fix, run 2 (`/healthz?password=secret&dob=2018-01-01` → `ce80…`, `/ro/does-not-exist` → `dbaf…`, `/en/pv/` → `e7db…`, `/en/boom/` with `X-Request-ID: qa-ref-0002`). Every logging line is JSON. The only non-JSON stdout lines are `runserver`'s 8-line start-up banner, which is written directly and isn't log output. `grep -c -E 'password=|2018-01-01'` over the JSON lines returns `0`, and stderr is empty.

```
{"timestamp": "2026-10-21T09:38:14.788710+00:00", "level": "INFO", "logger": "infrastructure.web.common.middleware", "event": "request.completed", "request_id": "ce80b0e990eb412e8c4a2e09208cacf5", "user_id": null, "role": null, "method": "GET", "path": "/healthz", "status": 200, "duration_ms": 0.7}
{"timestamp": "2026-10-21T09:38:14.798921+00:00", "level": "INFO", "logger": "infrastructure.web.common.middleware", "event": "request.completed", "request_id": "dbafbf1aeb1d4d6dbdc041b948922ec5", "user_id": null, "role": null, "method": "GET", "path": "/ro/does-not-exist", "status": 404, "duration_ms": 2.8}
{"timestamp": "2026-10-21T09:38:14.799120+00:00", "level": "WARNING", "logger": "django.request", "event": "Not Found: /ro/does-not-exist", "request_id": "dbafbf1aeb1d4d6dbdc041b948922ec5", "user_id": null, "role": null, "status_code": 404}
{"timestamp": "2026-10-21T09:38:14.807333+00:00", "level": "INFO", "logger": "infrastructure.web.common.middleware", "event": "domain_error", "request_id": "e7db7fe8868b4a86b9c28afb2591d9ce", "user_id": null, "role": null, "code": "policy_violation", "status": 422}
{"timestamp": "2026-10-21T09:38:14.807782+00:00", "level": "INFO", "logger": "infrastructure.web.common.middleware", "event": "request.completed", "request_id": "e7db7fe8868b4a86b9c28afb2591d9ce", "user_id": null, "role": null, "method": "GET", "path": "/en/pv/", "status": 422, "duration_ms": 1.0}
{"timestamp": "2026-10-21T09:38:14.807819+00:00", "level": "WARNING", "logger": "django.request", "event": "Unprocessable Entity: /en/pv/", "request_id": "e7db7fe8868b4a86b9c28afb2591d9ce", "user_id": null, "role": null, "status_code": 422}
{"timestamp": "2026-10-21T09:38:14.816348+00:00", "level": "ERROR", "logger": "django.request", "event": "Internal Server Error: /en/boom/", "request_id": "qa-ref-0002", "user_id": null, "role": null, "status_code": 500, "exc_info": "Traceback (most recent call last):\n  File \".../django/core/handlers/exception.py\", line 55, in inner\n ... \nRuntimeError: secret internal detail"}
{"timestamp": "2026-10-21T09:38:14.816718+00:00", "level": "INFO", "logger": "infrastructure.web.common.middleware", "event": "request.completed", "request_id": "qa-ref-0002", "user_id": null, "role": null, "method": "GET", "path": "/en/boom/", "status": 500, "duration_ms": 0.8}
```
(The `exc_info` path prefix is abbreviated here; the real line holds the full traceback. "secret internal detail" is the deliberate exception text. It appears only in the server log, never on the page.)

### Gate 1 — Spec Echo

| # | Requirement | Proof |
|---|-------------|-------|
| AC1 | `DomainError`/`NotFound`/`PolicyViolation`/`ConflictError` codes; frozen `Violation(code, params)`; empty `PolicyViolation` → `ValueError` | `src/domain/common/errors.py:7-52`; `test_each_domain_error_exposes_a_stable_code`, `test_policy_violation_requires_at_least_one_violation`, `test_violation_is_immutable` |
| AC2 | `Clock` Protocol; `Language(StrEnum)` RO/EN; `DEFAULT_LANGUAGE = RO`; domain stdlib only | `clock.py:7-10`, `language.py:6-13`; `test_languages_are_romanian_default_and_english`; lint-imports "Domain is framework-free KEPT"; Gate 2 import grep |
| AC3 | `SystemClock.now()` is aware UTC via `timezone.now` | `src/infrastructure/system_clock.py:8-12`; `test_system_clock_returns_current_timezone_aware_utc_time` |
| AC4 | NotFound→404, PolicyViolation→422, Conflict→409, other→400; MRO order; non-domain → `None` | `middleware.py:19-24,83-88`; `test_errors_map_to_status_and_full_page[...]`, `test_registered_error_code_message_replaces_the_generic_text` (subclass → 409), `test_unexpected_error_shows_reference_without_details` (RuntimeError → Django 500) |
| AC5 | `handler400/403/404/500` in `config/urls.py` → `errors.py` | `src/config/urls.py:17-20`; `test_root_urlconf_uses_the_shared_error_handlers[400,403,404,500]` |
| AC6 | `errors/<status>.html` extends `layouts/base.html`; `<h1>`, explanation, "Back to home" `/`, Phosphor icon `aria-hidden` | `templates/errors/{400..500}.html:1`, `_error.html:3-10`; `test_full_page_has_one_title_icon_and_back_to_home_link[6 statuses]`, `test_full_page_shows_the_generic_message_for_its_status[6]`; manual RO/EN 404 |
| AC7 | `HX-Request: true` → `_partial.html` `role="alert"`, same status; `is_htmx` is the only detector | `_partial.html:1`, `errors.py:40`, `htmx.py:6-8`; `test_every_error_has_an_htmx_partial_with_the_same_status[6]`, `test_is_htmx_only_when_hx_request_header_is_true`; `grep -rn "HX-Request" src` → only `htmx.py`; manual HTMX curl |
| AC8 | `ERROR_MESSAGES` keyed by code (gettext_lazy); unknown code → generic for status; violations formatted with params | `errors.py:11-26,31-34`; `test_unknown_error_code_falls_back_to_the_generic_message`, `test_registered_error_code_message_replaces_the_generic_text`, `test_violation_message_is_formatted_with_its_params` |
| AC9 | 422 lists **every** violation in a `<ul>`, in order | `_error.html:6-8`; `test_policy_violation_lists_every_violation`, `test_htmx_partial_lists_every_violation`; manual EN 422 shows 2 `<li>` |
| AC10 | 500 shows `Reference: <request_id>`, no exception text or stack trace (`DEBUG=False`) | `_error.html:9`; `test_unexpected_error_shows_reference_without_details`, `test_reference_on_500_page_equals_the_response_request_id`, `test_reference_is_shown_only_on_the_500_page`; test settings `DEBUG=False`; manual curl with `DEBUG=False` |
| AC11 | `RequestIdMiddleware` first; `^[A-Za-z0-9-]{8,64}$` or `uuid4().hex`; `request.request_id`; header; exactly one INFO `request.completed` with method, path (no query), status, duration_ms | `base.py:21`, `middleware.py:17,35-56`; `test_request_id_middleware_is_first...`, `test_boundary_valid_incoming_ids_are_reused`, `test_invalid_incoming_request_id_is_replaced[6]`, `test_each_request_logs_exactly_one_completed_line`, `test_request_completed_line_has_method_status_and_duration` |
| AC12 | JSON lines on stdout: timestamp (ISO UTC), level, logger, event, request_id, user_id, role + extras; null when anonymous; level from `LOG_LEVEL` (default INFO) | `json_formatter.py:17-32`, `base.py:82-107`; `test_log_lines_are_json_with_context_keys`, `test_timestamp_is_iso_8601_utc`, `test_every_stdout_line_is_json`, `test_signed_in_user_id_and_role_are_attached`, `test_root_log_level_comes_from_log_level_env[None→INFO, WARNING]` |
| AC13 | No query strings, bodies, passwords, full names, DOB or answers in logs; `/x?password=secret` test | `middleware.py:51` (`request.path`), `json_formatter.py:9-11` (drops the attached `request`); `test_query_string_values_never_reach_logs`, `test_query_string_never_reaches_logs_on_errors`, `test_no_personal_data_of_a_signed_in_user_reaches_logs`, `test_attached_http_request_object_is_never_serialised`; manual grep → 0 |
| AC14 | One INFO `domain_error` with code+status; unexpected → ERROR with `exc_info` via `django.request` | `middleware.py:87`; `test_domain_error_logs_one_info_line_with_code_and_status`, `test_unexpected_error_logs_error_with_exc_info_and_same_request_id`; manual log lines |
| AC15 | RO and EN translations in both `.po` files (6 titles, 6 explanations, "Back to home", "Reference", "Please fix the following") | `ro/.../django.po:10-51`, `en/.../django.po:10-51`; `test_every_story_message_has_a_translation_in_both_catalogues[ro,en]`, `test_romanian_translations_differ_from_the_english_source`, `test_every_generic_message_is_in_the_catalogue`; manual RO pages (scratch `.mo`) |
| AC16 | Coverage `src/domain/common` 100%, overall ≥85% | coverage output: domain 100%, total 100.00% |
| Step 1 | Domain errors, value objects, clock, language (tests first) | files above; red run `ModuleNotFoundError: domain.common.clock` |
| Step 2 | `SystemClock` | `system_clock.py` |
| Step 3 | `request_context.py`, `json_formatter.py`, `LOGGING` | `logging/*`; `base.py:84-108` (adjusted, see Deviations) |
| Step 4 | Middleware; user read in `process_view` | `middleware.py:29-88` |
| Step 5 | `htmx.py`, `errors.py`, handlers in `urls.py` | as cited for AC5/7/8 |
| Step 6 | `_error.html`, 6 status pages, `_partial.html`; titles as listed | `templates/errors/*`; title test per status |
| Step 7 | msgids in both `.po` files, RO filled; compile deferred | AC15 row; Known limitations |
| Step 8 | `MIDDLEWARE` first/last; `LOGGING` | `base.py:21,29`; `test_request_id_middleware_is_first_and_domain_error_middleware_is_last_of_story_1_1` |
| Step 9 | Gates run, output pasted | Quality gates above |
| Ref: Design tokens / styling decision | No CSS in this story; class hooks `error-card`, `error-card__violations`, `error-card__ref`, `error-partial` | `_error.html:2,7,9`, `_partial.html:1`; `test_error_pages_carry_no_inline_style_or_script` |
| Ref: icons per status | warning-circle 409/422/400, lock-simple 403, compass 404, plugs 500, aria-hidden | `{400..500}.html:6`, `_error.html:3`; `ICONS` assertions in the title test |
| Ref: QA-observable — `lang` follows active language | `layouts/base.html:2` (`LANGUAGE_CODE`); `test_html_lang_follows_the_active_language[ro,en]`; manual `/ro/` → `lang="ro"`, `/en/` → `lang="en"` (with LocaleMiddleware simulated; see Dependencies) |
| Ref: QA-observable — header = log `request_id` = 500 Reference | `test_response_header_matches_logged_request_id`, `test_unexpected_error_logs_error_with_exc_info_and_same_request_id` |
| Ref: QA-observable — no DB rows or session/cookie from error handling; success keeps status/body | `test_error_handling_creates_no_session_or_cookie[7]`, `test_successful_response_keeps_status_and_body_and_gains_only_the_header`; all 9 `/healthz` tests still pass |
| Ref: edge — repeated failure = same status/page, new id | `test_repeated_failure_gets_same_status_and_new_request_id` |
| Ref: table row — `SuspiciousOperation`/bad Host → 400 page | `test_suspicious_operation_renders_the_400_page`, `test_disallowed_host_renders_the_400_page`; manual bad-Host curl |
| Ref: patterns §9 — `request_id` on every record during the request | `request_context.py:14-27`; `test_every_line_of_a_failing_request_carries_its_request_id[3]`, `test_late_django_lines_carry_the_signed_in_user` |
| Ref: architecture Observability — logged fields `timestamp, level, request_id, user_id, role, method, path, status, duration_ms` | `request.completed` manual log line above |
| Ref: patterns §2 file/function size | largest new file `middleware.py` = 88 lines; every function ≤ 30 lines |
| Ref: patterns §1.3 deps | no new dependency (`pyproject.toml`/`uv.lock` untouched) |

AC rows: 16 of 16. Step rows: 9 of 9.

### Gate 2 — Negative-Space Check

| Rule | Check | Result |
|------|-------|--------|
| No TODO/FIXME/print/`mark_safe`/`\|safe`/`csrf_exempt` in story code | `grep -rnE "TODO\|FIXME\|print\(\|mark_safe\|\|safe\|csrf_exempt" src/domain/common src/infrastructure/logging src/infrastructure/web/common src/infrastructure/system_clock.py src/infrastructure/web/templates/errors` | no matches (exit 1) |
| No inline style or script in templates (CSP) | `grep -rnE "<style\|<script\|style=" src/infrastructure/web/templates/errors` + `test_error_pages_carry_no_inline_style_or_script` | no matches |
| Domain imports stdlib only | `grep -rn "^import\|^from" src/domain/common` → `enum`, `datetime`, `typing`, `collections.abc`, `dataclasses`; lint-imports KEPT | ✓ |
| Only one HTMX detector | `grep -rn "HX-Request" src` → `htmx.py:7-8` only | ✓ |
| Logging code never reads query string, body or PII fields | `grep -rn "get_full_path\|QUERY_STRING\|request.body\|request.POST\|full_name\|date_of_birth\|password" src/infrastructure/logging src/infrastructure/web/common/middleware.py src/infrastructure/web/common/errors.py` | no matches (exit 1) |
| Invalid incoming id never echoed (header or log) | `test_invalid_incoming_request_id_is_replaced` asserts the bad value is absent from both | ✓ |
| No stack trace on pages | `b"Traceback" not in response.content`; manual 500 curl | ✓ |
| Out of scope not built: `@require_permission` (1.3), CSS/primitives (1.6), sprite (1.5), audit (1.8), LocaleMiddleware/gettext compile (1.4), Dockerfile/CI | `grep -n "LocaleMiddleware\|require_permission\|audit" base.py web/common/*.py` → only the pre-existing Story 1.0 docstring in `decorators.py:4`; `ls static/icons static/css/components Dockerfile .github` → none exist | ✓ |
| No compiled `.mo` or `data/` committed | `git status --porcelain \| grep -E "\.mo$\|data/"` | no matches |
| Shared files: only appended or minimal in-place changes | `git diff --stat` on shared files: `base.py` (+2 middleware lines, LOGGING dict replaced), `urls.py` (+6 appended), `.po` (+43 appended each) | ✓ |
| `/healthz` unchanged | 9/9 `test_healthz.py` pass | ✓ |

### Gate 3 — Contract Consistency

| Producer | Consumer | Consistent? |
|----------|----------|-------------|
| `_STATUS_BY_ERROR` (404/422/409/400) | `errors/<status>.html` exist for each; `GENERIC_BY_STATUS` has each key plus 403/500 | ✓ (6 templates, 6 keys) |
| `handler400/403/404/500` | `render_error(request, status)` → templates 400/403/404/500 | ✓ |
| `render_error` context (`status`, `message`, `violations`, `request_id`) | `_error.html` uses all four; `_partial.html` uses `message` and `violations` (no reference needed in a fragment) | ✓ |
| Template `{% translate %}` msgids + `GENERIC_BY_STATUS` | both `.po` catalogues (14 ids) | ✓ `test_every_generic_message_is_in_the_catalogue`, catalogue tests |
| `RequestIdMiddleware` sets `request.request_id` | `render_error` reads it for the 500 Reference; header; log `request_id` | ✓ all three equal (`test_unexpected_error_logs_error_with_exc_info_and_same_request_id`) |
| Context variables / `request.log_context` | `RequestContextFilter` → `JsonFormatter` keys | ✓ unit and integration tests |
| `LOGGING` (`filters`, `formatters`, `handlers` class paths) | `RequestContextFilter`, `JsonFormatter`, `StdoutHandler` modules | ✓ settings load in every test run and the subprocess LOG_LEVEL test |
| Story 1.3 `PermissionDenied` | `handler403` | ✓ `/pd` → 403 page |
| Story 1.2 middleware order (`RequestId` first … `DomainError`, then `Axes` last) | `base.py:21,29` | ✓ positions compatible; 1.2 appends Axes after line 29 |
| Story 1.6 class hooks | `error-card`, `error-card__violations`, `error-card__ref`, `error-partial` present | ✓ |

## Challenges Encountered

| Challenge | Resolution | Time Spent |
|-----------|------------|------------|
| The worktree was created from `main` (899c001) without the Story 1.0 code | Reset my own worktree branch to the intended base `179c213` before starting | 2 min |
| `ext://sys.stdout` freezes pytest's session-level capture stream at settings load, so `capfd` saw nothing (9 failures) | `StdoutHandler` resolves `sys.stdout` on every emit (unit-tested); also robust when a supervisor swaps stdout | 10 min |
| Real server showed Django's `django.request` 4xx WARNING lines with `request_id: null` (written after the middleware chain returns). The test client didn't reveal this. | The middleware keeps a `(request_id, user_id, role)` snapshot on `request.log_context`; the filter falls back to the request Django attaches to its records. 4 red tests first, then green; re-verified on the real server. | 15 min |
| Django attaches the `HttpRequest` to `django.request`/`django.security` records; its repr includes the query string | The formatter never serialises the `request` extra (unit test) | 5 min |
| ruff N818 wants `*Error` suffixes on `NotFound`/`PolicyViolation` | Names are fixed by the architecture's error table and the story ACs; per-line `noqa: N818` with a reason | 2 min |

## Deviations from Plan

- **`LOGGING` differs from the Step 3 snippet:** (a) the handler class is `StdoutHandler` instead of `logging.StreamHandler` + `ext://sys.stdout` (see Challenges); (b) the handler has `level=LOG_LEVEL`, so `LOG_LEVEL` caps loggers that propagate with their own level; (c) the `django` logger loses Django's default plain-text console handler and stays at a fixed `INFO`, because `DEBUG` would emit SQL with parameters, which can be personal data; (d) `django.server` (runserver access lines, which contain the query string) goes to a `NullHandler`, since `request.completed` replaces it. All of these serve AC12/AC13 ("all log output is JSON lines", "no query strings").
- **`RequestContextFilter`** has the `request.log_context` fallback described above, an addition needed for "the id is attached to every log line written during the request".
- **`render_error(request, status, exc)`** follows the story's Step 5 signature. Patterns §8's excerpt shows `(request, exception, status)`; the story is the later and more specific source.
- **`request.request_id`** (story AC11) is used instead of patterns §9's `request.id`.
- **Evidence format:** the Evidence line asks for screenshots. No browser was available to this headless agent, so the rendered HTML of the RO 404, EN 422 (two violations) and the 500 with reference is pasted from `curl` instead.
- **Extra test files** beyond the story's list (`tests/unit/infrastructure/**`, `test_error_wiring.py`, `tests/unit/domain/common/test_clock.py`) prove AC3/AC5/AC7/AC12/AC15 against the real wiring.
- **No Dockerfile:** patterns §1.1 mentions "Dockerfile · docker-entrypoint.sh — added by Story 1.1 / DevOps", but this story's Files Touched and Steps don't include one, so it's left to DevOps.

## Known limitations / dependencies

- **GNU gettext is not installed** (`msgfmt` missing), so `compilemessages` can't run. The `.po` entries were written by hand and are not compiled (Story 1.4 compiles them). Tests assert English text and the `lang` attribute and parse the `.po` files directly, so they don't depend on `.mo` files. The catalogue syntax was checked by compiling a throwaway `.mo` in the scratchpad with a small Python script; the RO pages rendered correctly from it.
- **URL prefix → active language** needs `LocaleMiddleware` (Story 1.4). Until 1.4 is merged, `/en/…` error pages render with the default `ro`. The templates already follow the active language (`test_html_lang_follows_the_active_language`), and the manual check with `LocaleMiddleware` simulated shows `/en/` → `lang="en"`.
- **CSRF failures** render Django's `csrf_failure` view, not `handler403`. Story 1.2's table expects "403 page (Story 1.1 handler)" for a POST without a CSRF token. That needs `CSRF_FAILURE_VIEW` or a `403_csrf.html`, neither of which is in this story's ACs; flagged for Story 1.2.
- **Health check with a session cookie while the DB is down:** `process_view` reads `request.user`, which loads the session from the DB, so the request returns 500 instead of `/healthz`'s 503. It's still non-2xx for monitoring; health probes don't send cookies.
- The Phosphor sprite (`icons/sprite.svg`) arrives with Story 1.5; until then the decorative `<use>` renders nothing.

## Lessons Learned

1. Verify logging on a real server: the test client hid both the late `django.request` lines without a request id and the stale-stdout problem.
2. Django attaches the full `HttpRequest` to some log records. Any JSON formatter must deny-list it, or the query string leaks.

## Next Steps

- [ ] Merge with the wave-2 branches (1.2 adds `CSPMiddleware`/`AxesMiddleware` around these entries; keep the order from Story 1.2 Prerequisites)
- [ ] Ready for code review (`aire-review-code`)
- [ ] Ready for unit test validation
- [ ] Story 1.4: compile catalogues, add `LocaleMiddleware`; Story 1.2: route CSRF failures to the 403 page
