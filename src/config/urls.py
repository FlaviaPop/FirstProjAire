from django.conf.urls.i18n import i18n_patterns
from django.urls import URLPattern, URLResolver, path

from infrastructure.web.common.health import healthz

# Operational endpoints stay outside the language prefix.
urlpatterns: list[URLPattern | URLResolver] = [
    path("healthz", healthz, name="healthz"),
]

urlpatterns += i18n_patterns(
    # Context URL includes are appended here, one block per context, alphabetically.
    prefix_default_language=True,
)

# Story 1.1: localized error pages (full page or HTMX partial).
handler400 = "infrastructure.web.common.errors.handle_400"
handler403 = "infrastructure.web.common.errors.handle_403"
handler404 = "infrastructure.web.common.errors.handle_404"
handler500 = "infrastructure.web.common.errors.handle_500"
