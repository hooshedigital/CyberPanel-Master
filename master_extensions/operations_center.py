"""Bounded, read-only operations overview for CyberPanel Master.

Existing hoosh-cyberagent is the source for agent status. No command execution,
credential exposure, heavy du scan, cleanup or backup deletion occurs in Django.
The optional root-owned snapshot collector is a separate scheduled component.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import stat
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
        if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_REPORT or st.st_size < 2:
            return {}
        # O_NOFOLLOW plus inode comparison prevents symlink swap/race in report reads.
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as handle:
            actual = os.fstat(handle.fileno())
            if (not stat.S_ISREG(actual.st_mode) or
                    (actual.st_ino, actual.st_dev) != (st.st_ino, st.st_dev)):
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


def disk_summary(usage=None, *, inode_stat=None):
    try:
        usage = shutil.disk_usage("/") if usage is None else usage
        total, used, free = (usage.total, usage.used, usage.free)
        if not all(type(v) is int and 0 <= v <= 2 ** 63 for v in (total, used, free)) or total == 0:
            return {"ready": False}
        if inode_stat is None:
            try:
                inode_stat = os.statvfs("/")
            except OSError:
                inode_stat = None
        inode_used = None
        if inode_stat is not None:
            count = getattr(inode_stat, "f_files", None)
            free_count = getattr(inode_stat, "f_ffree", None)
            if (type(count) is int and type(free_count) is int
                    and count > 0 and 0 <= free_count <= count):
                inode_used = round(100 * (count - free_count) / count, 1)
        return {"ready": True, "used_percent": round(100 * used / total, 1),
                "total_gib": _gib(total), "used_gib": _gib(used),
                "free_gib": _gib(free), "inode_used_percent": inode_used}
    except (OSError, AttributeError, ValueError):
        return {"ready": False}



def memory_summary(meminfo: str | None = None) -> dict:
    """Inexpensive Linux memory + swap gauges, without shell or processes."""
    if meminfo is None:
        try:
            with Path("/proc/meminfo").open("r", encoding="ascii") as handle:
                meminfo = handle.read(16385)
        except (OSError, UnicodeError):
            return {"ready": False}
    if not isinstance(meminfo, str) or len(meminfo) > 16384:
        return {"ready": False}
    values = {}
    for line in meminfo.splitlines():
        if ":" not in line:
            continue
        key, text = line.split(":", 1)
        if key not in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
            continue
        tokens = text.strip().split()
        if len(tokens) != 2 or tokens[1] != "kB" or not tokens[0].isdigit():
            return {"ready": False}
        value = int(tokens[0])
        if not 0 <= value <= 2 ** 40:
            return {"ready": False}
        values[key] = value
    required = ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree")
    if not all(key in values for key in required):
        return {"ready": False}
    total, available = values["MemTotal"], values["MemAvailable"]
    swap_total, swap_free = values["SwapTotal"], values["SwapFree"]
    if total == 0 or available > total or swap_free > swap_total:
        return {"ready": False}
    return {
        "ready": True,
        "ram_available_gib": round(available / 1024 ** 2, 2),
        "ram_used_percent": round(100 * (total - available) / total, 1),
        "swap_used_gib": round((swap_total - swap_free) / 1024 ** 2, 2),
        "swap_total_gib": round(swap_total / 1024 ** 2, 2),
    }

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
        scanned = group.get("scanned", 0)
        if type(scanned) is not int or not 0 <= scanned <= 1000000:
            scanned = 0
        output.append({"id": key, "name": LABELS[lang][key],
                       "size_gib": _gib(count), "complete": complete,
                       "measured": bool(complete or scanned > 0)})
    return {"ready": bool(output), "groups": output, "partial": partial}


def agent_summary(*, report: dict | None = None, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    report = _read_bounded_json(AGENT_STATUS) if report is None else report
    # Source schema must be observed and timestamped; never claim live from file existence.
    stamp = report.get("generated_utc") or report.get("updated_utc") or report.get("at_utc")
    alive = _fresh(stamp, now, seconds=240)
    # Existing hoosh-cyberagent 0.9.0 publishes updated_at_unix, NOT ISO.
    epoch = report.get("updated_at_unix")
    if type(epoch) in (int, float) and 0 < epoch < 2 ** 35:
        alive = alive or 0 <= now.timestamp() - epoch <= 240
        if alive and not stamp:
            stamp = datetime.fromtimestamp(epoch, timezone.utc).isoformat()
    reported = report.get("status") if alive else None
    if reported not in ("ok", "warning", "critical", "unknown"):
        reported = None
    checks_total = report.get("checks_total")
    if type(checks_total) is not int or not 0 <= checks_total <= 10000:
        checks_total = None
    version = report.get("version")
    if not isinstance(version, str) or len(version) > 32 or not version.replace(".", "").replace("-", "").replace("+", "").isalnum():
        version = None
    return {
        "fresh": bool(alive),
        "version": version if alive else None,
        "updated": stamp if alive else None,
        "status": reported,
        "checks_total": checks_total if alive else None,
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
        complete = entry.get("complete")
        result.append({"id": category, "size_gib": _gib(amount), "count": number,
                       "complete": complete is True})
    return {"ready": bool(result), "items": result,
            "total_gib": round(sum(x["size_gib"] for x in result), 2)}


def operations_context(lang: str, *, disk=None, storage=None, agent=None, cleanup=None) -> dict:
    if lang not in LABELS:
        raise ValueError("unsupported language")
    return {
        "disk": disk_summary(disk),
        "memory": memory_summary(),
        "storage": breakdown(lang, report=storage),
        "agent": agent_summary(report=agent),
        "cleanup": cleanup_summary(report=cleanup),
    }
