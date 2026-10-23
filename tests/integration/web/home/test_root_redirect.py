"""Story 1.4 AC 2 hand-off: `/` redirects to the visitor's language home (`home:index`)."""

import pytest

pytestmark = pytest.mark.django_db


def test_root_redirects_to_romanian_by_default(client):
    response = client.get("/")

    assert (response.status_code, response["Location"]) == (302, "/ro/")


def test_root_honours_accept_language(client):
    response = client.get("/", headers={"Accept-Language": "en-GB,en;q=0.9"})

    assert response["Location"] == "/en/"


def test_root_prefers_the_language_cookie(client):
    client.cookies["django_language"] = "en"

    response = client.get("/", headers={"Accept-Language": "ro"})

    assert response["Location"] == "/en/"


def test_signed_in_root_lands_on_the_role_home(student_client):
    response = student_client.get("/", follow=True)

    assert response.redirect_chain[0] == ("/ro/", 302)
    assert response.status_code == 200
    assert "home/student.html" in [t.name for t in response.templates]
