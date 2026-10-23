# syntax=docker/dockerfile:1.7
# Learning platform image (DevOps pipeline, discovery 2026-10-23): one Gunicorn process tree,
# SQLite on the /data volume, static files collected for Nginx. Also carries the deploy bundle
# (compose, nginx, scripts) so the VM deploys exactly what was built with this image.

ARG PYTHON_VERSION=3.12

# --- build: dependencies, compiled translations, collected static files -----------------------
FROM python:${PYTHON_VERSION}-slim-bookworm AS build
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /usr/local/bin/uv
# GNU gettext only for compilemessages; the .mo files are build artefacts (README, Story 1.4).
RUN apt-get update \
 && apt-get install -y --no-install-recommends gettext \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY manage.py ./
COPY src ./src
RUN uv run --no-sync python manage.py compilemessages --ignore=.venv \
 && DJANGO_SETTINGS_MODULE=config.settings.prod \
    DJANGO_SECRET_KEY=collectstatic-only \
    DJANGO_ALLOWED_HOSTS=localhost \
    uv run --no-sync python manage.py collectstatic --noinput

# --- runtime: slim, non-root, no build tools ---------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime
LABEL org.opencontainers.image.source="https://github.com/FlaviaPop/FirstProjAire" \
      org.opencontainers.image.title="learnplat"
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --home-dir /app --shell /usr/sbin/nologin app \
 && mkdir -p /data /srv/static \
 && chown app:app /data /srv/static
WORKDIR /app
COPY --from=build --chown=app:app /app /app
COPY --chown=root:root --chmod=0755 docker/entrypoint.sh docker/healthcheck.py /app/docker/
# Deploy bundle, extracted on the VM by learnplat-watch (pull-based deploys).
COPY --chown=root:root docker-compose.prod.yml Makefile /opt/learnplat/deploy/
COPY --chown=root:root nginx /opt/learnplat/deploy/nginx
COPY --chown=root:root --chmod=0755 deploy/*.sh /opt/learnplat/deploy/
ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod \
    DATABASE_PATH=/data/db.sqlite3
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD ["python", "/app/docker/healthcheck.py"]
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", \
     "--access-logfile", "-", "--forwarded-allow-ips", "*"]
