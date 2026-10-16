# Independent CyberPanel control-plane (prototype)

**Status: prototype only; no real CyberPanel server integration.**

This prototype responds to `GET /health` and `GET /v1/capabilities`.
All capability inventory items report `not_connected`: no fake sites, SSL
certificates or backups are presented as real assets. `POST` and unknown
routes are denied. The only credential is `CONTROL_PLANE_READ_TOKEN` from
runtime environment; no secret is committed.

## Run and verify offline

```bash
python -m unittest discover -s tests -v
CONTROL_PLANE_READ_TOKEN='<test-only-random-token>' python -m control_plane.app
curl http://127.0.0.1:8088/health
curl -H 'Authorization: Bearer <test-only-random-token>' http://127.0.0.1:8088/v1/capabilities
```

The prototype listens on `127.0.0.1:8088` only, not a public interface.
Do not expose it to an untrusted network. This bearer token is intentionally
minimal and is **not** adequate for a production admin panel.

## Next engineering increments (separate approvals)

1. Inventory the real CyberPanel API contract and version without touching core files.
2. Create an adapter interface for **read-only** sites/SSL/backup metadata, with
   explicit allowlisted actions and a mock adapter for contract tests.
3. Add identity provider session verification, scoped RBAC per operation, audit logs
   with secret redaction, rate limits, and CSRF prevention for any browser access.
4. Build a migration/upgrade compatibility matrix; no direct modification of
   upstream CyberPanel core. Add safe backup/rollback runbooks.
5. Introduce queued write operations only after separate staging acceptance and
   owner approval, with idempotency and two-step confirmation.
6. Implement web UI for `panel.hooshedigital.ir` only after authoritative
   session and permission boundaries are defined.

No production deployment, server changes, or administrative actions are
authorized by this proof of concept.
