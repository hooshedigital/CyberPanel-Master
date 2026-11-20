"""Bounded, read-only operations overview for CyberPanel Master.

Existing hoosh-cyberagent is the source for agent status. No command execution,
credential exposure, heavy du scan, cleanup or backup deletion occurs in Django.
The optional root-owned snapshot collector is a separate scheduled component.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

AGENT_STATUS = Path("/run/hoosh-cyberagent/status.json")
STORAGE_REPORT = Path("/var/lib/hoosh-cybermaster/storage-report.json")
CLEANUP_REPORT = Path("/var/lib/hoosh-cybermaster/cleanup-preview.json")
MAX_REPORT = 64 * 1024
AGE_SECONDS = 900
CATEGORIES = ("logs", "cache", "containers", "backup", "websites", "other")
LABELS = {
    "en": {
        "logs": "Logs", "cache": "Caches", "containers": "Containers",
        "backup": "Backups", "websites": "Websites", "other": "Other",
    },
    "fa": {
        "logs": "لاگ‌ها", "cache": "کش‌ها", "containers": "کانتینرها",
        "backup": "بکاپ‌ها", "websites": "وب‌سایت‌ها", "other": "سایر",
    },
}


def _read_bounded_json(path: Path) -> dict:
    """Never follow a symlink. Ignore untrusted oversized, missing or malformed reports."""
    try:
        st = path.lstat()
        import stat
        if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_REPORT or st.st_size < 2:
            return {}
        with path.open("rb") as handle:
            # A different file from a racing rename is not blindly accepted.
            current = handle.fileno()
            actual = __import__("os").fstat(current)
            if (actual.st_ino, actual.st_dev) != (st.st_ino, st.st_dev):
                return {}
            raw = handle.read(MAX_REPORT + 1)
        if len(raw) > MAX_REPORT:
            return {}
        result = json.loads(raw)
        return result if isinstance(result, dict) else {}
    except (OSError, TypeError, ValueError, UnicodeError):
        return {}


def _fresh(value: object, now: datetime, seconds: int = AGE_SECONDS) -> bool:
    if not isinstance(value, str) or len(value) > 64:
        return False
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if t.tzinfo is None:
            return False
        delta = (now - t.astimezone(timezone.utc)).total_seconds()
        return 0 <= delta <= seconds
    except (ValueError, OverflowError):
        return False


def _gib(n: int) -> float:
    return round(n / (1024 ** 3), 2)


def disk_summary(usage=None):
    try:
        usage = shutil.disk_usage("/") if usage is None else usage
        total, used, free = (usage.total, usage.used, usage.free)
        if not all(type(v) is int and 0 <= v <= 2 ** 63 for v in (total, used, free)) or total == 0:
            return {"ready": False}
        return {"ready": True, "used_percent": round(100 * used / total, 1),
                "total_gib": _gib(total), "used_gib": _gib(used),
                "free_gib": _gib(free)}
    except (OSError, AttributeError, ValueError):
        return {"ready": False}


def breakdown(lang: str, *, report: dict | None = None, now: datetime | None = None) -> dict:
    if lang not in LABELS:
        raise ValueError("unsupported language")
    now = now or datetime.now(timezone.utc)
    report = _read_bounded_json(STORAGE_REPORT) if report is None else report
    if report.get("schema") != 1 or not _fresh(report.get("generated_utc"), now):
        return {"ready": False, "groups": [], "partial": False}
    groups = report.get("groups")
    if not isinstance(groups, list) or len(groups) > 32:
        return {"ready": False, "groups": [], "partial": False}
    output = []
    seen = set()
    partial = False
    for group in groups:
        if not isinstance(group, dict):
            continue
        key, count = group.get("category"), group.get("allocated_bytes")
        complete = group.get("complete")
        if key not in CATEGORIES or key in seen or type(count) is not int or not 0 <= count <= 2 ** 63:
            continue
        if type(complete) is not bool:
            continue
        seen.add(key)
        partial |= not complete
        output.append({"id": key, "name": LABELS[lang][key],
                       "size_gib": _gib(count), "complete": complete})
    return {"ready": bool(output), "groups": output, "partial": partial}


def agent_summary(*, report: dict | None = None, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    report = _read_bounded_json(AGENT_STATUS) if report is None else report
    # Source schema must be observed and timestamped; never claim live from file existence.
    stamp = report.get("generated_utc") or report.get("updated_utc") or report.get("at_utc")
    alive = _fresh(stamp, now, seconds=240)
    version = report.get("version")
    if not isinstance(version, str) or len(version) > 32 or not version.replace(".", "").replace("-", "").replace("+", "").isalnum():
        version = None
    return {
        "fresh": bool(alive),
        "version": version,
        "updated": stamp if alive else None,
        # A fresh heartbeat is not evidence that command execution is authorized.
        "operations_enabled": False,
    }


def cleanup_summary(*, report: dict | None = None, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    report = _read_bounded_json(CLEANUP_REPORT) if report is None else report
    if report.get("schema") != 1 or not _fresh(report.get("generated_utc"), now):
        return {"ready": False, "items": [], "total_gib": 0}
    items = report.get("items")
    if not isinstance(items, list) or len(items) > 16:
        return {"ready": False, "items": [], "total_gib": 0}
    result = []
    for entry in items:
        if not isinstance(entry, dict):
            continue
        category, amount, number = entry.get("category"), entry.get("allocated_bytes"), entry.get("count")
        if (category not in ("apt_archives", "hoosh_temp")
                or type(amount) is not int or not 0 <= amount <= 2 ** 63
                or type(number) is not int or not 0 <= number <= 1000000):
            continue
        result.append({"id": category, "size_gib": _gib(amount), "count": number})
    return {"ready": bool(result), "items": result,
            "total_gib": round(sum(x["size_gib"] for x in result), 2)}


def operations_context(lang: str, *, disk=None, storage=None, agent=None, cleanup=None) -> dict:
    if lang not in LABELS:
        raise ValueError("unsupported language")
    return {
        "disk": disk_summary(disk),
        "storage": breakdown(lang, report=storage),
        "agent": agent_summary(report=agent),
        "cleanup": cleanup_summary(report=cleanup),
    }
