"""Fail-closed, root-owned telemetry reader shared by Master and Smart Backup.

Only approved compact JSON names are read. Never follows a symbolic link,
never exposes file paths, and rejects stale/untrusted reports. No subprocess.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat

ROOT_DIR = Path("/var/lib/hoosh-cyber-agent")
EXPECTED_UID = 0
MAX_REPORT_BYTES = 65536
ALLOWED_REPORTS = frozenset({
    "disk-inventory.json", "cleanup-candidates.json", "agent-operations.json",
})


def read_fresh_report(name: str, *, max_age: int = 1800) -> dict:
    if (not isinstance(name, str) or name not in ALLOWED_REPORTS
            or type(max_age) is not int or not 1 <= max_age <= 86400):
        return {}
    try:
        base = ROOT_DIR.lstat()
        if (not stat.S_ISDIR(base.st_mode) or base.st_uid != EXPECTED_UID
                or base.st_mode & 0o022):
            return {}
        fd = os.open(str(ROOT_DIR / name),
                     os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            info = os.fstat(fd)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != EXPECTED_UID
                    or info.st_mode & 0o022 or not 2 <= info.st_size <= MAX_REPORT_BYTES):
                return {}
            with os.fdopen(fd, "rb", closefd=False) as data_file:
                raw = data_file.read(MAX_REPORT_BYTES + 1)
            if len(raw) > MAX_REPORT_BYTES:
                return {}
        finally:
            os.close(fd)
        report = json.loads(raw)
        if not isinstance(report, dict) or report.get("schema") != 1:
            return {}
        stamp = datetime.fromisoformat(report.get("generated_utc", ""))
        if stamp.tzinfo is None:
            return {}
        age = (datetime.now(timezone.utc) - stamp).total_seconds()
        return report if 0 <= age <= max_age else {}
    except (OSError, ValueError, UnicodeError, TypeError, OverflowError):
        return {}
