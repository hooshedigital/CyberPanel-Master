# Offline HMAC audit-chain contract

Scope: independent Python/SQLite CyberPanel control-plane experiment. No CyberPanel core changes, server access, customer data, or deployment.

## Security boundary

The earlier SQLite audit sink provides transactional durability, not tamper detection. The proposed local prototype computes HMAC-SHA256 over an increasing sequence, the four allowlisted event fields (timestamp, decision, resource, role), and the preceding MAC. It checks the entire chain before appending and refuses writes after detected corruption.

The runtime HMAC key MUST be provided by a secret manager and MUST NOT be stored in Git, SQLite, task trackers, or logs. An attacker with both DB and key access can forge history. Suffix deletion or database rollback cannot reliably be detected from the database alone: preserve a trusted, monotonic checkpoint outside the database and compare it during verification and writes. The prototype does not implement atomic external checkpoint persistence, key rotation, or scalable verification.

## Reproduction and acceptance

The accompanying local package includes 25 stdlib unittest cases for tampering, suffix truncation with a trusted anchor, invalid events, redaction, rollback, restart, file permissions, and concurrency; these are NOT GitHub CI results. Integration with the previous AuditEvent contract was tested offline. Do not deploy this code.

Before staging: verify canonical repository and API contract; provision independent secret storage and external checkpoints; design backup/restore and recovery for ambiguous checkpoint writes; benchmark concurrency; execute CI on the exact commit and integration tests against synthetic staging tenants. Production remains out of scope.
