from config.settings.base import *  # noqa: F403
from config.settings.base import DATABASE_PATH
from config.settings.env import env_list

DEBUG = True
SECRET_KEY = "dev-only-insecure-key-do-not-use-in-production"  # noqa: S105
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
