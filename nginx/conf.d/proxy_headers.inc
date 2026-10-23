# Shared proxy headers (included from each location).
proxy_set_header Host              $host;
# One trusted hop: the client address as Nginx saw it (axes: AXES_PROXY_COUNT=1).
proxy_set_header X-Forwarded-For   $remote_addr;
proxy_set_header X-Forwarded-Proto https;
# Story 1.1 review ISS-004: the request id is always set here, never taken from the client.
proxy_set_header X-Request-ID      $request_id;
proxy_read_timeout 30s;
