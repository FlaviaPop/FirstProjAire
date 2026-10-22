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

Quality gates (all must pass before merge):

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
PYTHONPATH=src uv run lint-imports
uv run python manage.py makemigrations --check --dry-run
```

## Translations

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
