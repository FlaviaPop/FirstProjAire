"""Story 1.9 AC 6: LinkParent validates roles, refuses duplicates and audits inside the UoW."""

import pytest

from application.accounts.link_parent import LinkExists, LinkParent, LinkParentCommand
from domain.common.errors import ConflictError, PolicyViolation
from tests.fakes import FakeAuditPort, FakeParentLinks, FakeUnitOfWork, FixedClock

ROLES = {1: "PARENT", 2: "STUDENT", 3: "TEACHER", 4: "STUDENT", 5: "ADMIN"}


def make(links=None):
    links, audit, uow = links or FakeParentLinks(ROLES), FakeAuditPort(), FakeUnitOfWork()
    return LinkParent(links, audit, uow, FixedClock()), links, audit, uow


def test_links_parent_to_student_and_audits():
    use_case, links, audit, uow = make()

    link_id = use_case.execute(LinkParentCommand(1, 2, actor_id=99))

    assert links.links[link_id] == (1, 2)
    assert links.added == [(99, FixedClock().at)]
    assert audit.records == [
        {
            "action": "accounts.parent_linked",
            "actor_id": 99,
            "actor_username": "",
            "target": ("parent_child_link", str(link_id)),
            "metadata": {"parent_id": 1, "student_id": 2},
            "ip_address": None,
        }
    ]
    assert (uow.entered, uow.committed, uow.rolled_back) == (1, 1, 0)


@pytest.mark.parametrize(
    ("parent", "student", "code"),
    [
        (3, 2, "parent_not_parent_role"),
        (5, 2, "parent_not_parent_role"),
        (404, 2, "parent_not_parent_role"),
        (1, 3, "student_not_student_role"),
        (1, 1, "student_not_student_role"),
        (1, 404, "student_not_student_role"),
        (2, 2, "parent_not_parent_role"),
    ],
)
def test_invalid_pairs_are_rejected(parent, student, code):
    use_case, links, audit, uow = make()

    with pytest.raises(PolicyViolation) as error:
        use_case.execute(LinkParentCommand(parent, student, actor_id=99))

    assert code in [v.code for v in error.value.violations]
    assert links.links == {}
    assert audit.records == []
    assert uow.rolled_back == 1


def test_validate_reports_every_broken_rule_in_order():
    use_case, *_ = make()

    violations = use_case.validate(LinkParentCommand(3, 404, actor_id=99))

    assert [v.code for v in violations] == ["parent_not_parent_role", "student_not_student_role"]


def test_a_student_linked_to_themselves_breaks_the_parent_and_same_account_rules():
    use_case, *_ = make()

    violations = use_case.validate(LinkParentCommand(2, 2, actor_id=99))

    assert [v.code for v in violations] == ["parent_not_parent_role", "self_link"]


def test_linking_a_parent_to_themselves_names_the_same_account_rule():
    use_case, *_ = make()

    assert [v.code for v in use_case.validate(LinkParentCommand(1, 1, 99))] == [
        "student_not_student_role",
        "self_link",
    ]


def test_validate_is_empty_for_a_valid_new_pair():
    use_case, *_ = make()

    assert use_case.validate(LinkParentCommand(1, 2, actor_id=99)) == []


def test_validate_reports_existing_link_only_when_roles_are_valid():
    use_case, *_ = make()
    use_case.execute(LinkParentCommand(1, 2, actor_id=99))

    assert [v.code for v in use_case.validate(LinkParentCommand(1, 2, 99))] == ["link_exists"]
    assert [v.code for v in use_case.validate(LinkParentCommand(3, 2, 99))] == [
        "parent_not_parent_role"
    ]


def test_duplicate_link_raises_conflict_and_adds_nothing():
    use_case, links, audit, _ = make()
    use_case.execute(LinkParentCommand(1, 2, actor_id=99))

    with pytest.raises(LinkExists) as error:
        use_case.execute(LinkParentCommand(1, 2, actor_id=99))

    assert isinstance(error.value, ConflictError)
    assert error.value.code == "link_exists"
    assert len(links.links) == 1
    assert len(audit.records) == 1


def test_race_detected_by_the_repository_is_a_conflict_and_not_audited():
    links = FakeParentLinks(ROLES, hide_existing=True)
    links.links[1] = (1, 2)  # inserted concurrently, invisible to the pre-check
    use_case, _, audit, uow = make(links)

    with pytest.raises(LinkExists):
        use_case.execute(LinkParentCommand(1, 2, actor_id=99))

    assert audit.records == []
    assert uow.rolled_back == 1


def test_parent_can_have_several_children_and_child_several_parents():
    roles = {**ROLES, 6: "PARENT"}
    use_case, links, _, _ = make(FakeParentLinks(roles))

    use_case.execute(LinkParentCommand(1, 2, actor_id=99))
    use_case.execute(LinkParentCommand(1, 4, actor_id=99))
    use_case.execute(LinkParentCommand(6, 2, actor_id=99))

    assert sorted(links.links.values()) == [(1, 2), (1, 4), (6, 2)]
