"""POST /i18n/setlang/: language switch for everyone; persisted for signed-in users."""

from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.utils import translation
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.i18n import set_language

from application.accounts.update_preferred_language import UpdatePreferredLanguageCommand
from infrastructure import container
from infrastructure.web.common.i18n import content_language

_SUPPORTED = frozenset(code for code, _name in settings.LANGUAGES)


def _safe_next(request: HttpRequest) -> str | None:
    next_url = request.POST.get("next", "")
    allowed = {request.get_host()}
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed, request.is_secure()):
        return next_url
    return None


@require_POST
def switch_language(request: HttpRequest) -> HttpResponse:
    """POST /i18n/setlang/ — public. Sets the cookie; persists the preference when signed in."""
    language = request.POST.get("language", "")
    if language not in _SUPPORTED:
        # Django's set_language accepts any locale Django ships (e.g. "de"); only ro/en here.
        return redirect(_safe_next(request) or f"/{content_language()}/")
    next_url = _safe_next(request)
    # translate_url only resolves `next` in the *active* language, so activate the language of
    # next's own prefix; otherwise /en/x/ → ro stays /en/x/ when the cookie says "ro".
    source = translation.get_language_from_path(urlsplit(next_url or "").path)
    with translation.override(source or content_language()):
        response = set_language(request)  # sets cookie, translates next to the chosen prefix
    if next_url is None:
        # Django falls back to the Referer (or "/", or 204); the story requires /<language>/.
        fallback = HttpResponseRedirect(f"/{language}/")
        fallback.cookies = response.cookies
        response = fallback
    if request.user.is_authenticated:
        # Identity from the session only: extra POST fields (user_id, username) are ignored.
        container.update_preferred_language().execute(
            UpdatePreferredLanguageCommand(user_id=request.user.pk, language=language)
        )
    return response
