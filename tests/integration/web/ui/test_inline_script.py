"""No inline script in the primitive templates (Story 1.6 refinement of a Story 1.5 rule).

Story 1.5's test_atoms.py banned every `<script` in templates/components and
templates/styleguide. Story 1.6 AC 12 loads ui.js there as an external
`<script type="module" src>`, so the ban is narrowed to what CSP (`script-src 'self'`) forbids:
inline code. Style, |safe and mark_safe stay banned in test_atoms.py.
"""

import re

import pytest
from django.conf import settings

WEB_DIR = settings.BASE_DIR / "src/infrastructure/web"


def primitive_templates() -> list:
    return [
        *(WEB_DIR / "templates/components").glob("*.html"),
        *(WEB_DIR / "templates/styleguide").glob("*.html"),
    ]


SCRIPT_ELEMENT = re.compile(r"<script\b([^>]*)>(.*?)</script\s*>", re.I | re.S)
INLINE_HANDLER = re.compile(r"\son[a-z]+\s*=", re.I)


def inline_scripts(source: str) -> list[str]:
    """Inline script code in `source`: a <script> without src, a script body, or an on*= handler."""
    elements = SCRIPT_ELEMENT.findall(source)
    found = [f"<script{attrs}>" for attrs, body in elements if "src=" not in attrs or body.strip()]
    if len(re.findall(r"<script\b", source, re.I)) != len(elements):
        found.append("unclosed <script>")
    return found + INLINE_HANDLER.findall(source)


@pytest.mark.parametrize(
    "source",
    [
        "<script>alert(1)</script>",
        '<script type="module">import "/x.js";</script>',
        '<script type="module" src="/static/js/ui.js">alert(1)</script>',
        "<SCRIPT>alert(1)</SCRIPT>",
        "<script>alert(1)",
        '<button type="button" onclick="go()">Go</button>',
        '<img src="/x.png" onerror = "go()">',
    ],
)
def test_inline_script_detector_catches_inline_code(source):
    assert inline_scripts(source) != []


def test_inline_script_detector_allows_an_external_module_and_noscript():
    source = '<script type="module" src="/static/js/ui.js"></script><noscript><p>JS</p></noscript>'

    assert inline_scripts(source) == []


def test_component_and_styleguide_templates_have_no_inline_script():
    templates = primitive_templates()

    offenders = {str(p): inline_scripts(p.read_text(encoding="utf-8")) for p in templates}

    assert templates
    assert {path: found for path, found in offenders.items() if found} == {}


def test_the_only_script_in_primitive_templates_is_the_same_origin_ui_module():
    scripts = [
        (p.name, attrs.strip())
        for p in primitive_templates()
        for attrs, _body in SCRIPT_ELEMENT.findall(p.read_text(encoding="utf-8"))
    ]

    assert scripts == [("index.html", 'type="module" src="{% static \'js/ui.js\' %}"')]
