#!/usr/bin/env bash
# Put a local SQLite snapshot back in place. The app container must be stopped.
#   restore.sh /data/backups/<stamp>-pre-deploy.sqlite3
set -euo pipefail

snapshot=${1:?usage: restore.sh <snapshot.sqlite3>}
[[ -f "${snapshot}" ]] || { echo "restore: ${snapshot} not found" >&2; exit 1; }
rm -f /data/db.sqlite3-wal /data/db.sqlite3-shm
cp --preserve=mode,ownership "${snapshot}" /data/db.sqlite3
echo "restore: /data/db.sqlite3 restored from ${snapshot}"
