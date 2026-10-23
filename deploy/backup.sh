#!/usr/bin/env bash
# Consistent SQLite backup via the online backup API (architecture ADR-004: never a raw copy).
#   backup.sh pre-deploy   -> local snapshot only (used for rollback); prints its path
#   backup.sh nightly      -> snapshot, encrypted with age, uploaded to Object Storage
# Retention: daily/ 30 days, monthly/ 12 months (bucket lifecycle rules, Terraform bootstrap).
set -euo pipefail

label=${1:?usage: backup.sh pre-deploy|nightly}
# shellcheck source=/dev/null
source /etc/learnplat/deploy.env      # LEARNPLAT_ENV
SNAPSHOT_DIR=/data/backups
stamp=$(date -u +%Y%m%dT%H%M%SZ)
snapshot="${SNAPSHOT_DIR}/${stamp}-${label}.sqlite3"

# Runs inside the app container (it owns /data and has Python's sqlite3).
docker exec learnplat-app-1 python -c "
import sqlite3, sys
source = sqlite3.connect('/data/db.sqlite3')
target = sqlite3.connect(sys.argv[1])
with target:
    source.backup(target)
target.close()
source.close()
" "${snapshot}"

# Keep the 5 newest local snapshots of each kind.
find "${SNAPSHOT_DIR}" -maxdepth 1 -name "*-${label}.sqlite3" -printf '%T@ %p\n' \
  | sort -rn | tail -n +6 | cut -d' ' -f2- | xargs -r rm -f

if [[ "${label}" == "pre-deploy" ]]; then
  echo "${snapshot}"
  exit 0
fi

# shellcheck source=/dev/null
source /etc/learnplat/backup.env      # RCLONE_CONFIG_HETZNER_*, BACKUP_BUCKET, HEARTBEAT_URL
encrypted="${snapshot}.age"
age --encrypt --recipients-file /etc/learnplat/backup.pub --output "${encrypted}" "${snapshot}"
# Kind first in the key: the bucket lifecycle rules match on the "daily/" and "monthly/" prefixes.
bucket="hetzner:${BACKUP_BUCKET}"
rclone copyto "${encrypted}" "${bucket}/daily/${LEARNPLAT_ENV}/${stamp}.sqlite3.age"
if [[ "$(date -u +%d)" == "01" ]]; then
  rclone copyto "${encrypted}" "${bucket}/monthly/${LEARNPLAT_ENV}/${stamp}.sqlite3.age"
fi
rm -f "${encrypted}"
if [[ -n "${HEARTBEAT_URL:-}" ]]; then
  curl -fsS --max-time 10 "${HEARTBEAT_URL}" >/dev/null   # alert fires when this goes missing
fi
echo "backup: ${stamp} uploaded to ${bucket}/daily/${LEARNPLAT_ENV}/"
