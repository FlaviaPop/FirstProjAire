"""The only place environment variables are read (patterns §10)."""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

_MISSING = object()


def env_str(name: str, default: object = _MISSING) -> str:
    value = os.environ.get(name)
    if value is None:
        if default is _MISSING:
            raise ImproperlyConfigured(f"Required environment variable {name} is not set")
        return str(default)
    return value


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in env_str(name, default).split(",") if item.strip()]


_BOOLEANS = {"true": True, "1": True, "false": False, "0": False}


def env_bool(name: str, *, default: bool) -> bool:
    """An on/off switch; anything but true/false/1/0 is a start-up error, never a silent guess."""
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return _BOOLEANS[value.strip().lower()]
    except KeyError:
        raise ImproperlyConfigured(f"{name} must be true or false, got {value!r}") from None


def env_path(name: str, default: Path) -> Path:
    return Path(env_str(name, str(default)))
