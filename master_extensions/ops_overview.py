"""Safe read-only operations presentation for CyberPanel Master.

The web worker never walks the filesystem, executes shell commands, deletes
cache, moves files, or invokes the agent. It consumes bounded, fresh, prebuilt
telemetry and renders only vetted aggregate metrics.
"""
from __future__ import annotations

import math
from typing import Any

DISK_CATEGORIES = (
    "websites", "databases", "backups", "logs", "containers",
    "cache", "mail", "system", "other",
)
AGENT_STATES = ("idle", "busy", "waiting_approval", "unverified", "offline")
MAX_BYTES = 2**63 - 1


def _bounded_int(value: Any) -> int | None:
    if type(value) is int and 0 <= value <= MAX_BYTES:
        return value
    return None


def _safe_pct(value: Any) -> float | None:
    if type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 100:
        return round(float(value), 1)
    return None


def disk_overview(report: object) -> dict:
    """Never expose raw paths or untrusted strings from the telemetry payload."""
    result = {"verified": False, "used_pct": None, "free_gb": None,
              "total_gb": None, "categories": []}
    if not isinstance(report, dict) or report.get("schema") != 1:
        return result
    total = _bounded_int(report.get("total_bytes"))
    used = _bounded_int(report.get("used_bytes"))
    free = _bounded_int(report.get("available_bytes"))
    if total is None or used is None or free is None or not total or used > total or free > total:
        return result
    result.update(verified=True, used_pct=round(used / total * 100, 1),
                  free_gb=round(free / 10**9, 2), total_gb=round(total / 10**9, 2))
    items = report.get("categories", {})
    if isinstance(items, dict):
        for key in DISK_CATEGORIES:
            size = _bounded_int(items.get(key))
            if size is not None:
                result["categories"].append({"key": key, "size_gb": round(size / 10**9, 2)})
    return result


def cleanup_candidates(report: object) -> list[dict]:
    """Candidate summaries only; no delete buttons or filesystem target paths."""
    if not isinstance(report, dict) or report.get("schema") != 1:
        return []
    raw = report.get("candidates", [])
    if not isinstance(raw, list):
        return []
    allowed = {"apt_download_cache", "journal_archives", "old_temp_files",
               "application_cache", "unused_build_artifacts"}
    results = []
    seen = set()
    for item in raw[:25]:
        if not isinstance(item, dict):
            continue
        key = item.get("kind")
        size = _bounded_int(item.get("reclaimable_bytes"))
        if not isinstance(key, str) or key not in allowed or key in seen or size is None:
            continue
        seen.add(key)
        results.append({"kind": key, "reclaimable_gb": round(size / 10**9, 2),
                        "requires_review": True})
    return results


def agent_overview(report: object) -> dict:
    """Never surface arbitrary agent output, prompts, shell text or credentials."""
    result = {"verified": False, "state": "unverified", "pending": None,
              "completed": None, "failed": None}
    if not isinstance(report, dict) or report.get("schema") != 1:
        return result
    state = report.get("state")
    if state not in AGENT_STATES:
        return result
    result["verified"] = True
    result["state"] = state
    for name in ("pending", "completed", "failed"):
        value = _bounded_int(report.get(name))
        if value is not None and value <= 1000000:
            result[name] = value
    return result
