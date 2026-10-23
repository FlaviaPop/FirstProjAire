# Deployment Plan: learnplat (Romanian Curriculum Learning Platform pilot)

**Date**: 2026-10-23 · **Agent**: DEVOPS (`aire-devops-deploy`) · **Status**: ✅ approved by the user 2026-10-23 (with LUKS2 encryption of the data volume)
**Sources**: `docs/deployment/discovery-report.md` (approved), `docs/deployment/pipeline-secrets.md`, branch `feature/devops-pipeline` (`900a936`)

---

## 1. Target architecture (server-based)

One Docker Compose stack per environment on its own Hetzner VM. SQLite needs a single writer on a local disk, so there is **one app instance per environment**.

```
                 Internet (HTTPS)
                       │
           Hetzner Cloud Firewall learnplat-fw
     80/443 from anywhere · 22 only from operator IPs · ICMP
                       │
┌──────────────── VM learnplat-<env> (CX22, Ubuntu 24.04, fsn1) ────────────────┐
│  nginx (container, 80/443)                                                     │
│    TLS (Let's Encrypt) · HTTP→HTTPS · login rate limit · X-Request-ID          │
│    /static/ from the shared volume · catch-all default server                  │
│         │ compose network (app:8000, never published)                          │
│  app (container): migrate → gunicorn 3 workers → Django (prod settings)        │
│         │                                                                      │
│  /data  ← Hetzner volume learnplat-<env>-data (LUKS2 + ext4): SQLite (WAL)     │
│  systemd: learnplat-watch.timer (1 min) · learnplat-backup.timer (02:30 RO)     │
└────────────────────────────────────────────────────────────────────────────────┘
        ▲ pulls the image tag            │ encrypted nightly backup (age)
  ghcr.io/flaviapop/learnplat         Hetzner Object Storage learnplat-backups-<suffix>
```

## 2. Environment strategy

| Environment | VM | Image tag it follows | Promoted by | Domain |
|---|---|---|---|---|
| staging | `learnplat-staging` | `staging` | `Deploy staging` workflow on every merge to `main` (automatic) | ⛔ open item |
| prod | `learnplat-prod` | `prod` | `Deploy production` workflow (`workflow_dispatch` with a SHA already proven on staging; approval in the `production` environment) | ⛔ open item |

## 3. Infrastructure naming (from discovery, unchanged)

| Resource | Name |
|---|---|
| Prefix / location | `learnplat` / `fsn1` |
| VMs | `learnplat-staging`, `learnplat-prod` (CX22, Ubuntu 24.04) |
| Data volumes | `learnplat-staging-data`, `learnplat-prod-data` (10 GB, ext4, mounted at `/data`) |
| Firewall | `learnplat-fw` (label selector `project=learnplat`) |
| SSH keys | `learnplat-<key name>` (from `TF_VAR_operator_ssh_public_keys`) |
| State bucket | `learnplat-tfstate-<4-char suffix>` (globally unique, rulebook NC1) |
| Backup bucket | `learnplat-backups-<same suffix>` |
| Image | `ghcr.io/flaviapop/learnplat` (`:<sha>`, `:staging`, `:prod`) |
| Compose project / containers | `learnplat` / `learnplat-app-1`, `learnplat-nginx-1` |
| GitHub environments | `staging`, `production`, `infrastructure` |

## 4. Terraform modules (only what discovery selected)

| Module | Creates | Depends on |
|---|---|---|
| `terraform/bootstrap` (local state) | state bucket + backup bucket (versioning, lifecycle daily 30 d / monthly 366 d), writes `backend.hcl` + `bootstrap.auto.tfvars` | Object Storage keys |
| root `hcloud_ssh_key` | operator SSH keys | n/a |
| `modules/firewall` | `learnplat-fw` | n/a |
| `modules/server` × {staging, prod} | volume → server (cloud-init) → volume attachment | firewall (explicit `depends_on`), SSH keys, bootstrap outputs |

No WAF, no private DNS, no extra modules (not selected). **DNS is manual**: required records are listed in the runbook.

## 5. Dependency graph and deploy order

