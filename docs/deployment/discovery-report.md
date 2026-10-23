# DevOps Discovery Report: Romanian Curriculum Learning Platform (pilot)

**Date**: 2026-10-23
**Agent**: DEVOPS (`aire-devops-discover`)
**Tracker path**: S (from scratch; project tracking is Local)
**Reference documents**: `SPEC/references/devops/` is empty, so 0 documents and 0 images. Nothing is pre-filled; every value below comes from auto-detection or the user.
**Status**: ✅ Discovery complete for CI. ⛔ Three required values are still open and block `aire-devops-deploy` (see [Open items](#open-items-blocking-deploy)).

---

## 1. Auto-detected application profile

| Area | Detected | Source |
|---|---|---|
| Language / runtime | Python **3.12** | `.python-version`; `pyproject.toml` `requires-python = ">=3.12,<3.13"` |
| Framework | **Django 5.2**, server-rendered templates + HTMX (vendored 2.0.11) | `pyproject.toml`, `static/js/htmx.min.js` |
| Package manager | **uv** with `uv.lock` | repo root |
| Runtime dependencies | argon2-cffi, django-axes, django-csp, markdown, nh3, gunicorn, whitenoise | `pyproject.toml [project]` |
| App server / static files | Gunicorn (1 instance, 3 sync workers), WhiteNoise | architecture §Tech stack, Deployment View |
| Database | **SQLite** file at `DATABASE_PATH` (default `./data/db.sqlite3`), WAL, `transaction_mode=IMMEDIATE` | `config/settings/base.py` |
| External services | None (no cache, queue, e-mail or SaaS) | dependencies |
| Settings for production | `config.settings.prod` (DEBUG off, SSL redirect, HSTS 1 year, secure cookies, `SECURE_PROXY_SSL_HEADER = X-Forwarded-Proto`) | `config/settings/prod.py` |
| Environment variables | `DJANGO_SETTINGS_MODULE`, `DJANGO_SECRET_KEY` (required), `DJANGO_ALLOWED_HOSTS` (required), `DJANGO_CSRF_TRUSTED_ORIGINS`, `DATABASE_PATH`, `LOG_LEVEL`, `AXES_PROXY_COUNT` | `.env.example`, settings |
| Health check | `GET /healthz`: 200 when the DB is reachable and the data dir writable, else 503; public, no personal data | `web/common/health.py` |
| Logging | JSON lines to stdout, request ids, personal and sensitive keys redacted | Story 1.1 |
| Quality gates (CI steps) | `ruff format --check .` · `ruff check .` · `mypy` · `PYTHONPATH=src lint-imports` · `manage.py makemigrations --check --dry-run` · `pytest --cov=src --cov-branch --cov-fail-under=85` (currently 1497 tests, 100%) | `pyproject.toml`, `docs/status.md` |
| Translations | `.po` sources committed; `.mo` are **build artefacts**: `manage.py compilemessages` needs **GNU gettext** in CI and in the image | README "Translations" |
| E2E tests | `pytest -m e2e` (Playwright, Chromium); excluded from the default run; first journeys come with Story 1.10 | `pyproject.toml` markers |
| Docker / CI | **None yet**: no `Dockerfile`, compose file, `.dockerignore` or `.github/workflows/`. Docker isn't installed on the dev laptop, so image builds are verified in CI | file scan |
| Terraform | None (`variables.tf` not found) | file scan |
| Repository | `https://github.com/FlaviaPop/FirstProjAire.git`, branch `main` only | `git remote` |

**Architecture constraints carried into DevOps** (from `docs/architecture/design/00-system-architecture-greenfield.md`):
- Single instance and single writer (ADR-004).
- SQLite on a local persistent, encrypted volume. **No network file shares** (WAL locking).
- Migrations run once at container start, before Gunicorn accepts traffic.
- Nightly online backup with `sqlite3 .backup` (not a raw file copy). Restores are tested before the pilot launch.
- TLS terminated in front of the app.

---

## 2. User-provided deployment requirements

| # | Decision | Value |
|---|---|---|
| 1 | Deployment model | **Server-based**: one Linux VM per environment, **Docker Compose** |
| 2 | Provider | **Hetzner Cloud** |
| 3 | Region / location | Germany, **fsn1 (Falkenstein)**; EU data residency for children's personal data |
| 4 | Environments | **staging** + **prod** |
| 5 | Project prefix | **`learnplat`** (used for every resource name) |
| 6 | VM size | **CX22** for both (2 vCPU, 4 GB RAM, 40 GB disk), Ubuntu 24.04 LTS |
| 7 | Reverse proxy / TLS | **Nginx + Let's Encrypt** (certbot auto-renew) on each VM |
| 8 | Infrastructure as Code | **Terraform** (`hcloud` provider) |
| 9 | Terraform state | **Hetzner Object Storage** (S3-compatible backend, fsn1, versioned bucket); never in git |
| 10 | Container registry | **GitHub Container Registry** (`ghcr.io`) |
| 11 | Branch / release strategy | `main` → CI → image → **staging automatically**; **prod manually** (GitHub `production` environment with required approval) |
| 12 | Deployment method | Pull + restart with **auto-rollback**: pre-deploy DB backup → `docker compose pull` → migrations at start → wait for `/healthz` = 200 → else roll back to the previous image tag **and** restore the pre-deploy backup. A few seconds of downtime are accepted (single SQLite instance; no blue-green) |
| 13 | Backups | **Hetzner Object Storage** bucket, nightly online `.backup`, **encrypted before upload**, retention **30 daily + 12 monthly** |
| 14 | Monitoring | External **uptime check on `/healthz`** (every minute, e-mail alert); **Docker log rotation** (size-capped json-file + journald); **backup success/failure alert** (alert when a nightly backup is missing) |
| 15 | Data retention | **Audit log 1 year** (scheduled purge of rows older than 12 months, needs a reviewed exception to the append-only trigger, see §8); backups 30 d + 12 m |
| 16 | Security scans | **SCA**: pip-audit on `uv.lock` + Dependabot (Python and GitHub Actions). **SAST**: Ruff security (bandit `S`) rules + GitHub **CodeQL** (Python). **DAST**: not selected |
| 17 | Auto-included (framework rule, no opt-out) | **gitleaks** (secret scanning) on every push/PR. **Trivy** on the built Docker image (the framework auto-includes it once a Dockerfile exists; the user did *not* additionally select a container-scan option, so it's informational at first: report-only, fail only on CRITICAL. Tell DEVOPS if it should be removed or made stricter) |

---

## 3. Infrastructure naming (confirmed by the user, used everywhere)

| Resource | Name / value |
|---|---|
| Project prefix | `learnplat` |
| Hetzner location | `fsn1` |
| VM (staging) | `learnplat-staging`, CX22, Ubuntu 24.04 |
| VM (prod) | `learnplat-prod`, CX22, Ubuntu 24.04 |
| Firewall | `learnplat-fw`: inbound 443 and 80 from anywhere; **22 only from operator IPs** (open item) |
| Data volume (SQLite, staging) | `learnplat-staging-data`, mounted at `/data` |
| Data volume (SQLite, prod) | `learnplat-prod-data`, mounted at `/data` |
| Backup bucket | `learnplat-backups` (Object Storage fsn1, versioning on) |
| Terraform state bucket | `learnplat-tfstate` (Object Storage fsn1, versioning on) |
| Container image | `ghcr.io/flaviapop/learnplat` (tags: git SHA + `staging`/`prod` pointers) |
| GitHub environments | `staging` (automatic), `production` (required reviewer) |
| Compose project | `learnplat` |
| Networking | **Created new by Terraform** (firewall attached to both VMs; no private network needed for a single-VM app) |

---

## 4. Per-module configuration

| Module | Configuration |
|---|---|
| **Compute (VM + Docker Compose)** | CX22 ×2, Ubuntu 24.04; Docker Engine + compose plugin; services: `app` (Gunicorn on `127.0.0.1:8000` only, never published publicly, per rulebook D2), `nginx` (80/443); `restart: unless-stopped`; app user non-root; `DJANGO_SETTINGS_MODULE=config.settings.prod`; `DATABASE_PATH=/data/db.sqlite3` |
| **Data volume** | Hetzner Volume per VM, ext4, mounted at `/data`; provider-side encryption at rest. The architecture asks for an encrypted volume: DEVOPS confirms in `aire-devops-deploy` whether Hetzner volume encryption suffices or LUKS is added |
| **Reverse proxy (Nginx)** | TLS via Let's Encrypt (HTTP-01 on port 80), HTTP→HTTPS redirect; `proxy_set_header X-Forwarded-Proto/For`; **overwrites `X-Request-ID`** (1.1 ISS-004); **login rate limit**: `limit_req_zone` (http context, rulebook N1) for `POST /*/accounts/login/`, 5/min per IP, burst 5 → 429 (1.2 ISS-005); security headers left to Django (CSP, HSTS) |
| **Container registry** | GHCR; Actions push with `GITHUB_TOKEN` (`packages: write`); VMs pull with a read-only token |
| **Backups** | systemd timer nightly: `sqlite3 /data/db.sqlite3 ".backup ..."` → encrypt (age, public key on the VM, private key offline) → upload to `learnplat-backups/<env>/YYYY/MM/DD/`; lifecycle 30 daily + 12 monthly; heartbeat to the alerting check |
| **Monitoring** | External uptime monitor on `https://<domain>/healthz` (1-minute interval), e-mail alerts (open item); Docker `json-file` log driver with `max-size`/`max-file`; backup heartbeat |
| **Secrets** | GitHub **environment secrets** (`staging`, `production`): `DJANGO_SECRET_KEY`, SSH deploy key, GHCR pull token, Object Storage keys, backup public key; on the VM in `/etc/learnplat/app.env` (root:root 600). **No secret values in this report or in git** |
| **Terraform** | `hcloud` provider; root `variables.tf` holds prefix, location, environments, server type, image, operator IPs (rulebook T11); state in `learnplat-tfstate` (S3 backend with versioning; single operator, so a lock table isn't required) |

---

## 5. Service dependency graph (startup order)

```
Terraform: firewall learnplat-fw → volumes → VMs (cloud-init: Docker, mount /data) → (manual DNS A records) → Let's Encrypt
VM boot:   /data mounted → docker compose up:
             app   (migrate → collectstatic is in the image → gunicorn; healthcheck /healthz)
             nginx (depends_on app healthy; TLS; rate limits)
Timers:    nightly backup (needs app volume) → upload → heartbeat
CI/CD:     checks → image build → GHCR → deploy (SSH) → /healthz gate → rollback on failure
```
No circular dependencies.

---

## 6. CI/CD design (input for `aire-devops-pipeline`)

**Workflow `ci.yml`** (every push and pull request to `main`), on GitHub-hosted `ubuntu-latest`:
1. Checkout; `astral-sh/setup-uv` with Python 3.12 from `.python-version`; `uv sync --frozen`.
2. `sudo apt-get install -y gettext` → `uv run python manage.py compilemessages --ignore=.venv` (**deferred item: translations in CI**).
3. Gates, each its own step so its own line is visible: `ruff format --check .`, `ruff check .`, `mypy`, `PYTHONPATH=src lint-imports`, `makemigrations --check --dry-run`, `pytest --cov=src --cov-branch --cov-fail-under=85` (coverage XML uploaded as an artefact).
4. Security: gitleaks; pip-audit (`uv export --frozen | pip-audit -r -`); Ruff `S` rules (in the lint step once enabled in `pyproject`, which is a DEV change); CodeQL in its own workflow (`codeql.yml`, push + weekly).
5. E2E job (after Story 1.10): `uv run playwright install --with-deps chromium` → `pytest -m e2e` with traces kept on failure.

**Workflow `build-deploy.yml`** (push to `main` after CI passes): build the Docker image (multi-stage: uv sync, `compilemessages`, `collectstatic`; slim runtime, non-root, `HEALTHCHECK`), Trivy scan, push `ghcr.io/flaviapop/learnplat:<sha>`; deploy to **staging** automatically; **production** via `workflow_dispatch` / environment approval with the same SHA. Reusable workflows called by path rules per rulebook W1.

**Dependabot**: `pip` (uv) weekly, `github-actions` weekly. **Branch protection** on `main`: CI required.

---

## 7. Deferred items from code reviews, now owned by DevOps

| Item | Source | Where it lands |
|---|---|---|
| gettext + `compilemessages` before tests in CI and in the Docker image | 1.4 / BUG workflow note | `ci.yml` step 2; Dockerfile build stage |
| HSTS `includeSubDomains` + `preload` | 1.0 review ISS-004 | Decide with the domain (preload is hard to undo); DEV setting change, flagged for DEV |
| Client IP behind the proxy for axes lockouts (`python-ipware`, `AXES_PROXY_COUNT=1`) | 1.2 notes | Nginx `X-Forwarded-For` + env `AXES_PROXY_COUNT=1`; DEV adds `python-ipware` if needed |
| Login rate limit | 1.2 review ISS-005 | Nginx `limit_req` (§4) |
| Audit-log retention (1 year) | 1.8 review ISS-004 | Scheduled purge job; needs a **DEV story**: a reviewed, narrowly scoped exception to the append-only trigger, and an audit row of the purge itself |
| Trust `X-Request-ID` only from the proxy | 1.1 review ISS-004 | Nginx sets/overwrites the header; app keeps accepting it only behind the proxy |
| Playwright E2E in CI | Story 1.10 | `ci.yml` E2E job |

DevOps never edits application code: the rows needing a DEV change (HSTS flags, `python-ipware`, audit purge) are hand-offs for DEV.

---

## 8. DNS and certificates

DNS configuration is **manual**. The required records will be documented in the runbook (`aire-devops-deploy`): one `A` (and optional `AAAA`) record per environment pointing to the VM's public IP, created before the first certificate request.

---

## Open items (blocking deploy)

| # | Item | Needed for | Status |
|---|---|---|---|
| 1 | **Domains** for prod and staging | Let's Encrypt, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, uptime checks, DNS runbook | ⛔ not provided |
| 2 | **Alert e-mail address** | uptime + backup alerts | ⛔ not provided |
| 3 | **Operator public IPs** for SSH | `learnplat-fw` port 22 (an empty list with default-deny locks out operators and Terraform) | ⛔ not provided |
| 4 | GitHub Actions → VM SSH path | GitHub-hosted runners have changing IPs; options: (a) open 22 to GitHub's published Actions ranges (large and changing), (b) **pull-based deploy**: a small agent on the VM polls GHCR / a deploy tag (no inbound SSH from CI) **(recommended)**, (c) a self-hosted runner on the VM | to decide in `aire-devops-pipeline` |
| 5 | Volume encryption method (Hetzner at-rest vs LUKS) | architecture "encrypted volume" | to confirm in `aire-devops-deploy` |
| 6 | HSTS preload | only once the domain is final | owner decision with the domain |

**None of these blocks the CI pipeline** (`ci.yml`, CodeQL, Dependabot, gitleaks, pip-audit, image build).

---

## Tracker

Project tracking is **Local**; no GitHub issue or Azure DevOps work item linked (see the Phase 5 question).
