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
    "infrastructure.persistence.catalogue",  # Story 2.1: grade/subject catalogue (K-8)
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
}
