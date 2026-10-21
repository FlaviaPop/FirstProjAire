import dataclasses

import pytest

from domain.common.errors import ConflictError, DomainError, NotFound, PolicyViolation, Violation


@pytest.mark.parametrize(
    ("error", "code"),
    [(DomainError(), "domain_error"), (NotFound(), "not_found"), (ConflictError(), "conflict")],
)
def test_each_domain_error_exposes_a_stable_code(error, code):
    assert error.code == code


def test_policy_violation_keeps_every_violation_in_order():
    violations = [
        Violation("points_total_not_100", {"total": 95}),
        Violation("questions_not_10", {"count": 9}),
    ]

    error = PolicyViolation(violations)

    assert error.violations == tuple(violations)
    assert error.code == "policy_violation"


def test_policy_violation_requires_at_least_one_violation():
    with pytest.raises(ValueError, match="at least one"):
        PolicyViolation([])


def test_subclass_codes_override_parent_codes():
    class AlreadySubmitted(ConflictError):  # noqa: N818 — mirrors the architecture's error name
        code = "test_already_submitted"

    assert isinstance(AlreadySubmitted(), ConflictError)
    assert AlreadySubmitted().code == "test_already_submitted"


def test_every_domain_error_is_a_domain_error_subclass():
    assert all(issubclass(cls, DomainError) for cls in (NotFound, ConflictError, PolicyViolation))


def test_detail_becomes_the_exception_text_when_given():
    error = NotFound("lesson 7")

    assert (error.detail, str(error)) == ("lesson 7", "lesson 7")


def test_code_becomes_the_exception_text_when_no_detail_is_given():
    error = ConflictError()

    assert (error.detail, str(error)) == ("", "conflict")


def test_policy_violation_text_joins_violation_codes():
    error = PolicyViolation([Violation("a_rule"), Violation("b_rule")])

    assert str(error) == "a_rule; b_rule"


def test_violation_params_default_to_empty_mapping():
    assert Violation("a_rule").params == {}


def test_violation_is_immutable():
    violation = Violation("a_rule", {"total": 95})

    with pytest.raises(dataclasses.FrozenInstanceError):
        violation.code = "other"  # type: ignore[misc]
