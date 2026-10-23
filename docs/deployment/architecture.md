# Deployment Architecture

```mermaid
flowchart TD
  dev[Developer PR] --> ci["GitHub Actions CI\n(gates, gettext, E2E, gitleaks, pip-audit, CodeQL, Trivy)"]
  ci -->|merge to main| build["Deploy staging\nbuild + push :sha → tag staging"]
  build --> ghcr[(GHCR\nghcr.io/flaviapop/learnplat)]
  approve["Deploy production\n(approval, SHA)"] -->|tag prod| ghcr
  subgraph hetzner["Hetzner Cloud fsn1 — firewall learnplat-fw"]
    subgraph vmS["learnplat-staging (CX22)"]
      wS[learnplat-watch timer] --> dS[deploy.sh: backup → up → /healthz → rollback]
      nS[nginx :443] --> aS[app gunicorn :8000] --> vS[("/data LUKS2 volume\nSQLite WAL")]
    end
    subgraph vmP["learnplat-prod (CX22)"]
      wP[learnplat-watch timer] --> dP[deploy.sh]
      nP[nginx :443] --> aP[app gunicorn :8000] --> vP[("/data LUKS2 volume")]
    end
    os[(Object Storage\nlearnplat-tfstate-*, learnplat-backups-*)]
  end
  ghcr -. pull :staging .-> wS
  ghcr -. pull :prod .-> wP
  vS -. nightly age-encrypted .-> os
  vP -. nightly age-encrypted .-> os
  users[Students, teachers, parents, admins] -->|HTTPS| nP
  tf["Terraform (terraform.yml / laptop)"] --> hetzner
```

| Concern | Decision |
|---|---|
| Hosting | Hetzner Cloud fsn1, one CX22 VM per environment (EU data residency) |
| Runtime | Docker Compose: `app` (Gunicorn, 3 workers, non-root) + `nginx` |
| Data | SQLite (WAL) on a LUKS2-encrypted Hetzner volume at `/data`; single writer |
| Delivery | Pull-based: VMs follow GHCR tags; no inbound SSH from CI |
| Safety | Health-gated deploys with automatic image + DB rollback; failed digests not retried |
| Backups | Nightly SQLite online backup, age-encrypted, Object Storage: daily 30 d, monthly 12 m |
| Edge | Nginx: TLS (Let's Encrypt), login rate limit, request id, catch-all default server |
| Security in CI | gitleaks, pip-audit, Dependabot, CodeQL, Trivy (CRITICAL gate) |
| IaC | Terraform (hcloud), state in Object Storage, plan on PR / apply with approval |
