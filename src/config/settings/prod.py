from django.core.exceptions import ImproperlyConfigured

from config.settings.base import *  # noqa: F403
from config.settings.env import env_bool, env_list, env_str

DEBUG = False
SECRET_KEY = env_str("DJANGO_SECRET_KEY")  # required, no default
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    # A set-but-empty value would otherwise answer every request with 400 and no start-up error.
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must list at least one host")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31_536_000
# Story 1.0 review v1 ISS-004 (owner decision 2026-10-23): includeSubDomains and preload stay off
# until the production domain is final (preload is hard to undo). While a flag is off, its deploy
# warning is silenced on purpose so `check --deploy` stays clean; switching it on unsilences it.
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_HSTS_INCLUDE_SUBDOMAINS", default=False)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_HSTS_PRELOAD", default=False)
SILENCED_SYSTEM_CHECKS = [
    *(["security.W005"] if not SECURE_HSTS_INCLUDE_SUBDOMAINS else []),
    *(["security.W021"] if not SECURE_HSTS_PRELOAD else []),
]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
LANGUAGE_COOKIE_SECURE = SESSION_COOKIE_SECURE  # Story 1.4: follows the session cookie
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# Nginx sets X-Request-ID on every proxied request (nginx/conf.d/proxy_headers.inc), so the
# id the app receives is the proxy's, never the client's (Story 1.1 review v1 ISS-004).
TRUST_INCOMING_REQUEST_ID = env_bool("DJANGO_TRUST_INCOMING_REQUEST_ID", default=True)
