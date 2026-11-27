# Infrastructure 2027 — Preview 2

Development snapshot — 2026-11-26. This is a source release, not an installer or production-readiness certification.

## Verified infrastructure changes
- OpenLiteSpeed 1.9.4 installed; basic service and HTTP health confirmed.
- Docker Live Restore enabled with the same running daemon and container IDs.
- Docker Buildx 0.30.1 installed; default Docker builder reports BuildKit 0.26.2. No additional builder container created.
- Ubuntu HWE 6.8 kernel installed; activation requires a planned reboot. Previous kernel retained.
- Read-only infrastructure inventory now reports Buildx version.

## Release boundary
The web engine renderer and resource planner remain staging-only. Apache/FPM hybrid provisioning, active hybrid cache, real user/cart/purge tests, TLS trust, rollback and Create Website integration are not production-ready. No commercial entitlement changes. No registry credentials, server secrets or customer data are included.

Full load and functional testing deferred; minimal health checks completed. No automatic deployment or production migration is triggered by this snapshot.

See [Persian infrastructure roadmap](INFRASTRUCTURE_2027_RELEASE_CANDIDATE_FA.md).
