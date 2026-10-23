"""Playwright harness for the CYCLE-1 journeys (Story 1.10, patterns §12.5).

Runs only with `uv run pytest -m e2e`; the default run deselects the `e2e` marker (pyproject).
Each journey gets a transactional DB, the live server and a console listener that fails the test
on any Content-Security-Policy violation.
"""

import importlib
import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from django.db import connection
from playwright.sync_api import Page

PASSWORD = "pilot-pass-123"  # tests/factories/accounts.py default
# Story 1.8: audit_log is append-only via SQLite triggers. The live server needs a transactional
# DB, whose teardown flush DELETEs every table - so the triggers are dropped just before the flush
# and re-created before the next journey (same SQL as the migration, no copy to drift).
_AUDIT_TRIGGERS = importlib.import_module(
    "infrastructure.persistence.audit.migrations.0002_append_only_triggers"
)
E2E_TEMPLATES = Path(__file__).parent / "templates"
LABELS = {
    "en": {"username": "Username", "password": "Password", "sign_in": "Sign in"},
    "ro": {"username": "Nume de utilizator", "password": "Parolă", "sign_in": "Autentificare"},
}


def pytest_configure(config: pytest.Config) -> None:
    """Chromium, traces and screenshots on failure, but only when the e2e marker is selected."""
    if "e2e" not in (config.getoption("-m") or "") or "not e2e" in config.getoption("-m"):
        return
    # Playwright's sync API runs an event loop in the test thread, so Django's ORM sees an async
    # context (in the test body and in pytest-django's teardown flush). E2E sessions only.
    os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
    config.option.browser = ["chromium"]
    config.option.tracing = "retain-on-failure"
    config.option.screenshot = "only-on-failure"
    config.option.output = "test-results"


def _run(statements: tuple[str, ...]) -> None:
    with connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Live-server journeys need a real transactional DB, and the catalogue that migrations seed
    must survive each flush: pytest-django serializes the DB at creation only for tests that carry
    this marker at collection time (the fixture alone is too late)."""
    marker = pytest.mark.django_db(transaction=True, serialized_rollback=True)
    for item in items:
        if Path(__file__).parent in Path(item.path).parents:
            item.add_marker(marker)


@pytest.fixture(scope="session")
def _seeded_snapshot(django_db_setup) -> str:
    """The migration-seeded rows (catalogue) Django serialized when it created the test DB.

    Playwright's sync API drives each test from a greenlet with a running event loop, so Django's
    context-local `connections` hands the test a fresh connection object without the snapshot,
    and the serialized rollback silently restores nothing. Capture it before the browser starts."""
    snapshot = getattr(connection, "_test_serialized_contents", None)
    assert snapshot, "e2e: the test DB was not serialized (serialized_rollback marker missing?)"
    return str(snapshot)


@pytest.fixture(autouse=True)
def _e2e_environment(_seeded_snapshot, transactional_db, settings) -> Iterator[None]:
    """A fresh transactional DB per journey, plus the test-only page (config.urls untouched).

    Serialized rollback restores the data migrations seed (the K-8 catalogue) after each flush.
    Journeys run with the append-only audit triggers in place (production behaviour); they are
    dropped only for pytest-django's teardown flush, which runs after this fixture's teardown.
    """
    if not hasattr(connection, "_test_serialized_contents"):
        # A connection object without the snapshot skipped Django's restore (see _seeded_snapshot):
        # restore here, and let Django's serialized rollback do it while this object lives.
        connection._test_serialized_contents = _seeded_snapshot  # type: ignore[attr-defined]
        connection.creation.deserialize_db_from_string(_seeded_snapshot)
    _run(_AUDIT_TRIGGERS.DROP_TRIGGERS + _AUDIT_TRIGGERS.CREATE_TRIGGERS)
    settings.ROOT_URLCONF = "tests.e2e.urls"
    engine = settings.TEMPLATES[0]
    settings.TEMPLATES = [{**engine, "DIRS": [*engine.get("DIRS", []), E2E_TEMPLATES]}]
    yield
    _run(_AUDIT_TRIGGERS.DROP_TRIGGERS)


@pytest.fixture(scope="session")
def base_url(live_server) -> str:
    """Overrides pytest-playwright's session-scoped base_url with the live server."""
    return str(live_server.url)


def watch_console(page: Page) -> list[str]:
    """Collect console errors of `page` (also for extra pages opened in a test)."""
    errors: list[str] = []
    page.on(
        "console", lambda message: errors.append(message.text) if message.type == "error" else None
    )
    return errors


@pytest.fixture
def console_errors(page: Page) -> Iterator[list[str]]:
    """AC 11: any CSP violation in the browser console fails the journey."""
    errors = watch_console(page)
    yield errors
    assert_no_csp_violations(errors)


def assert_no_csp_violations(errors: list[str]) -> None:
    csp = [error for error in errors if "Content Security Policy" in error]
    assert csp == [], f"CSP violations: {csp}"


def login(
    page: Page, base_url: str, username: str, password: str = PASSWORD, lang: str = "en"
) -> None:
    labels = LABELS[lang]
    page.goto(f"{base_url}/{lang}/accounts/login/")
    page.get_by_label(labels["username"]).fill(username)
    page.get_by_label(labels["password"]).fill(password)
    page.get_by_role("button", name=labels["sign_in"]).click()


def logout(page: Page) -> None:
    """Open the account menu (unless already open: a second click closes <details>), sign out."""
    sign_out = page.get_by_role("button", name="Sign out")
    if not sign_out.is_visible():
        page.get_by_label("Account menu").click()
    sign_out.click()
