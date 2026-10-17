# CyberPanel Control Plane — HTTP/WSGI Bearer Boundary (offline)

This branch is a review-only security contract for the independent read-only
control-plane prototype. It does not connect to CyberPanel and is not a
production authentication design.

## Reproducible verification

From the repository root after applying the accompanying offline patch:

```sh
python -m unittest discover -s tests -v
```

The standalone offline bundle contains 41 local tests (10 new WSGI/HTTP
boundary tests and 31 existing security/unit tests). New cases cover:
- Non-string Authorization values injected through WSGI.
- Control/format/surrogate Unicode and oversized Bearer headers.
- Unauthorized responses without token reflection.
- Actual HTTP requests to a loopback-only WSGI server.
- Authenticated read-only access, 405 for writes, 404 for unknown routes.
- `Cache-Control: no-store` and `X-Content-Type-Options: nosniff`.

## Review constraints

**GitHub CI: NOT_RUN for this code** until executable files are committed.
Do not infer a passing status from CI on PR #1 at a different SHA.
The executable patch is supplied separately for owner application because
the GitHub connector refused writes to Python source.

Before any staging use, confirm the canonical source, apply the patch to
the exact PR #1 head, run tests, review token handling and rollback plan.
No merge, deploy, production access, customer data or live credentials.
