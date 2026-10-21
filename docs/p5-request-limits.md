# P5: request ingress limit

The API now accepts at most 22 MiB of HTTP request body, including multipart
boundaries and metadata. This leaves room for the existing 20 MiB PDF limit;
individual JSON/CSV/PDF limits remain in force.

An ASGI middleware checks declared Content-Length before reading, and always counts
actual body bytes, including requests without Content-Length. Oversized requests
return JSON HTTP 413 before any endpoint or multipart parser runs. Invalid or
duplicate length headers return HTTP 400. CORS headers remain available to the
local frontend. Disconnects abandon the input without running the endpoint.

The body is buffered in a bounded bytearray before replay to the application.
This deliberately prevents multipart spooling before validation, at the cost of
buffering accepted requests. Conversion for replay temporarily holds two body
copies. This is a per-request application limit, not a total process memory limit
or an upstream server/proxy buffering guarantee.

The completed P5 layer adds an eight-request admission limit, a 30-second body-read
deadline, authentication before body handling, SQLite transactions and bounded jobs.
Linux PDF workers also enforce CPU/address-space limits. See
[deployment and operating boundaries](p5-deployment.md); upstream proxy/OS aggregate
limits remain an operator responsibility.

Validation covers declared/actual/chunked oversize, exact boundary, malformed
headers, disconnects and the real application CORS/error path, plus existing
multipart upload regression tests. No network/provider calls are needed.
