"""POST /<lang>/accounts/logout/ — flushes the session; GET is refused."""

import pytest
from django.contrib.sessions.models import Session
from django.test import Client

pytestmark = pytest.mark.django_db


def test_logout_requires_post_and_flushes_session(student_client):
    assert student_client.get("/ro/accounts/logout/").status_code == 405

    response = student_client.post("/ro/accounts/logout/")

    assert response["Location"] == "/ro/accounts/login/"
    assert Session.objects.count() == 0


def test_get_logout_keeps_the_session(student_client):
    student_client.get("/ro/accounts/logout/")

    assert Session.objects.count() == 1


def test_logout_redirects_to_login_in_the_current_language(student_client):
    response = student_client.post("/en/accounts/logout/")

    assert response["Location"] == "/en/accounts/login/"


def test_next_request_after_logout_is_anonymous(student_client):
    student_client.post("/ro/accounts/logout/")

    response = student_client.get("/ro/accounts/login/")

    assert response.wsgi_request.user.is_anonymous


def test_logout_when_signed_out_is_harmless(client):
    response = client.post("/ro/accounts/logout/")

    assert response.status_code == 302
    assert response["Location"] == "/ro/accounts/login/"


def test_logout_without_csrf_is_rejected(student):
    strict = Client(enforce_csrf_checks=True)
    strict.force_login(student, backend="django.contrib.auth.backends.ModelBackend")

    response = strict.post("/ro/accounts/logout/")

    assert response.status_code == 403
    assert Session.objects.count() == 1


def test_logout_with_csrf_token_flushes_under_strict_checks(student):
    strict = Client(enforce_csrf_checks=True)
    strict.force_login(student, backend="django.contrib.auth.backends.ModelBackend")
    token = strict.get("/ro/accounts/login/").context["csrf_token"]

    response = strict.post("/ro/accounts/logout/", {"csrfmiddlewaretoken": str(token)})

    assert response.status_code == 302
    assert Session.objects.count() == 0
