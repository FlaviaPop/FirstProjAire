#!/usr/bin/env bash
# Every 5 minutes (cron): check /healthz through the app container; after 3 consecutive failures
# restart the stack once and log it. Deploys have their own gate (deploy.sh); this catches
# problems between deploys. Log: /var/log/learnplat/healthcheck.log (logrotate: 14 days).
set -euo pipefail

STATE_DIR=/var/lib/learnplat
LOG=/var/log/learnplat/healthcheck.log
mkdir -p "$(dirname "${LOG}")"
release=$(cat "${STATE_DIR}/current-release" 2>/dev/null || true)
image=$(cat "${STATE_DIR}/current-image" 2>/dev/null || true)
[[ -n "${release}" && -n "${image}" ]] || exit 0          # nothing deployed yet
[[ -e "${STATE_DIR}/watch.lock" ]] && ! flock -n "${STATE_DIR}/watch.lock" true && exit 0  # deploy running

# shellcheck source=/dev/null
source /etc/learnplat/deploy.env
export APP_DOMAIN LEARNPLAT_IMAGE=${image}
compose() {
  docker compose --project-directory "${release}" -f "${release}/docker-compose.prod.yml" "$@"
}

failures_file="${STATE_DIR}/health-failures"
if compose exec -T app python /app/docker/healthcheck.py; then
  echo 0 > "${failures_file}"
  exit 0
fi

failures=$(( $(cat "${failures_file}" 2>/dev/null || echo 0) + 1 ))
echo "${failures}" > "${failures_file}"
echo "$(date -Is) /healthz failed (${failures} in a row)" >> "${LOG}"
if (( failures >= 3 )); then
  echo "$(date -Is) restarting the stack" >> "${LOG}"
  compose up -d --force-recreate
  echo 0 > "${failures_file}"
fi
