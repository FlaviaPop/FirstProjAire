from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

from config.settings.env import env_list, env_path, env_str


def test_env_str_raises_naming_the_missing_required_variable(monkeypatch):
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)

    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY"):
        env_str("DJANGO_SECRET_KEY")


def test_env_str_returns_default_when_unset(monkeypatch):
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    assert env_str("LOG_LEVEL", "INFO") == "INFO"


def test_env_str_prefers_environment_over_default(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    assert env_str("LOG_LEVEL", "INFO") == "DEBUG"


def test_env_list_splits_and_strips_empty_items(monkeypatch):
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", " a.ro, ,b.ro ")

    assert env_list("DJANGO_ALLOWED_HOSTS") == ["a.ro", "b.ro"]


def test_env_list_is_empty_when_unset_without_default(monkeypatch):
    monkeypatch.delenv("DJANGO_CSRF_TRUSTED_ORIGINS", raising=False)

    assert env_list("DJANGO_CSRF_TRUSTED_ORIGINS") == []


def test_env_path_prefers_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", "/data/db.sqlite3")

    assert env_path("DATABASE_PATH", Path("x")) == Path("/data/db.sqlite3")


def test_env_path_falls_back_to_default(monkeypatch):
    monkeypatch.delenv("DATABASE_PATH", raising=False)

    assert env_path("DATABASE_PATH", Path("data/db.sqlite3")) == Path("data/db.sqlite3")
