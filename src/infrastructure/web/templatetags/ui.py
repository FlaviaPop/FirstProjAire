"""Inclusion tags for the shared UI primitive library (patterns §11.2).

Each tag validates its input and raises on anything outside the catalogue, so a typo in a
template fails the tests instead of shipping a blank or misleading element. All values reach
the templates unmarked, so Django's autoescaping applies to every attribute and label.
"""

import math
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django import template
from django.forms import BoundField
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


# --- Molecules (Story 1.6) ---------------------------------------------------------------------

ALERT_LEVELS = {
    "info": "bell",
    "success": "check-circle",
    "warning": "warning-circle",
    "error": "warning-circle",
}
SCRIPT_SCHEMES = ("javascript:", "data:", "vbscript:")
DIALOG_ID = re.compile(r"[A-Za-z][\w-]*")
# "Title (RO)", "Title [ro]", "Title RO", "Title - Română" -> "Title"; "Intro" stays "Intro".
LANGUAGE_SUFFIX = re.compile(r"(?:\s*[-(\[]\s*|\s+)(?:ro|română|romanian)[)\]]?\s*$", re.I)
Rows = Iterable[Iterable[object]]


@dataclass(frozen=True)
class Cell:
    """A table cell: escaped text, optionally a link or a status pill (never raw HTML)."""

    text: str
    href: str | None = None
    pill: str | None = None  # a status for ui_status_pill


def _href(url: object, what: str) -> str:
    """A link target; script-running schemes are a caller bug (autoescape does not stop them)."""
    value = str(url)
    if re.sub(r"[\s\x00-\x1f]", "", value).lower().startswith(SCRIPT_SCHEMES):
        raise ValueError(f"{what} must not use a script URL, got {value!r}")
    return value


def _field_context(field: object, help: str = "", legend: str = "", lang: str = "") -> TagContext:
    if not isinstance(field, BoundField):
        raise ValueError(f"Expected a form field, got {field!r}")
    widget_id = field.id_for_label
    described = [f"{widget_id}_help"] if help else []
    attrs: dict[str, str | bool] = {"lang": lang} if lang else {}
    if field.errors:
        described.append(f"{widget_id}_error")
        attrs["aria-invalid"] = "true"
    if described:
        attrs["aria-describedby"] = " ".join(described)
    label = legend or field.label
    widget = field.as_widget(attrs=attrs)
    return {"field": field, "widget": widget, "help": help, "id": widget_id, "label": label}


@register.inclusion_tag("components/form_field.html")
def ui_field(field: BoundField, help: str = "") -> TagContext:
    """Label + Django widget + help + first error, wired with aria-describedby/aria-invalid."""
    return _field_context(field, help)


@register.inclusion_tag("components/field_pair.html")
def ui_field_pair(field_ro: BoundField, field_en: BoundField) -> TagContext:
    """RO|EN side-by-side editor: one legend, one column (and error) per language."""
    label = str(_field_context(field_ro)["label"])
    legend = LANGUAGE_SUFFIX.sub("", label).strip() or label
    pairs = ((field_ro, "ro"), (field_en, "en"))
    columns = [(lang, _field_context(field, "", legend, lang)) for field, lang in pairs]
    return {"legend": legend, "columns": columns}


@register.inclusion_tag("components/alert.html")
def ui_alert(level: str, message: str, dismissible: bool = True) -> TagContext:
    """An inline banner; errors/warnings interrupt (role=alert), the rest are polite."""
    if level not in ALERT_LEVELS:
        raise ValueError(f"Unknown alert level: {level}")
    return {
        "level": level,
        "icon": ALERT_LEVELS[level],
        "message": message,
        "dismissible": bool(dismissible),
        "role": "alert" if level in {"error", "warning"} else "status",
    }


@register.inclusion_tag("components/card.html")
def ui_card(
    title: str, body: str = "", href: str | None = None, icon: str | None = None, meta: str = ""
) -> TagContext:
    """A card; with `href` the title is its only link (CSS stretches it over the card).

    Icon names are validated by ui_icon when the card renders."""
    return {
        "title": title,
        "body": body,
        "href": _href(href, "Card href") if href else None,
        "icon": icon,
        "meta": meta,
    }


@register.inclusion_tag("components/disabled_tile.html")
def ui_disabled_tile(title: str, reason: str = "") -> TagContext:
    """A locked tile: no link, no tab stop, a visible "Unavailable" label."""
    return {"title": title, "reason": reason}


