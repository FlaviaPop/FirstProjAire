"""Inclusion tags for the shared UI primitive library (patterns §11.2).

Each tag validates its input and raises on anything outside the catalogue, so a typo in a
template fails the tests instead of shipping a blank or misleading element. All values reach
the templates unmarked, so Django's autoescaping applies to every attribute and label.
"""

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

TagContext = dict[str, Any]


@register.inclusion_tag("components/icon.html")
def ui_icon(name: str, size: int = 24, variant: str = "regular", label: str = "") -> TagContext:
    """A sprite icon; decorative (hidden from screen readers) unless a label is given."""
    if name not in ICON_NAMES or int(size) not in ICON_SIZES or variant not in ICON_VARIANTS:
        raise ValueError(f"Unknown icon: {name} (size={size}, variant={variant})")
    symbol = name if variant == "regular" else f"{name}-duotone"
    return {"symbol": symbol, "size": int(size), "label": label}


def _hx_attributes(hx: dict[str, str]) -> list[tuple[str, str]]:
    """`hx_post="/x"` -> `("hx-post", "/x")`. Only HTMX attributes pass, never inline handlers."""
    if bad := sorted(key for key in hx if not key.startswith("hx_") or key.startswith("hx_on")):
        raise template.TemplateSyntaxError(f"ui_button accepts only hx_* attributes, got {bad}")
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
    if int(value) < 0:
        raise ValueError(f"Badge value must be >= 0, got {value}")
    return {"value": int(value), "label": label}


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
    if int(value) not in SCORE_RANGE:
        raise ValueError(f"Score must be 1-100, got {value}")
    return {"value": int(value)}


@register.inclusion_tag("components/progress_meter.html")
def ui_progress(done: int, total: int, label: str) -> TagContext:
    """A labelled <progress> plus "done/total" text; total 0 shows 0/0 without dividing."""
    done, total = int(done), int(total)
    if done < 0 or total < 0 or done > total:
        raise ValueError(f"Invalid progress {done}/{total}")
    return {"done": done, "total": total, "max": total or 1, "label": label}
