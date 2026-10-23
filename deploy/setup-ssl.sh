#!/usr/bin/env bash
# First Let's Encrypt certificate for this VM's domain, then webroot renewals that reload the
# nginx container. Run once as root after the DNS record resolves to this VM:
#   setup-ssl.sh <domain> <alert e-mail>
# Renewal: certbot's systemd timer (installed with the package) runs `certbot renew` twice a day.
set -euo pipefail

domain=${1:?usage: setup-ssl.sh <domain> <e-mail>}
email=${2:?usage: setup-ssl.sh <domain> <e-mail>}
[[ "${domain}" =~ ^[a-z0-9]([a-z0-9.-]*[a-z0-9])?\.[a-z]{2,}$ ]] || { echo "invalid domain: ${domain}" >&2; exit 1; }
[[ "${email}" == *@*.* ]] || { echo "invalid e-mail: ${email}" >&2; exit 1; }

mkdir -p /var/www/certbot
# Port 80 must be free for the standalone challenge: stop the nginx container if it runs.
if docker ps --format '{{.Names}}' | grep -qx learnplat-nginx-1; then
  docker stop learnplat-nginx-1 >/dev/null
  restart_nginx=1
fi

certbot certonly --standalone --non-interactive --agree-tos -m "${email}" -d "${domain}"

# From now on renewals use the webroot the nginx container serves, then reload nginx.
certbot reconfigure --cert-name "${domain}" --non-interactive \
  --webroot --webroot-path /var/www/certbot \
  --deploy-hook "docker exec learnplat-nginx-1 nginx -s reload"

if [[ "${restart_nginx:-0}" == 1 ]]; then
  docker start learnplat-nginx-1 >/dev/null
fi
certbot renew --dry-run
echo "setup-ssl: certificate for ${domain} issued; renewals via webroot + nginx reload"
