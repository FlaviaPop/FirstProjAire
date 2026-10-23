#!/bin/sh
# Container start (architecture "Deployment View"): migrations run once, before Gunicorn accepts
# traffic; static files are copied to the volume Nginx serves from. Then the CMD is exec'd.
set -eu

python /app/manage.py migrate --noinput
# Nginx serves /static/ from this shared volume; refreshed on every start so it matches the image.
cp -a /app/staticfiles/. /srv/static/

exec "$@"
