import pytest

from domain.accounts.access_policy import RecordAccessPolicy, can_view_student_records


@pytest.mark.parametrize(
    ("viewer_id", "role", "student_id", "linked", "expected"),
    [
        (1, "STUDENT", 1, set(), True),  # own record
        (1, "STUDENT", 2, set(), False),  # another student → IDOR denied
        (1, "STUDENT", 2, {2}, False),  # links never widen a student's scope
        (9, "PARENT", 1, {1, 3}, True),  # linked child
        (9, "PARENT", 2, {1, 3}, False),  # unlinked child
        (9, "PARENT", 1, set(), False),  # parent with no links
        (9, "PARENT", 9, set(), False),  # a parent's own id is not a student record
        (5, "TEACHER", 2, set(), True),  # scores:view-all
        (7, "ADMIN", 2, set(), True),  # scores:view-all
        (1, "SUPERHERO", 1, set(), False),  # corrupt role never granted
        (1, "", 1, {1}, False),  # empty role never granted
    ],
)
def test_can_view_student_records(viewer_id, role, student_id, linked, expected):
    assert can_view_student_records(viewer_id, role, student_id, linked) is expected


def test_policy_class_exposes_the_same_rule():
    assert RecordAccessPolicy.can_view_student_records is can_view_student_records
