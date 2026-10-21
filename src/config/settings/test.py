from config.settings.base import *  # noqa: F403
from config.settings.base import BASE_DIR, DATABASES

DEBUG = False
SECRET_KEY = "test-only-secret-key"  # noqa: S105
ALLOWED_HOSTS = ["testserver", "localhost"]

# Speed only, never outside tests; Argon2 is configured for real settings in Story 1.2.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# A file-based test DB (not SQLite's in-memory default) so WAL mode is exercised as in prod.
DATABASE_PATH = BASE_DIR / "data" / "test.sqlite3"
DATABASES["default"]["NAME"] = DATABASE_PATH
DATABASES["default"]["TEST"] = {"NAME": DATABASE_PATH}
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
