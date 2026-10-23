# Learning Platform

## Overview

A server-rendered Django web application for the Romanian primary-school curriculum. The pilot
covers grade 2 (Comunicare în limba română, Matematică și explorarea mediului, Limba engleză) for
students, teachers, parents/guardians and admins, in Romanian and English.

Design documents live in `docs/`. Start with
`docs/architecture/design/00-system-architecture-greenfield.md`.

## Prerequisites

- Python 3.12 (pinned in `.python-version`)
- [uv](https://docs.astral.sh/uv/) 0.13 or newer. uv installs Python 3.12 for you if it's missing.
- GNU gettext (`msgfmt`, `xgettext`) to compile translations. See [Translations](#translations).

## Setup

```bash
uv sync --frozen                              # install the exact versions from uv.lock
cp .env.example .env                          # optional: local overrides
uv run python manage.py migrate               # creates ./data/db.sqlite3
uv run python manage.py compilemessages --ignore=.venv   # RO/EN catalogues (needs gettext)
uv run python manage.py createsuperuser       # first operator account, always role ADMIN
```

`createsuperuser` asks for username, full name, date of birth (`YYYY-MM-DD`) and password.

## Running

```bash
uv run python manage.py runserver
curl -i http://localhost:8000/healthz         # 200 {"status": "ok", "db": "ok"}
```

`/healthz` is the public uptime probe. It returns `503 {"status": "unavailable", "db": "error"}`
when the database can't be queried or its directory isn't writable.

## Testing

```bash
uv run python manage.py compilemessages --ignore=.venv     # first: tests check real RO/EN text
uv run pytest --cov=src --cov-branch --cov-fail-under=85    # unit + integration
uv run pytest -m e2e                                        # browser journeys (Playwright)
```

Without compiled catalogues, the tests that need real translations stop with
"Compiled catalogues missing … run compilemessages".

### End-to-end tests

The CYCLE-1 journeys in `tests/e2e/` drive Chromium against a live server (pytest-playwright).
A plain `uv run pytest` skips them (`-m 'not e2e'` in `pyproject.toml`).

```bash
uv run playwright install chromium     # once per machine
uv run pytest -m e2e                   # ~10 s; add --headed to watch
```

On a failure, the trace and a screenshot land in `test-results/<test>/` (git-ignored); open a trace
with `uv run playwright show-trace test-results/<test>/trace.zip`. Each journey gets a fresh
database with the seeded catalogue restored. The test-only page `/en/e2e/dialog/` exists only in
`tests/e2e/urls.py`.

### Demos

`demos/` holds presenter demos: one command plays a cycle's happy flow in a visible browser. Each
starts a dev server on a throwaway database in a temporary directory (your `data/` is never
touched), creates the demo admin (`admin` / `Demo-Pass-2026!`), and stops everything afterwards.

```bash
uv run python demos/cycle1_happy_flow.py                         # CYCLE-1, about 1 minute
uv run python demos/cycle1_happy_flow.py --slowmo 900 --pause 2500   # slower, for presenting
```

CYCLE-1 flow: Admin creates a student, a teacher and a parent and links them (visible in the audit
log) → the student signs in in Romanian, switches to English, opens Learn and a grade-2 subject,
and is back in English after signing in again → the teacher and the parent see their homes. The
same flow runs headless in `uv run pytest -m e2e` (`tests/e2e/test_demos.py`), so it can't
silently break.

Quality gates (all must pass before merge):

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
PYTHONPATH=src uv run lint-imports
uv run python manage.py makemigrations --check --dry-run
```

## Translations

**Romanian glossary** (owner decision 2026-10-23): in pages students and parents see, a school
subject is a **"materie"** (plural "materii"), not "disciplină", and a level is a **"clasă"**
(plural "clase"). New strings follow these terms so consecutive screens never switch words.

The UI is in Romanian (default) and English. Every page lives under `/ro/…` and `/en/…`, and the
RO | EN switcher posts to `/i18n/setlang/`. Catalogues are in
`src/infrastructure/i18n/locale/{ro,en}/LC_MESSAGES/django.po`.

**Install GNU gettext** (one of):

| Where | How |
|-------|-----|
| macOS without admin rights (used on the pilot laptop) | `curl -fsSL -o mm.tar.bz2 https://micro.mamba.pm/api/micromamba/osx-arm64/latest && tar -xjf mm.tar.bz2 bin/micromamba && mv bin/micromamba ~/.local/bin/`, then `MAMBA_ROOT_PREFIX=~/.local/share/mamba micromamba create -y -n gettext -c conda-forge gettext` and `export PATH="$HOME/.local/share/mamba/envs/gettext/bin:$PATH"` |
| macOS with Homebrew | `brew install gettext` |
| Ubuntu / CI / Docker | `apt-get install -y gettext` |

**After adding or changing a translatable string:**

```bash
uv run python manage.py makemessages -l ro -l en --no-wrap \
  --ignore=.venv --ignore=.claude --ignore=docs --ignore=SPEC --ignore=tests
# fill every new msgstr in ro/django.po (and en/django.po), then:
uv run python manage.py compilemessages --ignore=.venv
```

- Always pass `--no-wrap`: catalogue tests read one entry per line. To unwrap a file that was
  wrapped by mistake: `msgcat --no-wrap -o django.po django.po`.
- `test_translations_complete` fails CI if any RO `msgstr` is empty or fuzzy. It doesn't need gettext.
- Compiled `*.mo` files are **build artefacts**: git-ignored, and produced by `compilemessages`
  in CI and the Docker build before tests run.

## Project structure

```
src/config/          Django project: settings (base/dev/test/prod), urls, wsgi
src/domain/          pure-Python business rules (stdlib only)
src/application/     use cases (import domain only)
src/infrastructure/  Django apps: persistence, web, i18n, composition root
tests/               unit/, integration/, e2e/, factories/
```

Layering is enforced by import-linter. The full rules are in
`docs/architecture/design/01-patterns-and-standards-greenfield.md`.

## Configuration

Environment variables are read only in `src/config/settings/env.py`.

| Variable | Required in prod | Dev default | Notes |
|----------|------------------|-------------|-------|
| `DJANGO_SETTINGS_MODULE` | yes | `config.settings.dev` | `config.settings.prod` in production |
| `DJANGO_SECRET_KEY` | **yes** | dev-only placeholder | prod refuses to start without it |
| `DJANGO_ALLOWED_HOSTS` | yes | `localhost,127.0.0.1` | comma-separated |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | yes | empty | `https://…` origins |
| `DATABASE_PATH` | yes | `./data/db.sqlite3` | must be on a persistent volume in prod |
| `LOG_LEVEL` | no | `INFO` | |
| `AXES_PROXY_COUNT` | no | `0` | reverse proxies in front of Django, for the login lockout's client IP. Only takes effect if `python-ipware` is installed; without it axes uses `REMOTE_ADDR` |

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ImproperlyConfigured: Required environment variable DJANGO_SECRET_KEY is not set` | Set `DJANGO_SECRET_KEY` (prod settings only) |
| `/healthz` returns 503 | Check that `DATABASE_PATH` exists and its directory is writable |
| `lint-imports` can't find `domain` | Run it as `PYTHONPATH=src uv run lint-imports` |
| `database is locked` | Only one app instance may write to the SQLite file (ADR-004) |
| "Too many attempts" (429) on sign-in | 5 failed logins lock that username+IP for 15 minutes. Wait, or run `uv run python manage.py axes_reset_username <username>` |
