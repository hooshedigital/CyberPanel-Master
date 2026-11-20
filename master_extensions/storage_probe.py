"""Optional bounded read-only Linux storage inventory collector.

Collect only from fixed, explicitly selected roots. Run as a resource-limited
non-web task, never in a Django request. No content is opened, no files are
modified or deleted, and symbolic links / mount boundaries are never followed.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import time

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
    """Return allocated-block estimate with an explicit completeness flag.

    Each traversal uses directory FDs opened with O_NOFOLLOW. Holding parent
    directories open prevents symlink swaps between path validation and scan.
    """
    if max_entries < 1 or max_seconds <= 0 or not 1 <= max_depth <= 16:
        raise ValueError("invalid bounds")
    try:
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError:
        return {"allocated_bytes": 0, "complete": False, "scanned": 0}
    start = time.monotonic()
    scanned = 0
    allocated = 0
    complete = True
    seen_dirs = set()
    dev = os.fstat(fd).st_dev

    def visit(directory_fd: int, depth: int):
        nonlocal scanned, allocated, complete
        info = os.fstat(directory_fd)
        key = (info.st_dev, info.st_ino)
        if info.st_dev != dev or key in seen_dirs:
            complete = False
            return
        seen_dirs.add(key)
        try:
            with os.scandir(directory_fd) as entries:
                for entry in entries:
                    if scanned >= max_entries or time.monotonic() - start >= max_seconds:
                        complete = False
                        break
                    scanned += 1
                    try:
                        item = os.stat(entry.name, dir_fd=directory_fd, follow_symlinks=False)
                        if item.st_dev != dev:
                            complete = False
                            continue
                        if stat.S_ISDIR(item.st_mode):
                            if depth >= max_depth:
                                complete = False
                                continue
                            try:
                                child_fd = os.open(entry.name,
                                                   os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                                   dir_fd=directory_fd)
                            except OSError:
                                complete = False
                                continue
                            try:
                                actual = os.fstat(child_fd)
                                if (actual.st_ino, actual.st_dev) != (item.st_ino, item.st_dev):
                                    complete = False
                                else:
                                    visit(child_fd, depth + 1)
                            finally:
                                os.close(child_fd)
                        elif stat.S_ISREG(item.st_mode):
                            allocated += max(0, int(item.st_blocks)) * 512
                        # Other types, including symlinks, are not traversed.
                    except OSError:
                        complete = False
        except OSError:
            complete = False

    try:
        visit(fd, 1)
    finally:
        os.close(fd)
    return {"allocated_bytes": allocated, "complete": complete, "scanned": scanned}


def snapshot(roots=ROOTS, *, scan=scan_tree, now=None) -> dict:
    now = now or datetime.now(timezone.utc)
    groups = []
    seen = set()
    for category, root in roots:
        if category not in ("logs", "cache", "containers", "backup", "websites", "other") or category in seen:
            raise ValueError("invalid or repeated category")
        seen.add(category)
        result = scan(root)
        groups.append({"category": category, "allocated_bytes": result["allocated_bytes"],
                       "complete": result["complete"]})
    return {"schema": 1, "generated_utc": now.isoformat(), "groups": groups}


if __name__ == "__main__":
    print(json.dumps(snapshot(), ensure_ascii=False, separators=(",", ":")))
