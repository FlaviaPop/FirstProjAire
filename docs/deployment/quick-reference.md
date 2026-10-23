# Quick Reference

| Task | Command / place |
|---|---|
| Run all checks locally | `make lint && make test` |
| Deploy staging | merge to `main` |
| Deploy production | Actions → Deploy production → SHA → approve |
| Roll back production | Deploy production with the previous SHA |
| Deploy now (skip the 1-min wait) | on the VM: `/usr/local/bin/learnplat-watch` |
| What runs on a VM | `cat /var/lib/learnplat/current-image /var/lib/learnplat/last-deploy.json` |
| Pin / unpin a digest (on the VM) | `make -C $(cat /var/lib/learnplat/current-release) rollback IMAGE=…@sha256:…` / `… unpin` |
| Logs | `docker logs -f learnplat-app-1`, `docker logs -f learnplat-nginx-1`, `journalctl -u learnplat-watch -f` |
| Health | `curl -fsS https://<domain>/healthz` |
| Backup now | `$(cat /var/lib/learnplat/current-release)/backup.sh nightly` |
| Restore | `runbook-rollback.md` §C |
| Certificate | `certbot certificates`, `certbot renew --dry-run` |
| Data volume | `mountpoint /data`, `cryptsetup status learnplat-data` |
| Terraform | `make tf-plan` / `make tf-apply` (env: `HCLOUD_TOKEN`, `AWS_*`, `TF_VAR_*`) |
| Server IPs | `terraform -chdir=terraform output servers` |
