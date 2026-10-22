"""The only sanctioned way to read paired `<field>_ro` / `<field>_en` content (ADR-006)."""

from django.utils import translation

from domain.common.language import DEFAULT_LANGUAGE, Language

_SUPPORTED = frozenset(language.value for language in Language)


def content_language() -> str:
    """Active language as "ro" or "en" ("en-us" → "en"; anything unsupported → "ro")."""
    code = (translation.get_language() or "")[:2].lower()
    return code if code in _SUPPORTED else DEFAULT_LANGUAGE.value


def localized(obj: object, field: str) -> str:
    """Return `obj.<field>_<lang>` for the active language.

    Raises:
        AttributeError: when the field doesn't exist. Fail loudly; never fall back to the
            other language silently.
    """
    return str(getattr(obj, f"{field}_{content_language()}"))
