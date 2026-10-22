"""Story 1.6 molecule tags (form field, RO|EN pair, alert, card, tiles, header, dialog, table).

They live apart from the atoms only to keep each module under the 400-line limit; they register
on the same `ui` library, so templates keep using `{% load ui %}`.
"""

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from django import forms, template
from django.forms import BoundField

from infrastructure.web.templatetags.ui import (
    BUTTON_VARIANTS,
    ICON_VARIANTS,
    STATUS_LABELS,
    TagContext,
    _whole_number,
    register,
)

ALERT_LEVELS = {
    "info": "bell",
    "success": "check-circle",
    "warning": "warning-circle",
    "error": "warning-circle",
}
SCRIPT_SCHEMES = ("javascript:", "data:", "vbscript:")
DIALOG_ID = re.compile(r"[A-Za-z][\w-]*")
# "Title (RO)", "Title [ro]", "Title RO", "Title - Română" -> "Title"; "Intro" stays "Intro".
# One label for several inputs: rendered as <fieldset><legend>, ids from the field's auto_id.
GROUP_WIDGETS = (forms.RadioSelect, forms.CheckboxSelectMultiple)
CARD_HEADING_LEVELS = range(2, 5)
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
    # A group has no single input to point a <label> at (review v1 ISS-001).
    group = isinstance(field.field.widget, GROUP_WIDGETS)
    widget_id = field.auto_id if group else field.id_for_label
    if not widget_id:
        raise ValueError(f"ui_field needs a form with auto_id (field {field.name!r} has no id)")
    described = [f"{widget_id}_help"] if help else []
    if field.errors:
        described.append(f"{widget_id}_error")
    aria: dict[str, str | bool] = {"aria-describedby": " ".join(described)} if described else {}
    if field.errors:
        aria["aria-invalid"] = "true"
    attrs: dict[str, str | bool] = {"lang": lang} if lang else {}
    widget = field.as_widget(attrs=attrs if group else attrs | aria)
    return {
        "field": field,
        "widget": widget,
        "help": help,
        "id": widget_id,
        "label": legend or field.label,
        "group": group,
        "group_aria": aria if group else {},
    }


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
    title: str,
    body: str = "",
    href: str | None = None,
    icon: str | None = None,
    meta: str = "",
    level: int = 2,
) -> TagContext:
    """A card; with `href` the title is its only link (CSS stretches it over the card).

    `level` is the title's heading level (2-4): the caller knows where the card sits in the page
    outline (review v1 ISS-003). Icon names are validated by ui_icon when the card renders."""
    heading = _whole_number(level, "Card heading level")
    if heading not in CARD_HEADING_LEVELS:
        raise ValueError(f"Card heading level must be 2-4, got {level!r}")
    return {
        "level": heading,
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
