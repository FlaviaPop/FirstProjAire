# Seeded by Story 1.0; Stories 1.3, 1.7 and 2.2 add rows.
import pytest
from django.urls import reverse

from infrastructure.web.common.decorators import PUBLIC_URL_NAMES
from tests.factories.accounts import UserFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("url_name", sorted(PUBLIC_URL_NAMES))
def test_public_routes_are_reachable_anonymously(client, url_name):
    response = client.get(reverse(url_name))

    assert response.status_code == 200


# --- Story 1.3: role-by-route harness (patterns §12.4) --------------------------------------
# Fixture names match Story 1.2's tests/conftest.py. Until 1.2 is merged into this branch,
# the stand-ins below provide them; delete the stand-ins when merging 1.2 so its fixtures win.


def _client_for(client, role):
    client.force_login(UserFactory(role=role))
    return client


@pytest.fixture
def student_client(client):
    return _client_for(client, "STUDENT")


@pytest.fixture
def teacher_client(client):
    return _client_for(client, "TEACHER")


@pytest.fixture
def parent_client(client):
    return _client_for(client, "PARENT")


@pytest.fixture
def admin_client(client):
    return _client_for(client, "ADMIN")


CLIENT_FOR_ROLE = {
    "anonymous": "client",
    "Student": "student_client",
    "Teacher": "teacher_client",
    "Parent/Guardian": "parent_client",
    "Admin": "admin_client",
}
# (role, path, expected_status) — append one block per story, grouped by route.
ROWS = [(role, "/healthz", 200) for role in CLIENT_FOR_ROLE]


@pytest.mark.parametrize(("role", "path", "expected"), ROWS)
def test_role_access_matrix(request, role, path, expected):
    client = request.getfixturevalue(CLIENT_FOR_ROLE[role])

    assert client.get(path).status_code == expected
