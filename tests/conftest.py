"""Global pytest fixtures shared by every test package.

Role-specific users and logged-in clients are added here by the stories that introduce
login and RBAC (1.2, 1.3), so every context's tests use the same fixtures. Markers are
declared in pyproject.toml ([tool.pytest.ini_options] markers, enforced by --strict-markers).
"""

# --- Story 1.2: role users and logged-in clients (patterns §12.3) ---
from pathlib import Path

import pytest
from django.utils import translation

from tests.factories.accounts import (
    AdminFactory,
    ParentChildLinkFactory,
    ParentFactory,
    StudentFactory,
    TeacherFactory,
)


@pytest.fixture
def student(db):
    return StudentFactory(username="student1")


@pytest.fixture
def other_student(db):
    return StudentFactory(username="student2")


@pytest.fixture
def teacher(db):
    return TeacherFactory(username="teacher1")


@pytest.fixture
def parent(db):
    return ParentFactory(username="parent1")  # unlinked; `linked_parent` links it to `student`


@pytest.fixture
def admin_user(db):
    return AdminFactory(username="admin1")


# --- Story 1.9: parent-child links (CYCLE-3 scoping tests use these) ---
@pytest.fixture
def linked_parent(parent, student):
    """`parent` linked to `student`; returns the parent."""
    ParentChildLinkFactory(parent=parent, student=student)
    return parent


@pytest.fixture
def unlinked_parent(db):
    """A second Parent/Guardian with no linked children."""
    return ParentFactory(username="parent2")


def _logged_in(client, user):
    # force_login: Client.login() can't pass `request`, which AxesStandaloneBackend requires.
    client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
    return client


@pytest.fixture
def student_client(client, student):
    return _logged_in(client, student)


@pytest.fixture
def teacher_client(client, teacher):
    return _logged_in(client, teacher)


@pytest.fixture
def parent_client(client, parent):
    return _logged_in(client, parent)


@pytest.fixture
def admin_client(client, admin_user):  # overrides pytest-django's builtin admin_client
    return _logged_in(client, admin_user)


# --- Isolation: no test may leak its active language into the next one ---------------------
@pytest.fixture(autouse=True)
def _reset_active_language():
    """Deactivate any language a test (or a request it made) left active on this thread.

    Without LocaleMiddleware, `i18n_patterns` only resolves the *active* language's prefix, so
    a leaked "en" made later `/ro/...` requests 404 depending on test order (found with BUG-003).
    """
    yield
    translation.deactivate()


# --- Story 1.4: tests that need real (compiled) translations -------------------------------
LOCALE_DIR = Path(__file__).resolve().parents[1] / "src/infrastructure/i18n/locale"


@pytest.fixture
def compiled_catalogues():
    """Fail with an actionable message when the .mo files (build artefacts) are missing."""
    missing = [
        lang for lang in ("ro", "en") if not (LOCALE_DIR / lang / "LC_MESSAGES/django.mo").exists()
    ]
    if missing:
        pytest.fail(
            f"Compiled catalogues missing for {missing}: run "
            "`uv run python manage.py compilemessages --ignore=.venv` "
            "(needs GNU gettext; see README)",
            pytrace=False,
        )
