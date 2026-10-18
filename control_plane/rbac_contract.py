"""Offline, read-only RBAC decision and redacted audit contract.

This module is deliberately NOT wired into the CyberPanel WSGI app. It does not
authenticate callers or connect to CyberPanel. An identity provider must supply
trusted Principal objects before a future integration can use this policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Literal
from uuid import uuid4

READ_OPERATIONS = frozenset({
    "sites.inventory.read", "ssl.inventory.read", "backups.inventory.read",
    "audit.events.read",
})
ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "viewer": frozenset({"sites.inventory.read", "ssl.inventory.read", "backups.inventory.read"}),
    "auditor": frozenset({"audit.events.read"}),
    "operator": READ_OPERATIONS,
}
REASONS = frozenset({
    "allowed", "no_principal", "inactive_principal", "invalid_context",
    "tenant_mismatch", "unsupported_operation", "role_denied",
})


@dataclass(frozen=True, slots=True)
class Principal:
    """Trusted, server-resolved identity; never construct from raw HTTP headers."""

    role: str
    tenant_ref: str
    active: bool = True


@dataclass(frozen=True, slots=True)
class Decision:
    allowed: bool
    reason: str
    operation: str
    role: str
    tenant_scope: Literal["matched", "mismatch", "unknown"]


def _safe_role(principal: object) -> str:
    if type(principal) is Principal and type(principal.role) is str:
        if principal.role in ROLE_PERMISSIONS:
            return principal.role
    return "unknown"


def authorize(principal: Principal | None, operation: str, resource_tenant_ref: str) -> Decision:
    """Default-deny; all writes and cross-tenant reads are denied."""
    role = _safe_role(principal)
    safe_op = operation if type(operation) is str and operation in READ_OPERATIONS else "unknown"

    def result(allowed: bool, reason: str, scope: Literal["matched", "mismatch", "unknown"] = "unknown") -> Decision:
        return Decision(allowed, reason, safe_op, role, scope)

    if type(principal) is not Principal:
        return result(False, "no_principal")
    if type(principal.active) is not bool or not principal.active:
        return result(False, "inactive_principal")
    if (type(principal.tenant_ref) is not str or not principal.tenant_ref
            or type(resource_tenant_ref) is not str or not resource_tenant_ref):
        return result(False, "invalid_context")
    if principal.tenant_ref != resource_tenant_ref:
        return result(False, "tenant_mismatch", "mismatch")
    if safe_op == "unknown":
        return result(False, "unsupported_operation", "matched")
    if role == "unknown" or safe_op not in ROLE_PERMISSIONS[role]:
        return result(False, "role_denied", "matched")
    return result(True, "allowed", "matched")


def audit_record(decision: Decision, *, now: datetime | None = None, event_id: str | None = None) -> dict:
    """Return a minimal audit event without user or secret data."""
    if type(decision) is not Decision or decision.reason not in REASONS:
        raise ValueError("invalid decision")
    instant = now if now is not None else datetime.now(timezone.utc)
    if not isinstance(instant, datetime) or instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("timestamp must be timezone aware")
    identifier = str(uuid4()) if event_id is None else event_id
    if type(identifier) is not str or not identifier or len(identifier) > 64 or not identifier.isascii() or not all(c.isalnum() or c == '-' for c in identifier):
        raise ValueError("invalid event id")
    return {
        "schema_version": 1,
        "event_type": "authorization.decision",
        "event_id": identifier,
        "timestamp": instant.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "operation": decision.operation if decision.operation in READ_OPERATIONS else "unknown",
        "role": decision.role if decision.role in ROLE_PERMISSIONS else "unknown",
        "tenant_scope": decision.tenant_scope if decision.tenant_scope in ("matched", "mismatch", "unknown") else "unknown",
        "allowed": bool(decision.allowed),
        "reason": decision.reason,
    }


def audit_json_line(decision: Decision, *, now: datetime | None = None, event_id: str | None = None) -> str:
    """Deterministic JSONL serialization; no newline injection."""
    return json.dumps(audit_record(decision, now=now, event_id=event_id), sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
