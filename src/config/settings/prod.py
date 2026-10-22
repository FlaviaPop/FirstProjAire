from django.core.exceptions import ImproperlyConfigured

from config.settings.base import *  # noqa: F403
from config.settings.env import env_list, env_str

DEBUG = False
SECRET_KEY = env_str("DJANGO_SECRET_KEY")  # required, no default
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    # A set-but-empty value would otherwise answer every request with 400 and no start-up error.
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must list at least one host")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31_536_000
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
LANGUAGE_COOKIE_SECURE = SESSION_COOKIE_SECURE  # Story 1.4: follows the session cookie
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
