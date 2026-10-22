from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponse

from infrastructure.web.accounts.forms import PlatformLoginForm


class PlatformLoginView(LoginView):
    """GET/POST /<lang>/accounts/login/ — public; redirects to a safe `next` or the user's home."""

    template_name = "accounts/login.html"
    authentication_form = PlatformLoginForm
    redirect_authenticated_user = False  # a repeat login re-authenticates and rotates the key

    def form_valid(self, form: AuthenticationForm) -> HttpResponse:
        if self.request.user.is_authenticated:
            # login() rotates the key only for a new sign-in; rotate on a repeat one too.
            self.request.session.cycle_key()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        # LoginView.get_redirect_url() returns "" unless `next` is same-host with a safe scheme
        # (url_has_allowed_host_and_scheme), so it's the single place that check lives.
        # Otherwise the target comes from the authenticated user, never from client input.
        return self.get_redirect_url() or f"/{self.request.user.preferred_language}/"  # type: ignore[union-attr]


class PlatformLogoutView(LogoutView):
    """POST /<lang>/accounts/logout/ — public; flushes the session (GET → 405, Django default)."""

    next_page = "accounts:login"
