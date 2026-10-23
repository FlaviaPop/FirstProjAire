#!/usr/bin/env bash
# Encrypt and mount the SQLite data volume at /data (architecture: "encrypted volume";
# deploy plan decision 2026-10-23: LUKS2). Idempotent: safe on every boot and on re-runs.
#   data-volume.sh /dev/disk/by-id/scsi-0HC_Volume_<id>
# The key file lives only on this VM's boot disk (root-only). Copy it to the password manager
# right after the first boot (runbook-deploy.md); without it a detached volume is unreadable.
set -euo pipefail

device=${1:?usage: data-volume.sh <volume device>}
key=/etc/learnplat/data.key
mapper=learnplat-data

for _ in $(seq 1 60); do [[ -e "${device}" ]] && break; sleep 2; done   # attached after boot
[[ -e "${device}" ]] || { echo "data-volume: ${device} never appeared" >&2; exit 1; }

if [[ ! -f "${key}" ]]; then
  install -d -m 0700 /etc/learnplat
  head -c 64 /dev/urandom > "${key}"
  chmod 0400 "${key}"
fi

if ! cryptsetup isLuks "${device}"; then
  cryptsetup luksFormat --type luks2 --batch-mode --key-file "${key}" "${device}"
fi

[[ -e "/dev/mapper/${mapper}" ]] || cryptsetup open --key-file "${key}" "${device}" "${mapper}"

if ! blkid "/dev/mapper/${mapper}" >/dev/null 2>&1; then
  mkfs.ext4 -q -L learnplat-data "/dev/mapper/${mapper}"
fi

uuid=$(cryptsetup luksUUID "${device}")
grep -q "^${mapper} " /etc/crypttab \
  || echo "${mapper} UUID=${uuid} ${key} luks,discard,nofail" >> /etc/crypttab
grep -q "^/dev/mapper/${mapper} " /etc/fstab \
  || echo "/dev/mapper/${mapper} /data ext4 defaults,discard,nofail 0 2" >> /etc/fstab

mkdir -p /data
mountpoint -q /data || mount /data
mkdir -p /data/backups
chown -R 10001:10001 /data   # the app container's user
echo "data-volume: /data is the LUKS2 volume ${device} (${mapper})"
