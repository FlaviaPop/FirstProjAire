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


def test_healthz_returns_503_when_data_directory_not_writable(client, monkeypatch, caplog):
    monkeypatch.setattr("infrastructure.web.common.health.os.access", lambda *_: False)

    response = client.get("/healthz")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "db": "error"}
    assert any(
        r.levelname == "ERROR" and r.getMessage() == "healthz.data_dir_not_writable"
        for r in caplog.records
    )


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
