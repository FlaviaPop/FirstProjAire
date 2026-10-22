"""Persist a signed-in user's UI language so their next sign-in opens in it."""

from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol

from domain.common.errors import PolicyViolation, Violation
from domain.common.language import Language

SUPPORTED_LANGUAGES = frozenset(language.value for language in Language)


class UserPreferencePort(Protocol):
    """Reads and writes one user's `preferred_language`."""

    def get_language(self, user_id: int) -> str: ...

    def set_language(self, user_id: int, language: str) -> None: ...


@dataclass(frozen=True)
class UpdatePreferredLanguageCommand:
    """`user_id` is always `request.user.pk`, never request input (IDOR guard)."""

    user_id: int
    language: str


class UpdatePreferredLanguage:
    """Save the language only when it differs from the stored one (repeat switches don't write)."""

    def __init__(
        self,
        users: UserPreferencePort,
        uow_factory: Callable[[], AbstractContextManager[object]],
    ) -> None:
        self._users, self._uow_factory = users, uow_factory

    def execute(self, cmd: UpdatePreferredLanguageCommand) -> bool:
        """Persist `cmd.language` for `cmd.user_id`.

        Returns:
            True if a write happened, False if the language was already stored.

        Raises:
            PolicyViolation: `unsupported_language` for anything other than "ro"/"en"
                (defence in depth; the view validates first).
        """
        if cmd.language not in SUPPORTED_LANGUAGES:
            raise PolicyViolation([Violation("unsupported_language", {"language": cmd.language})])
        with self._uow_factory():
            if self._users.get_language(cmd.user_id) == cmd.language:
                return False
            self._users.set_language(cmd.user_id, cmd.language)
            return True
