"""Object-level scope for student records (ADR-007: role check = 403, record scope = 404)."""

from collections.abc import Collection

from domain.accounts.permissions import Permission, has_permission
from domain.accounts.roles import Role, parse_role


def can_view_student_records(
    viewer_id: int, viewer_role: str, student_id: int, linked_student_ids: Collection[int]
) -> bool:
    """Decide whether a viewer may see one student's records (progress, scores, attempts).

    Identity arguments MUST come from the authenticated session, never from request input;
    `student_id` is only the subject of the check.

    Args:
        viewer_id: `request.user.pk`.
        viewer_role: `request.user.role` as persisted.
        student_id: The student whose records are requested.
        linked_student_ids: Students linked to the viewer as a parent, loaded server-side.

    Returns:
        True only for the student themself, a linked parent, or a `scores:view-all` role.
    """
    role = parse_role(viewer_role)
    if role is None:
        return False
    if has_permission(role, Permission.SCORES_VIEW_ALL):
        return True
    if role is Role.PARENT:
        return student_id in linked_student_ids
    return role is Role.STUDENT and viewer_id == student_id


class RecordAccessPolicy:
    """Namespace for the record-scope rule, as named in the architecture (ADR-007)."""

    can_view_student_records = staticmethod(can_view_student_records)