def _icon_variant(context: template.Context) -> str:
    variant = context.get("icon_variant") or "regular"
    if variant not in ICON_VARIANTS:
        raise ValueError(f"Unknown icon variant: {variant}")
    return str(variant)


@register.inclusion_tag("components/empty_state.html", takes_context=True)
def ui_empty_state(
    context: template.Context,
    message: str,
    action_label: str = "",
    action_url: str = "",
    icon: str = "list-checks",
) -> TagContext:
    """An empty list: icon (theme variant from `icon_variant`), message, optional action link."""
    show_action = bool(action_label) and bool(action_url)
    return {
        "message": message,
        "action_label": action_label,
        "action_url": _href(action_url, "Empty-state action") if show_action else "",
        "icon": icon,
        "icon_variant": _icon_variant(context),
    }


def _button_variant(variant: str) -> str:
    if variant not in BUTTON_VARIANTS:
        raise template.TemplateSyntaxError(f"Unknown button variant: {variant}")
    return variant


def _pairs(items: Rows, size: int, what: str) -> list[tuple[Any, ...]]:
    result = [tuple(item) for item in items]
    if any(len(item) != size for item in result):
        raise ValueError(f"Each {what} must have {size} values")
    return result


@register.inclusion_tag("components/page_header.html")
def ui_page_header(title: str, breadcrumbs: Rows = (), actions: Rows = ()) -> TagContext:
    """<h1> + breadcrumb trail (last item is the current page) + action links."""
    crumbs = [
        (label, _href(url, "Breadcrumb url") if url else "")
        for label, url in _pairs(breadcrumbs, 2, "breadcrumb")
    ]
    links = [
        (label, _href(url, "Action url"), _button_variant(variant))
        for label, url, variant in _pairs(actions, 3, "action")
    ]
    return {"title": title, "breadcrumbs": crumbs, "actions": links}


def _dialog_id(dialog_id: object) -> str:
    if not isinstance(dialog_id, str) or not DIALOG_ID.fullmatch(dialog_id):
        raise ValueError(f"Invalid dialog id: {dialog_id!r}")
    return dialog_id


@register.inclusion_tag("components/confirm_dialog.html")
def ui_confirm_dialog(
    dialog_id: str,
    title: str,
    body: str,
    confirm_label: str,
    action: str,
    confirm_variant: str = "primary",
    hidden: Mapping[str, object] | Rows | None = None,
    extra_template: str | None = None,
) -> TagContext:
    """A native <dialog> holding its own CSRF form; the receiving view enforces permissions."""
    pairs = hidden.items() if isinstance(hidden, Mapping) else (hidden or ())
    return {
        "dialog_id": _dialog_id(dialog_id),
        "title": title,
        "body": body,
        "confirm_label": confirm_label,
        "action": _href(action, "Dialog action"),
        "confirm_variant": _button_variant(confirm_variant),
        "hidden": _pairs(pairs, 2, "hidden field"),
        "extra_template": extra_template,
    }


@register.inclusion_tag("components/dialog_trigger.html")
def ui_dialog_trigger(dialog_id: str, label: str, variant: str = "primary") -> TagContext:
    """The button that opens a confirm dialog (ui.js), with a no-JavaScript note."""
    return {"dialog_id": _dialog_id(dialog_id), "label": label, "variant": _button_variant(variant)}


def _cell(cell: object) -> Cell:
    if isinstance(cell, bool) or not isinstance(cell, str | int | Cell):
        raise ValueError(f"Unsupported cell: {type(cell).__name__}")
    if not isinstance(cell, Cell):
        return Cell(str(cell))
    if cell.href is not None and cell.pill is not None:
        raise ValueError("Unsupported cell: a Cell is either a link or a pill, not both")
    if cell.pill is not None and cell.pill not in STATUS_LABELS:
        raise ValueError(f"Unknown status: {cell.pill}")
    href = _href(cell.href, "Cell href") if cell.href is not None else None
    return Cell(str(cell.text), href, cell.pill)


@register.inclusion_tag("components/table.html", takes_context=True)
def ui_table(
    context: template.Context, columns: Iterable[str], rows: Rows, caption: str, empty_message: str
) -> TagContext:
    """A captioned table of escaped cells; no rows renders the empty state, never a <table>."""
    headers = list(columns)
    body = [[_cell(cell) for cell in row] for row in rows]
    if any(len(row) != len(headers) for row in body):
        raise ValueError(f"Each row must have {len(headers)} cells")
    return {
        "columns": headers,
        "rows": body,
        "caption": caption,
        "empty_message": empty_message,
        "icon_variant": _icon_variant(context),
    }
