"""Languages the platform supports for UI text and bilingual content."""

from enum import StrEnum


class Language(StrEnum):
    """Supported languages; values are the codes used in URLs and persisted preferences."""

    RO = "ro"
    EN = "en"


DEFAULT_LANGUAGE = Language.RO
