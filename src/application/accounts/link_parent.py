"""Link a Parent/Guardian to a Student, and remove such links (requirements: admin links parents).

A parent only ever sees the progress of children linked here (CYCLE-3 scoping), so the role
rules are re-checked inside the transaction and the database keeps a UNIQUE(parent, student)
constraint as the last line of defence against a concurrent duplicate.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from application.common.audit import AuditPort
from application.common.unit_of_work import UnitOfWork
from domain.accounts.roles import Role
from domain.common.clock import Clock
from domain.common.errors import ConflictError, PolicyViolation, Violation

LINK_TARGET = "parent_child_link"


class LinkExists(ConflictError):  # noqa: N818 - name fixed by the story contract
    """This parent is already linked to this student."""

    code = "link_exists"


class ParentLinkPort(Protocol):
    """Reads account roles and stores parent-child links."""

    def role_of(self, user_id: int) -> str | None: ...

    def exists(self, parent_id: int, student_id: int) -> bool: ...

    def add(self, parent_id: int, student_id: int, created_by: int, at: datetime) -> int:
        """Insert the link and return its id. Raises `LinkExists` on a duplicate."""
        ...

    def remove(self, link_id: int) -> tuple[int, int] | None:
        """Delete the link and return its `(parent_id, student_id)`, or None if it's gone."""
        ...


@dataclass(frozen=True)
class LinkParentCommand:
    """`actor_id` is always `request.user.pk` (the acting Admin), never request input."""

    parent_id: int
    student_id: int
    actor_id: int


class LinkParent:
    """Create one parent-child link and audit it, in one unit of work."""

    def __init__(
        self, links: ParentLinkPort, audit: AuditPort, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._links, self._audit, self._uow, self._clock = links, audit, uow, clock

    def validate(self, cmd: LinkParentCommand) -> list[Violation]:
        """Every broken rule, in a stable order; empty when the link may be created.

        `link_exists` is only checked when the pair is otherwise valid, so the form never
        reports a duplicate for a pair that could not be linked anyway.
        """
        violations = []
        if self._links.role_of(cmd.parent_id) != Role.PARENT:
            violations.append(Violation("parent_not_parent_role"))
        if self._links.role_of(cmd.student_id) != Role.STUDENT:
            violations.append(Violation("student_not_student_role"))
        if cmd.parent_id == cmd.student_id:
            violations.append(Violation("self_link"))
        if not violations and self._links.exists(cmd.parent_id, cmd.student_id):
            violations.append(Violation("link_exists"))
        return violations

    def execute(self, cmd: LinkParentCommand) -> int:
        """Create the link and return its id.

        Raises:
            LinkExists: the pair is already linked (also when a concurrent request won the race).
            PolicyViolation: a role or same-account rule is broken.
        """
        with self._uow:
            violations = self.validate(cmd)  # re-checked inside the transaction (race-safe)
            if any(v.code == LinkExists.code for v in violations):
                raise LinkExists()
            if violations:
                raise PolicyViolation(violations)
            link_id = self._links.add(
                cmd.parent_id, cmd.student_id, cmd.actor_id, self._clock.now()
            )
            self._audit.record(
                "accounts.parent_linked",
                actor_id=cmd.actor_id,
                target=(LINK_TARGET, str(link_id)),
                metadata={"parent_id": cmd.parent_id, "student_id": cmd.student_id},
            )
        return link_id


class UnlinkParent:
    """Remove one parent-child link and audit it; removing a missing link is a no-op."""

    def __init__(self, links: ParentLinkPort, audit: AuditPort, uow: UnitOfWork) -> None:
        self._links, self._audit, self._uow = links, audit, uow

    def execute(self, link_id: int, actor_id: int) -> bool:
        """Delete the link.

        Returns:
            True if a link was removed; False if it no longer existed (idempotent, no audit).
        """
        with self._uow:
            pair = self._links.remove(link_id)
            if pair is None:
                return False
            parent_id, student_id = pair
            self._audit.record(
                "accounts.parent_unlinked",
                actor_id=actor_id,
                target=(LINK_TARGET, str(link_id)),
                metadata={"parent_id": parent_id, "student_id": student_id},
            )
        return True
