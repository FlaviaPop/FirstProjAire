#!/usr/bin/env bash
# Deploy one image (by digest) on this VM, with a health gate and automatic rollback
# (rulebook R1/R2: the previous image is saved BEFORE deploying and actually restored on failure).
#   deploy.sh <image@sha256:...> <release-dir>
set -euo pipefail

new_image=$1
release_dir=$2
STATE_DIR=/var/lib/learnplat
# shellcheck source=/dev/null
source /etc/learnplat/deploy.env
export APP_DOMAIN

compose() {
  docker compose --project-directory "${release_dir}" -f "${release_dir}/docker-compose.prod.yml" "$@"
}

healthy() {
  local attempt
  for attempt in $(seq 1 30); do            # 30 attempts, 2 s apart
    if compose exec -T app python /app/docker/healthcheck.py; then
      return 0
    fi
    echo "deploy: waiting for /healthz (${attempt}/30)"
    sleep 2
  done
  return 1
}

record() {  # status image
  printf '{"time": "%s", "status": "%s", "image": "%s"}\n' "$(date -Is)" "$1" "$2" \
    > "${STATE_DIR}/last-deploy.json"
}

previous_image=$(cat "${STATE_DIR}/current-image" 2>/dev/null || true)
previous_release=$(cat "${STATE_DIR}/current-release" 2>/dev/null || true)
snapshot=""
if [[ -n "${previous_image}" ]]; then
  snapshot=$("${release_dir}/backup.sh" pre-deploy)   # consistent SQLite copy, local only
fi

LEARNPLAT_IMAGE=${new_image} compose up -d --remove-orphans
if LEARNPLAT_IMAGE=${new_image} healthy; then
  echo "${new_image}" > "${STATE_DIR}/current-image"
  echo "${release_dir}" > "${STATE_DIR}/current-release"
  rm -f "${STATE_DIR}/failed-image"
  record deployed "${new_image}"
  echo "deploy: ${new_image} is healthy"
  exit 0
fi

echo "deploy: ${new_image} failed its health check; rolling back" >&2
record failed "${new_image}"
echo "${new_image}" > "${STATE_DIR}/failed-image"   # learnplat-watch won't retry it
if [[ -z "${previous_image}" ]]; then
  echo "deploy: first deploy failed, nothing to roll back to" >&2
  exit 1
fi
release_dir=${previous_release}
export LEARNPLAT_IMAGE=${previous_image}
compose stop app
# Migrations of the failed image may have changed the schema: restore the pre-deploy snapshot.
"${release_dir}/restore.sh" "${snapshot}"
compose up -d --remove-orphans
if healthy; then
  record rolled-back "${previous_image}"
  echo "deploy: rolled back to ${previous_image}" >&2
else
  record rollback-failed "${previous_image}"
  echo "deploy: ROLLBACK FAILED, manual intervention needed (runbook)" >&2
fi
exit 1
