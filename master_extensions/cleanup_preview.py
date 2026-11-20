"""Conservative *preview only* of potentially disposable cache artifacts.

No deletion, truncation, sudo, Docker prune or journal vacuum. Old backups,
databases, customer sites and Docker volumes are never deletion candidates.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import time


@dataclass(frozen=True)
class CleanupPolicy:
    category: str
    root: Path
    suffix: str
    min_age_days: int


# Administrator must review all candidates even inside these restricted roots.
POLICIES = (
    CleanupPolicy("apt_archives", Path("/var/cache/apt/archives"), ".deb", 30),
    CleanupPolicy("hoosh_temp", Path("/var/tmp/hoosh-cybermaster"), ".tmp", 14),
)


def preview(policy: CleanupPolicy, *, now_epoch: float | None = None,
            max_entries: int = 2000, max_seconds: float = 2.0) -> dict:
    """Report file counts/sizes, never filenames or file contents.

    Deliberately nonrecursive. Skips symlinks, hardlinks and mount boundaries.
    """
    if policy.category not in ("apt_archives", "hoosh_temp"):
        raise ValueError("category not allowed")
    if not policy.suffix or policy.min_age_days < 7 or max_entries < 1 or max_seconds <= 0:
        raise ValueError("invalid conservative policy")
    now_epoch = time.time() if now_epoch is None else now_epoch
    count, total, complete, seen = 0, 0, True, 0
    end = time.monotonic() + max_seconds
    fd = None
    try:
        fd = os.open(policy.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        device = os.fstat(fd).st_dev
        with os.scandir(fd) as entries:
            for entry in entries:
                if seen >= max_entries or time.monotonic() >= end:
                    complete = False
                    break
                seen += 1
                try:
                    s = entry.stat(follow_symlinks=False)
                    if (s.st_dev != device or not stat.S_ISREG(s.st_mode)
                            or s.st_nlink != 1 or not entry.name.endswith(policy.suffix)):
                        continue
                    age = now_epoch - s.st_mtime
                    if age >= policy.min_age_days * 86400:
                        count += 1
                        total += max(0, int(s.st_blocks)) * 512
                except OSError:
                    complete = False
    except OSError:
        complete = False
    finally:
        if fd is not None:
            os.close(fd)
    return {"category": policy.category, "allocated_bytes": total,
            "count": count, "complete": complete,
            "action": "review_only", "deleted": False}


def snapshot(policies=POLICIES, *, now=None, scan=preview) -> dict:
    now = now or datetime.now(timezone.utc)
    items = []
    for policy in policies:
        items.append(scan(policy))
    return {"schema": 1, "generated_utc": now.isoformat(),
            "items": items, "execution_enabled": False}


if __name__ == "__main__":
    print(json.dumps(snapshot(), ensure_ascii=False, separators=(",", ":")))
