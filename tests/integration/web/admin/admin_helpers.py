"""Helpers shared by the Story 1.9 admin tests (plain module, imported explicitly)."""

from infrastructure.persistence.audit.models import AuditLogModel

USERS = "/en/admin/accounts/usermodel/"
LINKS = "/en/admin/accounts/parentchildlinkmodel/"
ATTEMPTS = "/en/admin/axes/accessattempt/"
AUDIT = "/en/admin/audit/auditlogmodel/"
STRONG_PASSWORD = "Pilot-Start-2026!"


def change_data(user, **overrides):
    """POST body for the user change form, starting from the stored values."""
    data = {
        "username": user.username,
        "full_name": user.full_name,
        "date_of_birth": user.date_of_birth.isoformat(),
        "role": user.role,
        "preferred_language": user.preferred_language,
        "is_active": "on" if user.is_active else "",
    }
    data.update(overrides)
    return {key: value for key, value in data.items() if value != ""}


def audit_rows(action=None):
    rows = AuditLogModel.objects.order_by("id")
    if action is not None:
        rows = rows.filter(action=action)
    return list(rows.values("action", "actor_id", "actor_username", "target_id", "metadata"))


def admin_rows(action=None):
    """Audit rows written by admin actions (the test client's sign-in rows excluded)."""
    return [row for row in audit_rows(action) if not row["action"].startswith("auth.log")]
