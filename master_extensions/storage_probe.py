"""Optional bounded read-only Linux disk scanner.

Run in a separately resource-limited scheduled job, NEVER on an HTTP request.
Output is a sanitized snapshot only. It contains no filenames, contents or
secrets and never deletes anything. No installation or timer is enabled here.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import time

# Explicit scope; never include credentials or database files by default.
ROOTS = (
    ("logs", "/var/log"),
    ("cache", "/var/cache"),
    ("containers", "/var/lib/docker"),
    ("backup", "/home/backup"),
)
MAX_ENTRIES_PER_ROOT = 20000
MAX_SECONDS_PER_ROOT = 3.0
MAX_DEPTH = 5


def scan_tree(root: Path | str, *, max_entries=MAX_ENTRIES_PER_ROOT,
              max_seconds=MAX_SECONDS_PER_ROOT, max_depth=MAX_DEPTH) -> dict:
    """Bounded st_blocks estimate; no symlink following or crossing mount points.

    Only a complete=true estimate is comparable to a full directory size.
    Does not equate filesystem used space with sum of scan roots.
    """
    root = Path(root)
    try:
        st = root.lstat()
        if not stat.S_ISDIR(st.st_mode):
            return {"allocated_bytes": 0, "complete": False, "scanned": 0}
        device = st.st_dev
    except OSError:
        return {"allocated_bytes": 0, "complete": False, "scanned": 0}
    if max_entries < 1 or max_seconds <= 0 or max_depth < 1:
        raise ValueError("invalid bounds")
    end = time.monotonic() + max_seconds
    queue = [(root, 0)]
    scanned = 0
    total = 0
    complete = True
    visited = set()
    while queue:
        if scanned >= max_entries or time.monotonic() >= end:
            complete = False
            break
        directory, depth = queue.pop()
        try:
            info = directory.lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_dev != device:
                complete = False
                continue
            inode = (info.st_dev, info.st_ino)
            if inode in visited:
                continue
            visited.add(inode)
            with os.scandir(directory) as entries:
                for entry in entries:
                    if scanned >= max_entries or time.monotonic() >= end:
                        complete = False
                        break
                    scanned += 1
                    try:
                        item = entry.stat(follow_symlinks=False)
                        if item.st_dev != device:
                            complete = False
                            continue
                        if stat.S_ISDIR(item.st_mode):
                            if depth + 1 < max_depth:
                                queue.append((Path(entry.path), depth + 1))
                            else:
                                complete = False
                        elif stat.S_ISREG(item.st_mode):
                            total += max(0, int(item.st_blocks)) * 512
                        # Symbolic links, devices and sockets are ignored.
                    except OSError:
                        complete = False
        except OSError:
            complete = False
    return {"allocated_bytes": total, "complete": complete,
            "scanned": scanned}


def snapshot(roots=ROOTS, *, scan=scan_tree, now=None) -> dict:
    now = now or datetime.now(timezone.utc)
    groups = []
    for category, root in roots:
        if category not in ("logs", "cache", "containers", "backup", "websites", "other"):
            raise ValueError("invalid category")
        results = scan(root)
        groups.append({"category": category,
                       "allocated_bytes": results["allocated_bytes"],
                       "complete": results["complete"]})
    return {"schema": 1, "generated_utc": now.isoformat(), "groups": groups}


if __name__ == "__main__":
    print(json.dumps(snapshot(), ensure_ascii=False, separators=(",", ":")))
