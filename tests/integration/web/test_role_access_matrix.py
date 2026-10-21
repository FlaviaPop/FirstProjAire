# Seeded by Story 1.0; Stories 1.3, 1.7 and 2.2 add rows.
import pytest
from django.urls import reverse

from infrastructure.web.common.decorators import PUBLIC_URL_NAMES

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("url_name", sorted(PUBLIC_URL_NAMES))
def test_public_routes_are_reachable_anonymously(client, url_name):
    response = client.get(reverse(url_name))

    assert response.status_code == 200
