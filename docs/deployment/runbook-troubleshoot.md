# Runbook: Troubleshooting

| Symptom | Check | Fix |
|---|---|---|
| New commit never reaches staging | Actions run of **Deploy staging**; on the VM `journalctl -u learnplat-watch -n 50` | GHCR login expired (`docker login ghcr.io`); `failed-image` equals the tag digest → a previous attempt failed; see `last-deploy.json` |
| Deploy rolled back | `cat /var/lib/learnplat/last-deploy.json`; `docker logs learnplat-app-1 --tail 100` | Usually a migration or settings error; fix forward, merge again |
| `/healthz` 503 | App log `healthz.db_unavailable` / `healthz.data_dir_not_writable` | `/data` not mounted (`mountpoint /data`, `learnplat-data-volume <device>`), disk full (`df -h /data`), permissions (`chown -R 10001:10001 /data`) |
| `/data` missing after reboot | `cryptsetup status learnplat-data`, `/etc/crypttab` | Key file `/etc/learnplat/data.key` present? Run `/usr/local/sbin/learnplat-data-volume /dev/disk/by-id/scsi-0HC_Volume_<id>` |
| 502 from Nginx | `docker ps` (app healthy?), `docker logs learnplat-nginx-1` | App starting or crashed; `make up` / redeploy |
| No CSS/JS on pages | `curl -I https://<domain>/static/css/tokens.css` | Static volume not populated: restart the app (entrypoint copies `staticfiles`); DEV hand-off: WhiteNoise |
| 429 on sign-in | Nginx login rate limit (5/min/IP, burst 5) | Expected under brute force; shared school IP? Raise `rate`/`burst` in `nginx/conf.d/00-http-context.conf` |
| Locked-out account | Admin → Sign-in lockouts | Delete the attempt (unlock), audited |
| Certificate expired | `certbot certificates`; `systemctl list-timers certbot*` | `certbot renew`; check port 80 reachable and the webroot volume |
| Backup alert | `journalctl -u learnplat-backup -n 50` | Object Storage keys, `backup.pub`, disk space for `/data/backups` |
| Terraform: required variable | `operator_ip_addresses` / `operator_ssh_public_keys` not set | Set the `TF_VAR_*` secrets / env vars |
| Terraform: bucket name taken | bootstrap error | Re-run bootstrap (a new random suffix) or import (rulebook NC6) |
| Disk filling | `docker system df`, `du -sh /data/backups /var/lib/learnplat/releases` | `docker image prune -a --filter until=168h`; remove old release dirs (keep the current and previous) |

Logs: `docker logs learnplat-app-1` (JSON lines with `request_id`), `docker logs learnplat-nginx-1`, `/var/log/learnplat/healthcheck.log`, `journalctl -u learnplat-watch -u learnplat-backup`.
