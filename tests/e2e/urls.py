"""E2E-only URLconf: the project routes and error handlers, plus one test page under the language
prefixes (/<lang>/e2e/dialog/). Never part of config.urls, so production routing is untouched."""

from django.conf.urls.i18n import i18n_patterns
from django.urls import path
from django.views.generic import TemplateView

from config.urls import handler400, handler403, handler404, handler500  # noqa: F401
from config.urls import urlpatterns as root_urlpatterns

urlpatterns = [
    *root_urlpatterns,
    *i18n_patterns(
        path(
            "e2e/dialog/",
            TemplateView.as_view(
                template_name="e2e/dialog.html", extra_context={"rows": range(1, 41)}
            ),
        ),
        prefix_default_language=True,
    ),
]