```
1. make tf-bootstrap        → buckets + backend.hcl + bootstrap.auto.tfvars (commit them)
2. terraform apply          → firewall → volumes → VMs (cloud-init) → volume attachments
3. DNS (manual)             → A/AAAA for each domain → VM IPs from `terraform output servers`
4. Per VM (operator, SSH)   → app.env, APP_DOMAIN, backup.env, backup.pub, GHCR login
5. setup-ssl.sh <domain> <e-mail>   → first certificate (standalone), renewal hook → nginx reload
6. GitHub                   → environments, branch protection, variables STAGING_URL/PROD_URL
7. Merge to main            → CI → image → `staging` tag → staging VM deploys (≤1 min)
8. Deploy production (SHA)  → approval → `prod` tag → prod VM deploys
```

## 6. Secret management

GitHub repository secrets for Terraform; GitHub `GITHUB_TOKEN` for GHCR; per-VM root-only files under `/etc/learnplat/` (app, backup); the age **private** key offline only. Full list: `docs/deployment/pipeline-secrets.md`. No secret in git, Terraform state inputs, or cloud-init.

## 7. Rollback strategy

- **Automatic** (`deploy/deploy.sh`):
  - The previous image and release are recorded before deploying, and a pre-deploy SQLite snapshot is taken.
  - `/healthz` is checked 30 times, 2 s apart.
  - On failure: restore the previous image and the snapshot, re-check health, record `failed-image` so the watcher doesn't retry it, and write `last-deploy.json`.
- **Manual on one VM**: `make rollback IMAGE=…@sha256:…` (pins the image), then `make unpin` after the fix.
- **Permanent**: run `Deploy production` with the previous SHA (moves the `prod` tag).
- **Data**: restore an encrypted nightly backup (runbook-rollback.md). Test a restore before the pilot.

## 8. Health checks and monitoring

| Check | Where | Action |
|---|---|---|
| Container `HEALTHCHECK` (`/healthz` via the app's own probe) | every 30 s | Docker marks the container unhealthy; Nginx starts only after the app is healthy |
| Deploy gate | each deploy | rollback on failure |
| `deploy/healthcheck.sh` (cron, every 5 min) | each VM | restarts the stack if `/healthz` fails 3 times in a row; logs it |
| External uptime monitor on `https://<domain>/healthz` | every minute | e-mail alert ⛔ (alert address open) |
| Backup heartbeat (`HEARTBEAT_URL`) | nightly | alert when missing |
| Docker log rotation | daemon.json: 10 MB × 5 per container | disk never fills |
| Host log rotation (`deploy/logrotate.conf`) | `/var/log/learnplat/*.log` | 14 days, compressed |

## 9. What this workflow adds (on `feature/devops-pipeline`)

- `deploy/setup-ssl.sh`: certbot standalone first issue, webroot renewal, nginx reload hook; domain and e-mail as **arguments** (no hardcoding).
- `deploy/healthcheck.sh` + cron entry (cloud-init), `deploy/logrotate.conf`.
- `docs/deployment/runbook-deploy.md`, `runbook-rollback.md`, `runbook-troubleshoot.md`, `architecture.md`, `quick-reference.md`.
- Full re-validation: terraform, actionlint, shellcheck/`bash -n`, `nginx -t`, cloud-init render, and cross-file consistency.

**Not added:**
- `server-setup.sh` / `app-setup.sh` / UFW: cloud-init already does server and app setup, and the Hetzner firewall is the network boundary. UFW would also be bypassed by Docker's published ports, so it would give a false sense of protection.
- HSTS changes: the app already sends `Strict-Transport-Security` (1 year) from `config.settings.prod`. `includeSubDomains`/`preload` remain an owner decision once the domain is known (DEV hand-off).

## 10. Open items (block the real run, not the generation)

| # | Item | Blocks |
|---|---|---|
| 1 | Domains (prod + staging) | DNS, certificates, `APP_DOMAIN`, ALLOWED_HOSTS |
| 2 | Alert e-mail | uptime + backup alerts, certbot registration |
| 3 | Operator IPs + SSH public keys | `terraform plan/apply` (required variables) |
| 4 | Hetzner account: API token, Object Storage keys | bootstrap + apply |
| 5 | DEV hand-off: wire WhiteNoise **or** keep Nginx static serving | (works today via Nginx) |
| 6 | ~~Volume encryption~~ **decided: LUKS2** (`deploy/data-volume.sh`); copy the key to the password manager after first boot | n/a |

Every command that creates or changes real resources (bootstrap, apply, certbot, GitHub settings) runs **only after your explicit "yes", one command at a time**.
