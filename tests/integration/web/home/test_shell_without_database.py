"""Story 1.1 review v1 ISS-003 hand-off: error pages must render while the database is down.

The top bar and the flash messages read the session-backed user, i.e. the database. When every
query fails, the shell renders as for a signed-out visitor so the error page itself still works.
"""

import re

import pytest
from django.db import OperationalError
from django.db.backends.utils import CursorWrapper

pytestmark = pytest.mark.django_db


@pytest.fixture
def database_down(monkeypatch):
    def fail(*args, **kwargs):
        raise OperationalError("database is locked")

    monkeypatch.setattr(CursorWrapper, "execute", fail)
    monkeypatch.setattr(CursorWrapper, "executemany", fail)


@pytest.fixture
def signed_in(student_client):
    student_client.get("/ro/")  # the session exists before the outage
    student_client.raise_request_exception = False
    return student_client


def test_500_page_renders_localized_with_reference_when_every_query_fails(signed_in, database_down):
    response = signed_in.get("/ro/")
    html = response.content.decode()

    assert response.status_code == 500
    assert "Ceva nu a funcționat" in html
    assert re.search(r'class="error-card__ref">Cod de referință: [0-9a-f]{32}<', html)
    assert '<body class="theme-student"' in html
    assert "user-menu" not in html


def test_404_page_renders_with_an_anonymous_shell_when_every_query_fails(signed_in, database_down):
    response = signed_in.get("/ro/does-not-exist/")
    html = response.content.decode()

    assert response.status_code == 404
    assert 'class="error-card"' in html
    assert 'class="lang-switch"' in html
    assert "user-menu" not in html


def test_healthz_still_answers_503_when_every_query_fails(signed_in, database_down):
    assert signed_in.get("/healthz").status_code == 503
