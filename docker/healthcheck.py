"""Container health probe: GET /healthz as Nginx would forward it (HTTPS host, proxy header).

`SECURE_SSL_REDIRECT` and `ALLOWED_HOSTS` apply to the probe too, so it sends the public host
and `X-Forwarded-Proto: https`. Exit 0 when /healthz answers 200, else 1.
"""

import os
import sys
import urllib.request

host = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost").split(",")[0].strip()
request = urllib.request.Request(
    "http://127.0.0.1:8000/healthz",
    headers={"Host": host, "X-Forwarded-Proto": "https"},
)
try:
    with urllib.request.urlopen(request, timeout=4) as response:  # noqa: S310 - fixed local URL
        sys.exit(0 if response.status == 200 else 1)
except Exception:  # any failure means unhealthy
    sys.exit(1)
