import pytest
from django.test import RequestFactory

from infrastructure.web.common.htmx import is_htmx


@pytest.mark.parametrize(
    ("headers", "expected"),
    [
        ({"HX-Request": "true"}, True),
        ({}, False),
        ({"HX-Request": "false"}, False),
        ({"HX-Request": "1"}, False),
    ],
)
def test_is_htmx_only_when_hx_request_header_is_true(headers, expected):
    request = RequestFactory().get("/", headers=headers)

    assert is_htmx(request) is expected
