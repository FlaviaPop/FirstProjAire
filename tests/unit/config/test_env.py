from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

from config.settings.env import env_bool, env_list, env_path, env_str


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


# Story 1.1 review v1 ISS-004 / Story 1.0 review v1 ISS-004: on/off switches from the environment.
@pytest.mark.parametrize("raw", ["true", "True", "1", " TRUE "])
def test_env_bool_reads_true(monkeypatch, raw):
    monkeypatch.setenv("DJANGO_HSTS_PRELOAD", raw)

    assert env_bool("DJANGO_HSTS_PRELOAD", default=False) is True


@pytest.mark.parametrize("raw", ["false", "False", "0", " FALSE "])
def test_env_bool_reads_false(monkeypatch, raw):
    monkeypatch.setenv("DJANGO_HSTS_PRELOAD", raw)

    assert env_bool("DJANGO_HSTS_PRELOAD", default=True) is False


@pytest.mark.parametrize("default", [True, False])
def test_env_bool_returns_default_when_unset(monkeypatch, default):
    monkeypatch.delenv("DJANGO_HSTS_PRELOAD", raising=False)

    assert env_bool("DJANGO_HSTS_PRELOAD", default=default) is default


@pytest.mark.parametrize("raw", ["yes", "on", "", "2", "truthy"])
def test_env_bool_rejects_anything_else_naming_the_variable(monkeypatch, raw):
    monkeypatch.setenv("DJANGO_HSTS_PRELOAD", raw)

    with pytest.raises(ImproperlyConfigured, match="DJANGO_HSTS_PRELOAD"):
        env_bool("DJANGO_HSTS_PRELOAD", default=False)
