"""Settings shared by every environment. Environment-specific values live in dev/test/prod."""

from datetime import timedelta
from pathlib import Path
from typing import Any

from csp.constants import NONE, SELF

from config.settings.env import env_path, env_str

BASE_DIR = Path(__file__).resolve().parents[3]  # repository root

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "infrastructure.web",  # registers the shared templatetags package ({% load ui %})
    "infrastructure.persistence.accounts",
    "infrastructure.persistence.catalogue",  # Story 2.1: grade/subject catalogue (K-8)
    "infrastructure.persistence.audit",  # Story 1.8: append-only audit log + auth receivers
]

MIDDLEWARE = [
    "infrastructure.web.common.middleware.RequestIdMiddleware",  # first: request id for all logs
    "django.middleware.security.SecurityMiddleware",
    "csp.middleware.CSPMiddleware",  # Story 1.2
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "infrastructure.web.common.middleware.DomainErrorMiddleware",  # DomainError → 404/422/409/400
    "axes.middleware.AxesMiddleware",  # Story 1.2: must stay last
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "src/infrastructure/web/templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASE_PATH = env_path("DATABASE_PATH", default=BASE_DIR / "data" / "db.sqlite3")

# ADR-004: single-instance SQLite; IMMEDIATE takes the write lock at BEGIN to avoid
# lock-upgrade deadlocks, WAL lets readers run alongside the single writer.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATABASE_PATH,
        "ATOMIC_REQUESTS": False,  # transactions are owned by use cases (UnitOfWork)
        "OPTIONS": {
            "transaction_mode": "IMMEDIATE",
            "timeout": 20,
            "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;",
        },
    }
}

AUTH_USER_MODEL = "accounts.UserModel"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "ro"
LANGUAGES = [("ro", "Română"), ("en", "English")]
LOCALE_PATHS = [BASE_DIR / "src/infrastructure/i18n/locale"]
USE_I18N = True
USE_TZ = True
TIME_ZONE = "Europe/Bucharest"

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "src/infrastructure/web/static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

LOG_LEVEL = env_str("LOG_LEVEL", "INFO")
# Story 1.1: JSON lines on stdout with request_id/user_id/role on every record (patterns §9).
LOGGING: dict[str, Any] = {  # dictConfig; dev.py adjusts the levels in place
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_context": {"()": "infrastructure.logging.request_context.RequestContextFilter"}
    },
    "formatters": {"json": {"()": "infrastructure.logging.json_formatter.JsonFormatter"}},
    "handlers": {
        "stdout": {
            "class": "infrastructure.logging.stdout_handler.StdoutHandler",
            "formatter": "json",
            "filters": ["request_context"],
            "level": LOG_LEVEL,  # also caps loggers that propagate with their own level
        },
        "null": {"class": "logging.NullHandler"},
    },
    "loggers": {
        # Drop Django's plain-text console handler so django.* records go to the JSON
        # handler only. INFO stays fixed: DEBUG would emit SQL with parameters (personal data).
        "django": {"handlers": [], "level": "INFO", "propagate": True},
        # runserver's access line contains the query string; request.completed replaces it.
        "django.server": {"handlers": ["null"], "propagate": False},
    },
    "root": {"handlers": ["stdout"], "level": LOG_LEVEL},
}

# --- Story 1.2: authentication, brute-force protection, sessions, security headers ---
# Fixed product policy (patterns §10): constants here, not env vars. Only the proxy count
# depends on the deployment.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",  # Argon2id (architecture: Security Design)
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",  # fallbacks: older hashes upgrade on login
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

INSTALLED_APPS += ["axes", "csp"]
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",  # first: refuses locked-out username+IP pairs
    "django.contrib.auth.backends.ModelBackend",
]
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]  # architecture: "per username+IP"
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_TEMPLATE = "accounts/locked_out.html"
AXES_HTTP_RESPONSE_CODE = 429
# Story 1.2 table: an attempt during the cool-off has no side effect, so it must not
# restart the 15 minutes (axes' default would).
AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = False
AXES_IPWARE_PROXY_COUNT = int(env_str("AXES_PROXY_COUNT", "0"))
# Wave-2 integration: axes logs an INFO banner on every start. With Story 1.1's JSON logs on
# stdout, that line polluted every management command's output (shell -c, scripts).
AXES_VERBOSE = False

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 8 * 60 * 60
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True  # HTMX reads the token from the page, not the cookie (Story 1.7)
# BUG-003: CSRF failures use Story 1.1's localized 403 page instead of Django's default.
CSRF_FAILURE_VIEW = "infrastructure.web.common.errors.csrf_failure"

LOGIN_URL = "accounts:login"
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": [SELF],
        "script-src": [SELF],
        "style-src": [SELF],
        "img-src": [SELF, "data:"],
        "font-src": [SELF],
        "form-action": [SELF],
        "frame-ancestors": [NONE],
        "base-uri": [SELF],
    }
}
