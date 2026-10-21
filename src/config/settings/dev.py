from config.settings.base import *  # noqa: F403
from config.settings.base import DATABASE_PATH, LOGGING
from config.settings.env import env_list, env_str

DEBUG = True
SECRET_KEY = "dev-only-insecure-key-do-not-use-in-production"  # noqa: S105
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

# Patterns §10: LOG_LEVEL defaults to DEBUG in dev (INFO elsewhere); the environment still wins.
# The "django" logger stays at INFO from base.py: its DEBUG output includes SQL parameters.
LOG_LEVEL = env_str("LOG_LEVEL", "DEBUG")
LOGGING["handlers"]["stdout"]["level"] = LOG_LEVEL
LOGGING["root"]["level"] = LOG_LEVEL
