# Runbook: Rollback and Restore

## A. Automatic (no action)
`deploy.sh` keeps the previous image and a pre-deploy database snapshot. If `/healthz` fails 30 times (2 s apart) after a deploy, it:
1. restores the previous image;
2. restores the snapshot;
3. writes `/var/lib/learnplat/last-deploy.json` (`rolled-back`) and `failed-image`, so the watcher won't retry the bad image until the tag moves.

Check: `ssh root@<vm> cat /var/lib/learnplat/last-deploy.json`.

## B. Manual

| Situation | Action |
|---|---|
| Bad release in **production** (permanent fix) | Actions → **Deploy production** → SHA of the previous good release. The `prod` tag moves back; the VM redeploys it |
| Need to pin one VM immediately | `ssh root@<vm>` → `make -C $(cat /var/lib/learnplat/current-release) rollback IMAGE=ghcr.io/flaviapop/learnplat@sha256:<previous digest>` (digests: `ls /var/lib/learnplat/releases/`; every release ships the Makefile). Afterwards `make -C $(cat /var/lib/learnplat/current-release) unpin` once a fixed release is tagged |
| Staging | Revert the commit on `main` (new deploy) |

Previous digests are the directory names under `/var/lib/learnplat/releases/` and the GHCR package versions.

## C. Restore data from a nightly backup

1. Stop the app: `LEARNPLAT_IMAGE=$(cat /var/lib/learnplat/current-image) docker compose --project-directory $(cat /var/lib/learnplat/current-release) -f $(cat /var/lib/learnplat/current-release)/docker-compose.prod.yml stop app`
2. Download and decrypt **on the operator laptop** (the private age key never goes on a server):
   ```bash
   rclone copyto hetzner:<backup bucket>/daily/<env>/<stamp>.sqlite3.age ./restore.sqlite3.age
   age --decrypt -i <offline key file> -o restore.sqlite3 restore.sqlite3.age
   sqlite3 restore.sqlite3 'PRAGMA integrity_check;'    # must print: ok
   scp restore.sqlite3 root@<vm>:/data/backups/
   ```
3. On the VM: `$(cat /var/lib/learnplat/current-release)/restore.sh /data/backups/restore.sqlite3`, then start the app again (`… up -d`), then check `/healthz`.
4. Record the restore (time, backup used, reason) in the incident notes.

## D. Lost VM
`make tf-apply` recreates it (new empty volume). Then follow `runbook-deploy.md` A.5. Restore the latest backup (C). If the **volume** survived but the boot disk didn't, re-create `/etc/learnplat/data.key` from the password manager before running `learnplat-data-volume`.
