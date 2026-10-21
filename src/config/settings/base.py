"""Settings shared by every environment. Environment-specific values live in dev/test/prod."""

from pathlib import Path

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
]

MIDDLEWARE = [
    "infrastructure.web.common.middleware.RequestIdMiddleware",  # first: request id for all logs
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "infrastructure.web.common.middleware.DomainErrorMiddleware",  # DomainError → 404/422/409/400
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
LOGGING = {
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
