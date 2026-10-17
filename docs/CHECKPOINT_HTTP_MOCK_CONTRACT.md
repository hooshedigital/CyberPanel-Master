# External checkpoint HTTP mock — offline contract

This document accompanies an isolated Python 3.10+ WSGI prototype for the CyberPanel independent control plane. The runnable source and tests are distributed separately as a local bundle until executable-file writes are permitted. It does not call CyberPanel, customer services, or Production.

Contract:
- GET /health returns {"status":"ok","mock":true}; this is not a storage-readiness guarantee.
- GET /v1/checkpoint requires a configured Bearer token and returns revision plus checkpoint (null initially).
- POST /v1/checkpoint requires strict JSON with expected_revision, idempotency_key and checkpoint {sequence,digest}; the digest is a 64-character lowercase SHA-256 hex string.
- 201 means committed; 200 means replay of the exact same request and key; 409 means revision/sequence conflict or reuse of an idempotency key for a different payload; 401 means unauthorized; 503 means unconfigured or unavailable.
- A POST timeout is UNKNOWN: retry with exactly the same idempotency key and payload; do not assume success or advance sequence.
- SQLite BEGIN IMMEDIATE serializes concurrent compare-and-swap writes, and idempotency records are committed atomically.
- Fail-closed validation rejects unknown fields, malformed JSON, duplicate JSON keys, oversized bodies and invalid digests. Error bodies never echo secrets.

Limitations: this SQLite mock is not WORM, tamper-evident, rollback-proof or an independent trust domain. An attacker who rolls back its entire database can also roll back its revision. A production design requires independently managed monotonic anchoring, TLS, per-service authorization, key rotation, backups, recovery testing and verified canonical audit-chain integration.

Reproduce local tests from the companion bundle: python -m unittest discover -s tests -v. No CI or Staging result should be inferred from this document. No merge or deploy is authorized.
