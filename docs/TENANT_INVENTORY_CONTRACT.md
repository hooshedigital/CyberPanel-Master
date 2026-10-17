# Tenant-scoped inventory contract (offline prototype)

This is a separate WSGI prototype, not a CyberPanel integration and not production-ready.
It is intentionally not wired into the existing control_plane.app or public server.

GET /v1/tenants/{tenant_id}/inventory/{sites|ssl|backups} requires an identity
mapped server-side to a tenant and role. viewer can read sites and ssl; admin
may also read backups. A tenant mismatch returns 404 before adapter invocation.
Missing credentials return 401, insufficient role 403, no configured registry 503.
All write methods return 405.

The default adapter returns empty not_connected snapshots. Synthetic fixtures
must not be confused with actual server inventory. Cross-tenant and malformed
adapter responses are rejected with redacted 503 errors.

Run: python -m unittest discover -s tests -v

Before any staging integration: confirm the canonical upstream adapter, replace
test-only identity registry with trusted authentication, add audit and rate
limiting, review backup metadata access, test with two isolated staging tenants,
and obtain owner review with backup and rollback plans.

No production system, live credentials, or customer data are involved.
