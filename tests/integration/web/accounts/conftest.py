"""Fixtures for the login/logout tests (Story 1.2)."""

import pytest

LOCALE_MIDDLEWARE = "django.middleware.locale.LocaleMiddleware"
SESSION_MIDDLEWARE = "django.contrib.sessions.middleware.SessionMiddleware"


@pytest.fixture(autouse=True)
def language_prefixes_resolve(settings):
    """Activate the URL's language so `/en/...` resolves.

    Story 1.4 (same wave, separate run) owns `LocaleMiddleware` and places it right after
    `SessionMiddleware`. Until that merge, these tests insert it at the same position.
    Once 1.4 is merged, this fixture does nothing.
    """
    if LOCALE_MIDDLEWARE not in settings.MIDDLEWARE:
        middleware = list(settings.MIDDLEWARE)
        middleware.insert(middleware.index(SESSION_MIDDLEWARE) + 1, LOCALE_MIDDLEWARE)
        settings.MIDDLEWARE = middleware
