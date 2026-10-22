"""Inclusion tags for the shared UI primitive library (patterns §11.2).

Each tag validates its input and raises on anything outside the catalogue, so a typo in a
template fails the tests instead of shipping a blank or misleading element. All values reach
the templates unmarked, so Django's autoescaping applies to every attribute and label.
"""

import math
import re
from decimal import Decimal
from typing import Any

from django import template
from django.utils.translation import gettext_lazy as _

register = template.Library()

ICON_NAMES = frozenset(
    {
        "arrow-counter-clockwise",
        "bell",
        "book-open",
        "caret-right",
        "chalkboard-teacher",
        "chart-bar",
        "check-circle",
        "compass",
        "exam",
        "flag",
        "house",
        "list-checks",
        "lock-simple",
        "pencil-simple",
        "plugs",
        "prohibit",
        "shield-check",
        "sign-in",
        "sign-out",
        "student",
        "translate",
        "user-circle",
        "users",
        "warning-circle",
        "x-circle",
    }
)
ICON_SIZES = frozenset({20, 24, 32})
ICON_VARIANTS = frozenset({"regular", "duotone"})
BUTTON_VARIANTS = frozenset({"primary", "secondary", "danger", "link"})
BUTTON_TYPES = frozenset({"submit", "button", "reset"})
STATUS_LABELS = {
    "ACTIVE": _("Active"),
    "FLAGGED": _("Flagged"),
    "BLOCKED": _("Blocked"),
    "RESUBMITTED": _("Resubmitted"),
    "DRAFT": _("Draft"),
    "PUBLISHED": _("Published"),
}
SCORE_RANGE = range(1, 101)
# HTMX evaluates JavaScript in hx-vars, and in hx-vals / hx-headers values prefixed "js:".
HX_SCRIPT_KEYS = frozenset({"hx_vars"})
HX_JSON_KEYS = frozenset({"hx_vals", "hx_headers"})
HX_SCRIPT_PREFIXES = ("js:", "javascript:")

TagContext = dict[str, Any]


def _whole_number(value: object, what: str) -> int:
    """`value` as an int; 87.6, True or None is a caller bug, never shown as 87 (ISS-001)."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str) and re.fullmatch(r"-?\d+", value.strip()):
        return int(value)
    if isinstance(value, float | Decimal) and math.isfinite(value) and value == int(value):
        return int(value)
    raise ValueError(f"{what} must be a whole number, got {value!r}")


@register.inclusion_tag("components/icon.html")
def ui_icon(name: str, size: int = 24, variant: str = "regular", label: str = "") -> TagContext:
    """A sprite icon; decorative (hidden from screen readers) unless a label is given."""
    if name not in ICON_NAMES or int(size) not in ICON_SIZES or variant not in ICON_VARIANTS:
        raise ValueError(f"Unknown icon: {name} (size={size}, variant={variant})")
    symbol = name if variant == "regular" else f"{name}-duotone"
    return {"symbol": symbol, "size": int(size), "label": label}


def _runs_script(key: str, value: object) -> bool:
    if key.startswith("hx_on") or key in HX_SCRIPT_KEYS:
        return True
    return key in HX_JSON_KEYS and str(value).lstrip().startswith(HX_SCRIPT_PREFIXES)


def _hx_attributes(hx: dict[str, str]) -> list[tuple[str, str]]:
    """`hx_post="/x"` -> `("hx-post", "/x")`. Only HTMX attributes pass, never script."""
    bad = sorted(k for k, v in hx.items() if not k.startswith("hx_") or _runs_script(k, v))
    if bad:
        raise template.TemplateSyntaxError(
            f"ui_button accepts only non-script hx_* attributes, got {bad}"
        )
    return [(key.replace("_", "-"), value) for key, value in sorted(hx.items())]


@register.inclusion_tag("components/button.html")
def ui_button(
    label: str,
    variant: str = "primary",
    type: str = "submit",
    icon: str | None = None,
    name: str | None = None,
    value: str | None = None,
    disabled: bool = False,
    loading: bool = False,
    **hx: str,
) -> TagContext:
    """A real <button>. `loading` renders the in-flight state HTMX produces during a request."""
    if variant not in BUTTON_VARIANTS:
        raise template.TemplateSyntaxError(f"Unknown button variant: {variant}")
    if type not in BUTTON_TYPES:
        raise template.TemplateSyntaxError(f"Unknown button type: {type}")
    return {
        "label": label,
        "variant": variant,
        "type": type,
        "icon": icon,
        "name": name,
        "value": value,
        "disabled": bool(disabled or loading),
        "loading": bool(loading),
        "attrs": _hx_attributes(hx),
    }


@register.inclusion_tag("components/badge.html")
def ui_badge(value: int, label: str) -> TagContext:
    """A count badge; zero renders nothing, the label gives screen readers the full meaning."""
    count = _whole_number(value, "Badge value")
    if count < 0:
        raise ValueError(f"Badge value must be >= 0, got {value}")
    return {"value": count, "label": label}


@register.inclusion_tag("components/status_pill.html")
def ui_status_pill(status: str) -> TagContext:
    """Colour + translated word, never colour alone."""
    if status not in STATUS_LABELS:
        raise ValueError(f"Unknown status: {status}")
    return {"status": status.lower(), "label": STATUS_LABELS[status]}


@register.inclusion_tag("components/avatar.html")
def ui_avatar(user: object = None) -> TagContext:
    """The generic user icon (no photo uploads), named after the user for screen readers."""
    get_full_name = getattr(user, "get_full_name", None)
    full_name = str(get_full_name()).strip() if callable(get_full_name) else ""
    return {"label": full_name or _("User")}


@register.inclusion_tag("components/score.html")
def ui_score(value: int) -> TagContext:
    """A final score shown as "N / 100"."""
    score = _whole_number(value, "Score")
    if score not in SCORE_RANGE:
        raise ValueError(f"Score must be 1-100, got {value}")
    return {"value": score}


@register.inclusion_tag("components/progress_meter.html")
def ui_progress(done: int, total: int, label: str) -> TagContext:
    """A labelled <progress> plus "done/total" text; total 0 shows 0/0 without dividing."""
    done, total = _whole_number(done, "Progress done"), _whole_number(total, "Progress total")
    if done < 0 or total < 0 or done > total:
        raise ValueError(f"Invalid progress {done}/{total}")
    return {"done": done, "total": total, "max": total or 1, "label": label}


# Story 1.6 molecules register on `register` from ui_molecules.py (module-size limit). Imported
# last because that module imports the catalogues above; `Cell` is resolved lazily so either
# module can be imported first.
from infrastructure.web.templatetags import ui_molecules  # noqa: E402


def __getattr__(name: str) -> Any:
    if name == "Cell":
        return ui_molecules.Cell
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
