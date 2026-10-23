#!/usr/bin/env bash
# learnplat-watch (systemd timer, every minute): pull-based deploys.
# GitHub Actions moves the image tag for this environment (`staging` or `prod`) in GHCR; when its
# digest differs from what runs here, extract the deploy bundle from that image and run it.
#   learnplat-watch              follow the tag (timer)
# A digest in /var/lib/learnplat/pinned-image (make rollback) wins over the tag until removed
# (make unpin). A digest that failed its health check is not retried until the tag moves on.
set -euo pipefail

# shellcheck source=/dev/null
source /etc/learnplat/deploy.env   # LEARNPLAT_ENV, IMAGE_REPO, APP_DOMAIN
STATE_DIR=/var/lib/learnplat
exec 9>"${STATE_DIR}/watch.lock"
flock -n 9 || exit 0               # a deploy is already running

pinned=$(cat "${STATE_DIR}/pinned-image" 2>/dev/null || true)
if [[ -n "${pinned}" ]]; then
  docker pull --quiet "${pinned}" >/dev/null
  wanted=${pinned}
else
  docker pull --quiet "${IMAGE_REPO}:${LEARNPLAT_ENV}" >/dev/null
  wanted=$(docker image inspect --format '{{index .RepoDigests 0}}' "${IMAGE_REPO}:${LEARNPLAT_ENV}")
fi
current=$(cat "${STATE_DIR}/current-image" 2>/dev/null || true)
failed=$(cat "${STATE_DIR}/failed-image" 2>/dev/null || true)
[[ "${wanted}" == "${current}" ]] && exit 0
[[ "${wanted}" == "${failed}" && -z "${pinned}" ]] && exit 0   # wait for a new tag

release="${STATE_DIR}/releases/${wanted##*:}"
mkdir -p "${release}"
container=$(docker create "${wanted}")
trap 'docker rm "${container}" >/dev/null' EXIT
docker cp "${container}:/opt/learnplat/deploy/." "${release}/"
echo "learnplat-watch: deploying ${wanted} from ${release}"
"${release}/deploy.sh" "${wanted}" "${release}"
