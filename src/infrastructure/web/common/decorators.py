"""Authorization decorators and the public-route registry.

PUBLIC_URL_NAMES lists every URL name reachable without a permission check. Story 1.3
adds @require_permission here, plus a test that fails for any URL that is neither
decorated nor listed below.
"""

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, Protocol, cast

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse

from domain.accounts.permissions import Permission, has_permission
from domain.accounts.roles import parse_role

PUBLIC_URL_NAMES: frozenset[str] = frozenset({"healthz", "accounts:login", "accounts:logout"})

# Not `View`, to avoid confusion with django.views.View (class-based views).
ViewCallable = Callable[..., HttpResponse]


class GuardedView(Protocol):
    """A view wrapped by a guard; `required_permissions` is read by test_url_protection."""

    required_permissions: tuple[Permission, ...]
    __name__: str

    def __call__(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse: ...


def _guard(view: ViewCallable, permissions: tuple[Permission, ...]) -> GuardedView:
    if inspect.iscoroutinefunction(view):
        # The wrapper is synchronous and would return an un-awaited coroutine.
        raise TypeError("async views are not supported by the role guards")

    @wraps(view)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        # Identity comes only from the session user; request parameters are never consulted.
        role = parse_role(getattr(request.user, "role", ""))
        if role is None or not all(has_permission(role, p) for p in permissions):
            raise PermissionDenied
        return view(request, *args, **kwargs)

    guarded = cast("GuardedView", wrapper)
    guarded.required_permissions = permissions
    return guarded


def require_permission(*permissions: Permission) -> Callable[[ViewCallable], GuardedView]:
    """Allow the view only if the user's role holds ALL given permissions (403 otherwise).

    Anonymous users are redirected to `settings.LOGIN_URL` with `next`.

    Raises:
        ValueError: at decoration time when no permission is given, or when a key isn't one of
            the 16 `Permission` values (fail fast at import instead of denying everyone).
    """
    if not permissions:
        raise ValueError("require_permission needs at least one Permission")
    required = tuple(Permission(p) for p in permissions)
    return lambda view: _guard(view, required)


def require_authenticated(view: ViewCallable) -> GuardedView:
    """Allow any signed-in user with a valid role (home, catalogue)."""
    return _guard(view, ())
