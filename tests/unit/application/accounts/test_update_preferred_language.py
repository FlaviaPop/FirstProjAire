import pytest

from application.accounts.update_preferred_language import (
    UpdatePreferredLanguage,
    UpdatePreferredLanguageCommand,
)
from domain.common.errors import PolicyViolation
from tests.fakes import FakeUnitOfWork


class FakePreferences:
    def __init__(self, stored):
        self.stored, self.writes = dict(stored), []

    def get_language(self, user_id):
        return self.stored[user_id]

    def set_language(self, user_id, language):
        self.writes.append((user_id, language))
        self.stored[user_id] = language


def _use_case(prefs, uow=None):
    uow = uow or FakeUnitOfWork()
    return UpdatePreferredLanguage(prefs, lambda: uow), uow


def test_changes_language_for_that_user_only():
    prefs = FakePreferences({1: "ro", 2: "ro"})
    use_case, uow = _use_case(prefs)

    changed = use_case.execute(UpdatePreferredLanguageCommand(1, "en"))

    assert changed is True
    assert prefs.stored == {1: "en", 2: "ro"}
    assert prefs.writes == [(1, "en")]
    assert (uow.entered, uow.committed) == (1, 1)


def test_same_language_is_a_no_op():
    prefs = FakePreferences({1: "en"})
    use_case, _ = _use_case(prefs)

    assert use_case.execute(UpdatePreferredLanguageCommand(1, "en")) is False
    assert prefs.writes == []


@pytest.mark.parametrize("code", ["de", "", "RO", "en-us"])
def test_unsupported_language_is_rejected_before_any_read_or_write(code):
    prefs = FakePreferences({1: "ro"})
    use_case, uow = _use_case(prefs)

    with pytest.raises(PolicyViolation) as error:
        use_case.execute(UpdatePreferredLanguageCommand(1, code))

    violation = error.value.violations[0]
    assert (violation.code, violation.params) == ("unsupported_language", {"language": code})
    assert prefs.writes == []
    assert uow.entered == 0
