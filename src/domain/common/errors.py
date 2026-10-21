"""Expected business failures. The web layer maps each `code` to an HTTP status and a message."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Violation:
    """One broken business rule. `code` is a stable i18n key; `params` fill its placeholders."""

    code: str
    params: Mapping[str, str | int] = field(default_factory=dict)


class DomainError(Exception):
    """Base for expected business failures; the web layer maps `code` to a localized message."""

    code = "domain_error"

    def __init__(self, detail: str = "") -> None:
        super().__init__(detail or self.code)
        self.detail = detail


class NotFound(DomainError):  # noqa: N818 — name fixed by architecture §Error Handling
    """The record does not exist or is outside the caller's scope (never reveal which)."""

    code = "not_found"


class ConflictError(DomainError):
    """The action was already done or the current state forbids repeating it."""

    code = "conflict"


class PolicyViolation(DomainError):  # noqa: N818 — name fixed by architecture §Error Handling
    """A business rule rejected the input. `violations` lists every broken rule, in order."""

    code = "policy_violation"

    def __init__(self, violations: Sequence[Violation]) -> None:
        """Args:
            violations: every broken rule; at least one.

        Raises:
            ValueError: when `violations` is empty.
        """
        if not violations:
            raise ValueError("PolicyViolation requires at least one Violation")
        super().__init__("; ".join(v.code for v in violations))
        self.violations: tuple[Violation, ...] = tuple(violations)
