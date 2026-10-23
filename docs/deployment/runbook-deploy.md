# Runbook: First Deployment and Routine Deploys

**Audience**: the operator setting up or running learnplat. **Prerequisites**: open items in `deployment-plan.md` §10 provided (domains, alert e-mail, operator IPs + SSH keys, Hetzner account).
Every command below changes real resources: run them in order, one at a time.

## A. One-time setup

1. **Hetzner account and project `learnplat`**: create an API token (Read & Write) and Object Storage credentials (fsn1).
2. **Bootstrap the buckets** (operator laptop, local state):
   ```bash
   export AWS_ACCESS_KEY_ID=<object storage key> AWS_SECRET_ACCESS_KEY=<secret>
   make tf-bootstrap
   git add terraform/backend.hcl terraform/bootstrap.auto.tfvars && git commit -m "Terraform backend"
   ```
   Keep `terraform/bootstrap/terraform.tfstate` safe (password manager attachment); it's gitignored.
3. **Servers**:
   ```bash
   export HCLOUD_TOKEN=<token>
   export TF_VAR_operator_ip_addresses='["<your-ip>/32"]'
   export TF_VAR_operator_ssh_public_keys='{"owner": "ssh-ed25519 AAAA…"}'
   make tf-plan     # review: 1 firewall, 2 volumes, 2 servers, 2 attachments, N SSH keys
   make tf-apply
   terraform -chdir=terraform output servers   # IPs for DNS
   ```
4. **DNS (manual, at your registrar)**: one `A` (and `AAAA`) record per environment:
   | Record | Type | Value |
   |---|---|---|
   | `<prod domain>` | A / AAAA | `servers.prod.ipv4` / `.ipv6` |
   | `<staging domain>` | A / AAAA | `servers.staging.ipv4` / `.ipv6` |
   Wait until `dig +short <domain>` returns the IP.
5. **Each VM** (`ssh root@<ip>`; cloud-init has already run: `cloud-init status --wait`):
   - **Encryption key backup**: copy `/etc/learnplat/data.key` (base64: `base64 /etc/learnplat/data.key`) into the password manager. Without it a detached volume can't be read.
   - `echo 'APP_DOMAIN=<domain>' >> /etc/learnplat/deploy.env`
   - Create `/etc/learnplat/app.env` (0600) per `pipeline-secrets.md` §3 (new `DJANGO_SECRET_KEY` per environment: `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`).
   - Add the Object Storage keys and `HEARTBEAT_URL` to `/etc/learnplat/backup.env`; put the age **public** key in `/etc/learnplat/backup.pub`.
   - `docker login ghcr.io -u <github user>` with a `read:packages` token.
   - Certificate: the first deploy hasn't run yet, so run the script from a checkout or copy it: `bash setup-ssl.sh <domain> <alert e-mail>` (from `deploy/setup-ssl.sh`).
6. **GitHub** (`pipeline-secrets.md` §1): environments `staging`, `production` (required reviewers), `infrastructure`; repository secrets for Terraform; variables `STAGING_URL`, `PROD_URL`; branch protection on `main`.
7. **Uptime monitor**: check `https://<domain>/healthz` every minute for both environments, alerting the alert e-mail; a heartbeat check for backups (its URL goes into `HEARTBEAT_URL`).

## B. Routine deploys

| Step | How | What happens |
|---|---|---|
| Staging | Merge a PR into `main` | `Deploy staging`: CI → image `:<sha>` → tag `staging`; the staging VM deploys within ~1 min (`journalctl -u learnplat-watch`) |
| Check | `https://<staging domain>`, workflow `verify` job | `/healthz` 200; smoke-test the changed feature |
| Production | Actions → **Deploy production** → Run workflow → SHA = the commit running on staging | Approval in `production` → tag `prod` → prod VM deploys with the health gate |
| Confirm | `ssh root@<prod>` → `cat /var/lib/learnplat/last-deploy.json` | `"status": "deployed"` with the new digest |

Migrations run automatically when the container starts. They must stay backward-compatible for one release (the automatic rollback restores the pre-deploy database snapshot).

## C. Before the pilot launch

- [ ] Restore test: download one nightly backup, decrypt with the offline age key, open it with `sqlite3`, run `PRAGMA integrity_check;` (see `runbook-rollback.md` §C).
- [ ] Simulate a failed deploy on staging (e.g. a commit whose `/healthz` fails) and confirm the automatic rollback and that `failed-image` stops retries.
- [ ] Confirm the uptime and backup alerts reach the alert e-mail.
