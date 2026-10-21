import os
import stat

import pytest
from django.db import DatabaseError
from django.test import Client

pytestmark = pytest.mark.django_db


def test_healthz_returns_ok_when_database_reachable(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}
    assert "no-store" in response["Cache-Control"]


def test_healthz_is_idempotent_and_sets_no_session_cookie(client):
    first, second = client.get("/healthz"), client.get("/healthz")

    assert first.json() == second.json()
    assert "sessionid" not in second.cookies


def test_healthz_head_returns_ok_with_empty_body(client):
    response = client.head("/healthz")

    assert response.status_code == 200
    assert response.content == b""


def test_healthz_returns_503_when_database_query_fails(client, monkeypatch, caplog):
    def broken_cursor(*args, **kwargs):
        raise DatabaseError("disk I/O error")

    monkeypatch.setattr("django.db.backends.base.base.BaseDatabaseWrapper.cursor", broken_cursor)

    response = client.get("/healthz")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "db": "error"}
    assert "disk I/O error" not in response.content.decode()
    assert any(
        r.levelname == "ERROR" and r.getMessage() == "healthz.db_unavailable"
        for r in caplog.records
    )


def test_healthz_returns_503_not_500_when_session_cookie_present_and_db_down(
    student_client, monkeypatch
):
    # BUG-002: with a session cookie, resolving request.user hits the DB before the view runs.
    assert "sessionid" in student_client.cookies

    def broken_cursor(*args, **kwargs):
        raise DatabaseError("database is locked")

    monkeypatch.setattr("django.db.backends.base.base.BaseDatabaseWrapper.cursor", broken_cursor)

    response = student_client.get("/healthz")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "db": "error"}


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores directory write permissions")
# Only the path the health check reads is overridden; the open test connection is untouched.
@pytest.mark.filterwarnings("ignore:Overriding setting DATABASES:UserWarning")
def test_healthz_reports_read_only_data_directory_as_its_own_cause(
    client, settings, monkeypatch, tmp_path, caplog
):
    # BUG-001: a real read-only directory. In WAL mode SQLite then fails the query too, so the
    # directory must be checked first, or the log blames the database.
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    data_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)
    settings.DATABASES = {
        **settings.DATABASES,
        "default": {**settings.DATABASES["default"], "NAME": data_dir / "db.sqlite3"},
    }
    queried = []

    def failing_cursor(*args, **kwargs):  # what SQLite does with a read-only WAL directory
        queried.append(True)
        raise DatabaseError("attempt to write a readonly database")

    monkeypatch.setattr("django.db.backends.base.base.BaseDatabaseWrapper.cursor", failing_cursor)

    try:
        response = client.get("/healthz")
    finally:
        data_dir.chmod(stat.S_IRWXU)

    events = [r.getMessage() for r in caplog.records if r.levelname == "ERROR"]
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "db": "error"}
    assert "healthz.data_dir_not_writable" in events
    assert "healthz.db_unavailable" not in events
    assert queried == []  # the DB is never touched once the directory is known to be read-only


def test_healthz_view_rejects_post(client):
    # The default test client skips CSRF, so this proves the view's own method guard.
    assert client.post("/healthz").status_code == 405


def test_healthz_post_is_rejected_by_csrf_before_reaching_the_view():
    # In a real request CSRF runs first, so POST gets 403 (accepted deviation from AC 9).
    response = Client(enforce_csrf_checks=True).post("/healthz")

    assert response.status_code == 403


@pytest.mark.parametrize("prefix", ["/ro", "/en"])
def test_healthz_is_not_language_prefixed(client, prefix):
    assert client.get(f"{prefix}/healthz").status_code == 404
