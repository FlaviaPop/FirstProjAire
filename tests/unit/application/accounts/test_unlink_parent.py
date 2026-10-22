"""Story 1.9 AC 7: UnlinkParent deletes and audits once; a missing link is a no-op."""

from application.accounts.link_parent import UnlinkParent
from tests.fakes import FakeAuditPort, FakeParentLinks, FakeUnitOfWork

ROLES = {1: "PARENT", 2: "STUDENT"}


def make():
    links, audit, uow = FakeParentLinks(ROLES), FakeAuditPort(), FakeUnitOfWork()
    links.links[7] = (1, 2)
    return UnlinkParent(links, audit, uow), links, audit, uow


def test_removes_the_link_and_audits_its_parties():
    use_case, links, audit, uow = make()

    removed = use_case.execute(7, actor_id=99)

    assert removed is True
    assert links.links == {}
    assert audit.records == [
        {
            "action": "accounts.parent_unlinked",
            "actor_id": 99,
            "actor_username": "",
            "target": ("parent_child_link", "7"),
            "metadata": {"parent_id": 1, "student_id": 2},
            "ip_address": None,
        }
    ]
    assert (uow.entered, uow.committed) == (1, 1)


def test_unlinking_again_is_a_no_op_without_audit():
    use_case, _, audit, uow = make()
    use_case.execute(7, actor_id=99)

    removed_again = use_case.execute(7, actor_id=99)

    assert removed_again is False
    assert len(audit.records) == 1
    assert (uow.entered, uow.committed) == (2, 2)


def test_unknown_link_is_a_no_op():
    use_case, links, audit, _ = make()

    assert use_case.execute(404, actor_id=99) is False
    assert links.links == {7: (1, 2)}
    assert audit.records == []
