from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _


class PlatformLoginForm(AuthenticationForm):
    """Same message for wrong password, unknown user and inactive account (no enumeration)."""

    error_messages = {  # noqa: RUF012  # same shape as Django's AuthenticationForm attribute
        "invalid_login": _("Incorrect username or password."),
        "inactive": _("Incorrect username or password."),
    }
