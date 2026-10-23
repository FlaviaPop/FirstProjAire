"""Story 2.2 review v1 ISS-001: students see duotone card icons, staff regular (design tokens)."""

import re

import pytest
from django.template import Context, Template

pytestmark = pytest.mark.django_db


def _render(source: str, **context: object) -> str:
    return Template("{% load ui %}" + source).render(Context(context))


def test_card_icon_defaults_to_the_regular_symbol():
    assert '#book-open"' in _render('{% ui_card "Matematică" icon="book-open" %}')


def test_card_icon_can_be_duotone():
    html = _render('{% ui_card "Matematică" icon="book-open" icon_variant="duotone" %}')

    assert "#book-open-duotone" in html


@pytest.mark.parametrize("variant", ["filled", "", None])
def test_card_rejects_unknown_icon_variants(variant):
    with pytest.raises(ValueError, match="Unknown icon variant"):
        _render('{% ui_card "Matematică" icon="book-open" icon_variant=v %}', v=variant)


def test_student_catalogue_cards_are_duotone(student_client):
    html = student_client.get("/ro/catalogue/").content.decode()
    cards = re.findall(r'<article class="card[^"]*">.*?</article>', html, re.S)

    assert len(cards) == 3
    assert all("#book-open-duotone" in card for card in cards)


@pytest.mark.parametrize("fixture", ["teacher_client", "parent_client", "admin_client"])
def test_staff_catalogue_cards_are_regular(request, fixture):
    html = request.getfixturevalue(fixture).get("/ro/catalogue/").content.decode()
    cards = re.findall(r'<article class="card[^"]*">.*?</article>', html, re.S)

    assert len(cards) == 3
    assert all('#book-open"' in card for card in cards)


def test_student_home_cards_are_duotone(student_client):
    html = student_client.get("/ro/").content.decode()
    main = html[html.index('<main id="content"') :]

    assert "#book-open-duotone" in main  # the "Learn" card


def test_admin_home_cards_are_regular(admin_client):
    html = admin_client.get("/ro/").content.decode()
    main = html[html.index('<main id="content"') :]

    assert '#shield-check"' in main
