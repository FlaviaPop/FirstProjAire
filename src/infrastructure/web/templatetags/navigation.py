"""Layout tags (Story 1.7): the role menu, the home cards and the database-safe shell context.

The shell (top bar, theme, flash messages) renders on every page, error pages included. Reading
the signed-in user or the session-backed messages needs the database, so when that fails the
shell renders as for a signed-out visitor (Story 1.1 review v1 ISS-003): an error page must
never fail because of its own frame.
"""

from typing import Any

from django import template
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import constants
from django.db import DatabaseError

from infrastructure.web.home.navigation import HOME, NavEntry, available_sections

register = template.Library()

# Django message level -> ui_alert level; "debug" has no alert style.
ALERT_LEVEL = {
    constants.DEBUG: "info",
    constants.INFO: "info",
    constants.SUCCESS: "success",
    constants.WARNING: "warning",
    constants.ERROR: "error",
}


def shell_user_of(request: Any) -> Any:
    """`request.user`, or an anonymous user when there is none or the database is down."""
    user = getattr(request, "user", None)
    try:
        if user is not None and user.is_authenticated:
            return user
    except DatabaseError:
        pass
    return AnonymousUser()


@register.simple_tag(takes_context=True)
def shell_user(context: template.Context) -> Any:
    """`{% shell_user as shell_user %}`: the user the layout may safely render."""
    return shell_user_of(context.get("request"))


@register.simple_tag(takes_context=True)
def shell_messages(context: template.Context) -> list[Any]:
    """The pending flash messages (consumed by iterating); none when the session is unreadable."""
    try:
        return list(context.get("messages") or ())
    except DatabaseError:
        return []


@register.filter
def alert_level(message: Any) -> str:
    """The ui_alert level for a Django message (custom levels fall back to "info")."""
    return ALERT_LEVEL.get(getattr(message, "level", constants.INFO), "info")


def _sections(context: template.Context) -> tuple[tuple[NavEntry, str], ...]:
    return available_sections(shell_user_of(context.get("request")))


@register.inclusion_tag("layouts/_nav.html", takes_context=True)
def role_nav(context: template.Context) -> dict[str, Any]:
    """Top-bar links for the user's role, `aria-current` on the page being shown."""
    path = getattr(context.get("request"), "path", "")
    return {"items": [(entry, url, url == path) for entry, url in _sections(context)]}


@register.inclusion_tag("home/_cards.html", takes_context=True)
def role_home_cards(context: template.Context) -> dict[str, Any]:
    """Home cards from the same registry as the menu (Home itself excluded)."""
    sections = context.get("sections")
    if sections is None:
        sections = [(entry, url) for entry, url in _sections(context) if entry is not HOME]
    return {"sections": sections, "icon_variant": context.get("icon_variant") or "regular"}
