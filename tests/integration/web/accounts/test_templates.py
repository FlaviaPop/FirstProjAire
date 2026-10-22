"""Template rules of AC 13: layout, translation, one <h1>, labels, autocomplete, no inline code."""

import re
from pathlib import Path

import pytest
from django.conf import settings

pytestmark = pytest.mark.django_db
TEMPLATES = Path(settings.BASE_DIR) / "src/infrastructure/web/templates/accounts"
TEMPLATE_NAMES = ["login.html", "locked_out.html"]


@pytest.mark.parametrize("name", TEMPLATE_NAMES)
def test_template_extends_base_layout_and_loads_i18n(name):
    source = (TEMPLATES / name).read_text()

    assert source.startswith('{% extends "layouts/base.html" %}')
    assert "{% load i18n" in source


@pytest.mark.parametrize("name", TEMPLATE_NAMES)
def test_template_has_no_inline_style_script_or_safe(name):
    source = (TEMPLATES / name).read_text()

    assert not re.search(r"<style|<script|\sstyle=|\son[a-z]+=", source)
    assert "|safe" not in source
    assert "mark_safe" not in source


@pytest.mark.parametrize("name", TEMPLATE_NAMES)
def test_every_visible_string_is_translated(name):
    source = (TEMPLATES / name).read_text()
    # {% blocktranslate %}…{% endblocktranslate %} bodies are translated text: drop them first.
    without_blocks = re.sub(
        r"{%\s*blocktranslate.*?{%\s*endblocktranslate\s*%}", "", source, flags=re.DOTALL
    )
    without_tags = re.sub(r"{%.*?%}|{{.*?}}|<[^>]+>", "", without_blocks, flags=re.DOTALL)

    assert without_tags.strip() == ""


def test_login_page_markup_is_accessible(client):
    content = client.get("/en/accounts/login/").content.decode()

    assert content.count("<h1") == 1
    assert '<label for="id_username">' in content
    assert '<label for="id_password">' in content
    assert 'id="id_username"' in content
    assert 'autocomplete="username"' in content
    assert 'autocomplete="current-password"' in content
    assert 'type="password"' in content
    assert 'class="login-card"' in content
    assert 'aria-hidden="true"' in content
    assert "#sign-in-duotone" in content


def test_lockout_template_uses_the_lock_icon():
    # Review v1 ISS-001: rendered through the ui_icon primitive (decorative, aria-hidden);
    # the rendered markup is asserted in test_templates_review_v1.py.
    source = (TEMPLATES / "locked_out.html").read_text()

    assert '{% ui_icon "lock-simple" size=32 variant="duotone" %}' in source
