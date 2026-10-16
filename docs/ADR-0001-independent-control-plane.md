# ADR-0001: Separate CyberPanel Control Plane (Proposal)

- **Status:** Proposed — documentation only; not an approved implementation or deployment.
- **Date:** 2026-10-17
- **Scope:** CyberPanel-Master infrastructure planning.
- **Owner/reviewer:** To be assigned before implementation.

## Context

CyberPanel upgrades can overwrite or conflict with changes to its core files. A separate management control plane is being considered for hosting operations, SSL visibility, monitoring and selected administrative workflows. The current repository README is a high-level roadmap; no deployed control plane, integration contract or test environment is verified here.

## Decision proposal

Build an **independent, versioned control-plane service** rather than patching CyberPanel core. Treat CyberPanel and its supported APIs as a managed system behind a narrow adapter. Begin with **read-only inventory/health/SSL status** in a disposable staging environment. Any state-changing action (e.g., account creation, certificate renewal, service restart) must be separately specified, authorized and tested before being exposed.

```text
Operator -> Identity/SSO -> Control Plane API -> Policy Engine -> Audit
                               |                   |
                               +-> Job Queue ------+-> CyberPanel Adapter -> Supported CyberPanel APIs
                               +-> Read-only Inventory/Monitoring
                               +-> Status and Alerts
```

**Non-goals for initial MVP:** replacing CyberPanel's native authentication; editing its core files; direct privileged shell execution; production deployment; automated billing/provisioning; storing provider credentials in the browser.

## Trust and authorization boundaries

1. **Browser -> API:** Treat all browser input as untrusted; use server-side authentication and authorization. Do not rely on hidden UI buttons as access control.
2. **Identity -> policy:** Define a role/action/resource matrix before implementation. Start with Viewer (read-only) and Operator (limited, explicitly approved operations); Administrator is not a universal bypass.
3. **Control plane -> CyberPanel:** Prefer documented supported APIs. Keep service credentials in a secret manager, never Git, frontend bundles, logs or client-side storage.
4. **Mutations:** Deny by default; use short-lived, scoped service identity; require explicit operator intent, input validation, idempotency key where appropriate, and auditable correlation IDs. High-impact actions require step-up approval.
5. **Job execution:** Queue potentially slow operations; bound concurrency, timeout and retries. Do not retry non-idempotent actions blindly. Keep a clear job status and failure reason.
6. **Network:** Restrict allowed hosts and ports to an approved inventory; prevent arbitrary URL fetch/SSRF and shell command construction from user input.
7. **Logging:** Log who/what/when/outcome without session tokens, passwords, private keys or raw customer records. Establish retention and access policy before collecting operational data.
8. **Tenant isolation:** If multiple customer tenants are supported, enforce tenant ownership at the API/data layer and test cross-tenant denial.
9. **Updates:** Control plane must survive a CyberPanel upgrade without relying on undocumented internals; test the adapter against a version matrix.

## Candidate MVP read-only API (not yet implemented)

| Endpoint | Purpose | Required permission |
|---|---|---|
| `GET /health` | Control plane liveness/readiness | internal monitoring |
| `GET /v1/servers` | Sanitized server inventory | `servers:read` |
| `GET /v1/servers/{id}/status` | Health and version | `servers:read` |
| `GET /v1/certificates` | Certificate metadata and expiration only | `certificates:read` |
| `GET /v1/audit-events` | Filtered audit events | `audit:read` |

Use pagination and bounded filters for list endpoints. Avoid returning private key material, access tokens, customer secrets, or unrestricted server logs.

## Threat model and validation matrix

| ID | Risk | Required evidence before MVP acceptance |
|---|---|---|
| CP-01 | Unauthorized API access | 401/403 cases for missing/invalid identity and denied actions |
| CP-02 | Role escalation | Negative tests for Viewer -> Operator/Admin operations |
| CP-03 | Cross-tenant access | Cross-tenant read/write denial if tenancy exists |
| CP-04 | SSRF / arbitrary host | Allowlist and malformed URL negative tests |
| CP-05 | Secret leakage | Redacted logs, response bodies and repository secret scan |
| CP-06 | Unsafe retries | Duplicate command/idempotency and timeout tests |
| CP-07 | Upgrade breakage | Staging compatibility matrix against supported CyberPanel versions |
| CP-08 | Disaster recovery | Verified backup and restore, rollback drill in staging |
| CP-09 | Misleading monitoring | Liveness/readiness distinction and degraded-state tests |
| CP-10 | Excessive privileges | Minimal service account permissions verified |

## Milestones and release gates

1. **Inventory:** Verify actual CyberPanel version, available documented APIs, staging environment, authentication method and repo ownership; record versioned evidence.
2. **Design review:** Confirm the API contract, threat model, role matrix, data retention and supported upgrade versions; record an approved ADR.
3. **Read-only MVP:** Implement on a feature branch with synthetic fixtures, mock adapter, unit/integration tests and CI; produce a draft PR.
4. **Staging verification:** Run security, permission, upgrade-compatibility and failure-injection tests; attach sanitized logs with exact commit SHA and commands.
5. **Release decision:** Require backup/restore rehearsal, rollback plan, CI success and explicit deployment approval. Do not infer readiness from this ADR.

## Alternatives considered

- **Patch CyberPanel core:** Rejected as default due to update conflicts and hard-to-audit privilege boundaries.
- **Direct browser-to-CyberPanel API:** Rejected because it risks exposing privileged credentials and bypassing centralized authorization/audit.
- **Independent read-only adapter:** Preferred first step; smallest security and operational blast radius.

## Evidence status

- Architecture design: **PROPOSED / NOT IMPLEMENTED**
- CI/application tests: **BLOCKED** — no control-plane implementation or staging target identified
- Production impact: **NONE** — this ADR changes documentation only

**Next action:** Verify the canonical CyberPanel API and a non-production instance, then review this ADR and implement only the read-only contract in a new, tested branch.
