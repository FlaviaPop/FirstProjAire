"""Register the platform's focused admin modules on one protected admin site."""

from . import audit_admin as _audit_admin  # noqa: F401
from . import lockout_admin as _lockout_admin  # noqa: F401
from . import parent_link_admin as _parent_link_admin  # noqa: F401
from . import user_admin as _user_admin  # noqa: F401
from .admin_site import PlatformAdminSite, platform_admin_site
from .user_admin import delete_selected

__all__ = ["PlatformAdminSite", "delete_selected", "platform_admin_site"]
