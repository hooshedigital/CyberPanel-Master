# Offline SQLite audit sink contract

This branch proposes an isolated local SQLite audit sink for the tenant inventory prototype. No CyberPanel core integration, production connection, customer data, or deployment.

The local prototype uses an allowlisted four-field event (timestamp, decision, resource, role), owner-only database permissions, transactional commits, and fail-closed exceptions. Local tests cover SQLite locking, rollback after process exit, concurrency, redaction, and persistence after restart.

Integration is blocked until the earlier tenant audit Python module is committed and its canonical interface reviewed. Do not deploy this standalone code. Run the unit tests on the actual checkout before review.
