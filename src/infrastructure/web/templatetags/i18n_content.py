"""Template access to bilingual content: `{% load i18n_content %}{% localized obj "field" %}`."""

from django import template

from infrastructure.web.common.i18n import localized as _localized

register = template.Library()


@register.simple_tag
def localized(obj: object, field: str) -> str:
    """{% localized subject "name" %} → subject.name_ro / subject.name_en (autoescaped)."""
    return _localized(obj, field)
