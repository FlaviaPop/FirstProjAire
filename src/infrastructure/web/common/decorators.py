"""Authorization decorators and the public-route registry.

PUBLIC_URL_NAMES lists every URL name reachable without a permission check. Story 1.3
adds @require_permission here, plus a test that fails for any URL that is neither
decorated nor listed below.
"""

PUBLIC_URL_NAMES: frozenset[str] = frozenset({"healthz"})
