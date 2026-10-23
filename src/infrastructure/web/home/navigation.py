"""The role menu registry (Story 1.7): one list per role feeds both the top bar and the home cards.

Entries are kept only when the role holds the permission AND the URL name resolves, so a section
appears by itself once its feature ships. Hiding a link is a convenience; every target view still
enforces its own permission (Story 1.3).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from django.urls import NoReverseMatch, reverse
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _

from domain.accounts.permissions import P, has_permission
from domain.accounts.roles import Role, parse_role


@dataclass(frozen=True)
class NavEntry:
    """One menu entry / home card; `permission` None means every signed-in role."""

    label: str | Promise
    url_name: str
    permission: P | None
    icon: str
    description: str | Promise = ""


HOME = NavEntry(_("Home"), "home:index", None, "house")
SCORES = NavEntry(
    _("Scores"), "progress:scores", P.SCORES_VIEW_ALL, "chart-bar", _("Pilot results")
)
NAV_BY_ROLE: Mapping[Role, tuple[NavEntry, ...]] = {
    Role.STUDENT: (
        HOME,
        NavEntry(_("Learn"), "catalogue:index", P.LESSONS_VIEW, "book-open", _("Choose a subject")),
        NavEntry(
            _("My progress"), "progress:me", P.SCORES_VIEW_OWN, "chart-bar", _("See your results")
        ),
    ),
    Role.TEACHER: (
        HOME,
        NavEntry(
            _("Dashboard"),
            "content:teacher_dashboard",
            P.CONTENT_EDIT,
            "chalkboard-teacher",
            _("Write lessons, exercises and tests"),
        ),
        SCORES,
        NavEntry(
            _("Notifications"),
            "notifications:list",
            P.CONTENT_EDIT,
            "bell",
            _("Messages about your content"),
        ),
    ),
    Role.PARENT: (
        HOME,
        NavEntry(
            _("My children"),
            "progress:children",
            P.CHILD_PROGRESS_VIEW,
            "users",
            _("Progress and scores of your children"),
        ),
    ),
    Role.ADMIN: (
        HOME,
        NavEntry(
            _("Accounts"),
            "admin:index",
            P.ACCOUNTS_MANAGE,
            "shield-check",
            _("Create accounts and link parents"),
        ),
        NavEntry(
            _("Moderation"),
            "moderation:queue",
            P.CONTENT_REVIEW,
            "flag",
            _("Review flagged content"),
        ),
        SCORES,
        NavEntry(
            _("Pilot"),
            "reporting:pilot",
            P.ACCOUNTS_MANAGE,
            "list-checks",
            _("Readiness and completion"),
        ),
    ),
}


def available_sections(user: Any) -> tuple[tuple[NavEntry, str], ...]:
    """(entry, url) pairs the user may use and that exist; unshipped features are skipped.

    Never raises: an invalid role (or an anonymous user) gets `()`, an unknown URL name is skipped.
    """
    role = parse_role(getattr(user, "role", None) or "")
    if role is None:
        return ()
    result = []
    for entry in NAV_BY_ROLE[role]:
        if entry.permission is not None and not has_permission(role, entry.permission):
            continue
        try:
            result.append((entry, reverse(entry.url_name)))
        except NoReverseMatch:
            continue
    return tuple(result)
