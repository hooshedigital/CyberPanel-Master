"""Bounded, metadata-only inventory producer for CyberPanel Master.

Run ONLY as a separately deployed, root-owned systemd oneshot, never from
Django or an HTTP endpoint. This module has no delete/move/execution API.
All results are aggregates; filenames and filesystem paths are never emitted.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import time
from datetime import datetime, timezone

from master_extensions.bridge import emit

# Root-owned source configuration; never accept web/client-supplied paths.
CATEGORY_ROOTS = {
    "websites": ("/home",),
    "databases": ("/var/lib/mysql", "/var/lib/postgresql"),
    "backups": ("/home/backup", "/var/backups", "/backup"),
    "logs": ("/var/log",),
    "containers": ("/var/lib/docker",),
    "cache": ("/var/cache",),
    "mail": ("/var/mail", "/var/spool/mail"),
    "system": ("/usr/local/CyberCP", "/usr/local/lsws"),
}
MAX_ENTRIES_PER_ROOT = 3000
MAX_SCAN_SECONDS = 6
MAX_CANDIDATE_ENTRIES = 2500
MIB = 1024 * 1024


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _child_of(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip("/") + "/")


def _mountpoints() -> set[str] | None:
    """Read mount boundaries; do not silently count nested overlay mounts."""
    mounts = set()
    try:
        with open("/proc/self/mountinfo", encoding="utf-8") as fh:
            for line in fh:
                fields = line.split(" - ", 1)[0].split()
                if len(fields) < 5:
                    continue
                escaped = fields[4]
                name = re.sub(r"\\([0-7]{3})",
                              lambda m: chr(int(m.group(1), 8)), escaped)
                mounts.add(os.path.normpath(name))
    except OSError:
        return None
    return mounts


def _bytes_used(st) -> int:
    # Allocated blocks, not logical size (handles sparse files).
    return max(0, int(st.st_blocks) * 512)


def _scan(root: str, *, exclude: set[str], mounts: set[str],
          device: int, seen_inodes: set[tuple[int, int]],
          deadline: float, limit: int) -> tuple[int, bool, int]:
    """Physical block estimate. Stops on budget; never follows symlinks."""
    try:
        root_st = os.lstat(root)
        if not stat.S_ISDIR(root_st.st_mode) or root_st.st_dev != device:
            return 0, False, 0
    except OSError:
        return 0, False, 0
    size = 0
    count = 0
    complete = True
    stack = [root]
    while stack:
        if count >= limit or time.monotonic() >= deadline:
            complete = False
            break
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for item in entries:
                    if count >= limit or time.monotonic() >= deadline:
                        complete = False
                        break
                    count += 1
                    name = item.path
                    if name in mounts or any(_child_of(name, e) for e in exclude):
                        continue
                    try:
                        st = item.stat(follow_symlinks=False)
                    except OSError:
                        complete = False
                        continue
                    if st.st_dev != device:
                        continue
                    if stat.S_ISDIR(st.st_mode):
                        stack.append(name)
                    elif stat.S_ISREG(st.st_mode):
                        key = (st.st_dev, st.st_ino)
                        if key not in seen_inodes:
                            seen_inodes.add(key)
                            size += _bytes_used(st)
        except OSError:
            complete = False
        if not complete:
            break
    return size, complete, count


def collect_disk(*, roots=None, deadline_seconds=MAX_SCAN_SECONDS,
                 mounts=None) -> dict:
    """Accurate root statvfs + *sampled* directory estimates (not a full du)."""
    usage = os.statvfs("/")
    total = usage.f_blocks * usage.f_frsize
    used = (usage.f_blocks - usage.f_bfree) * usage.f_frsize
    available = usage.f_bavail * usage.f_frsize
    inode_pct = (
        round((usage.f_files - usage.f_ffree) * 100 / usage.f_files, 1)
        if usage.f_files else None
    )
    result = {
        "schema": 1, "generated_utc": _now(),
        "total_bytes": total, "used_bytes": used,
        "available_bytes": available, "inode_used_pct": inode_pct,
        "categories": {}, "category_scans": {}, "coverage": "sampled",
    }
    # Can't safely attribute nested mounts if mountinfo is inaccessible.
    if mounts is None:
        mounts = _mountpoints()
    if mounts is None:
        return result
    if roots is None:
        roots = CATEGORY_ROOTS
    all_roots = {os.path.normpath(r) for values in roots.values() for r in values}
    seen_inodes: set[tuple[int, int]] = set()
    root_device = os.stat("/").st_dev
    deadline = time.monotonic() + min(max(0, deadline_seconds), 15)
    for category, paths in roots.items():
        if category not in CATEGORY_ROOTS:
            continue
        category_size = 0
        scanned = False
        complete = True
        entries = 0
        for raw in paths:
            path = os.path.normpath(raw)
            if not os.path.isabs(path) or path == "/":
                complete = False
                continue
            if not os.path.isdir(path) or os.path.islink(path):
                # Don't misrepresent a missing/unreadable directory as zero.
                complete = False
                continue
            # A more-specific category root owns this subtree, not its parent.
            exclude = {p for p in all_roots if p != path and _child_of(p, path)}
            size, done, count = _scan(
                path, exclude=exclude, mounts=mounts,
                device=root_device, seen_inodes=seen_inodes,
                deadline=deadline, limit=MAX_ENTRIES_PER_ROOT,
            )
            scanned = scanned or bool(count or done)
            category_size += size
            complete = complete and done
            entries += count
        if scanned:
            result["categories"][category] = category_size
            result["category_scans"][category] = {
                "complete": complete, "entries_scanned": entries,
            }
    return result


def _candidate_tree(root: str, *, extension: str | None,
                    min_age_days: int, archive: bool,
                    now: float, deadline: float, max_entries: int,
                    mounts: set[str], device: int) -> tuple[int, bool]:
    """Potentially reclaimable allocated bytes, never a removal plan."""
    try:
        root_st = os.lstat(root)
        if not stat.S_ISDIR(root_st.st_mode) or root_st.st_dev != device:
            return 0, False
    except OSError:
        return 0, False
    total = 0
    entries_seen = 0
    complete = True
    visited: set[tuple[int, int]] = set()
    stack = [root]
    while stack:
        if entries_seen >= max_entries or time.monotonic() >= deadline:
            complete = False
            break
        directory = stack.pop()
        try:
            with os.scandir(directory) as children:
                for entry in children:
                    if entries_seen >= max_entries or time.monotonic() >= deadline:
                        complete = False
                        break
                    entries_seen += 1
                    if entry.path in mounts:
                        continue
                    try:
                        st = entry.stat(follow_symlinks=False)
                    except OSError:
                        complete = False
                        continue
                    if st.st_dev != device:
                        continue
                    if stat.S_ISDIR(st.st_mode):
                        stack.append(entry.path)
                        continue
                    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
                        continue
                    if now - st.st_mtime < min_age_days * 86400:
                        continue
                    if archive:
                        # Never count active system.journal/user-*.journal.
                        if not (entry.name.endswith(".journal~") or
                                ("@" in entry.name and entry.name.endswith(".journal"))):
                            continue
                    elif extension and not entry.name.endswith(extension):
                        continue
                    key = (st.st_dev, st.st_ino)
                    if key not in visited:
                        visited.add(key)
                        total += _bytes_used(st)
        except OSError:
            complete = False
        if not complete:
            break
    return total, complete


def collect_cleanup(*, paths=None, mounts=None,
                    deadline_seconds=MAX_SCAN_SECONDS) -> dict:
    """Dry-run estimates only. Never enumerates paths in the JSON result."""
    if paths is None:
        paths = {
            "apt_download_cache": ("/var/cache/apt/archives", ".deb", 1, False),
            "journal_archives": ("/var/log/journal", None, 30, True),
            "old_temp_files": ("/var/tmp", None, 30, False),
        }
    report = {"schema": 1, "generated_utc": _now(), "candidates": [],
              "analysis_complete": True}
    if mounts is None:
        mounts = _mountpoints()
    if mounts is None:
        report["analysis_complete"] = False
        return report
    deadline = time.monotonic() + min(max(0, deadline_seconds), 15)
    device = os.stat("/").st_dev
    clock = time.time()
    for kind, (root, ext, min_age, archive) in paths.items():
        if kind not in ("apt_download_cache", "journal_archives", "old_temp_files"):
            continue
        amount, done = _candidate_tree(
            root, extension=ext, min_age_days=min_age,
            archive=archive, now=clock, deadline=deadline,
            max_entries=MAX_CANDIDATE_ENTRIES,
            mounts=mounts, device=device,
        )
        report["analysis_complete"] = report["analysis_complete"] and done
        if amount:
            report["candidates"].append(
                {"kind": kind, "reclaimable_bytes": amount,
                 "requires_review": True, "estimate_only": True}
            )
    return report


def main() -> None:
    # Existing bridge.emit checks root-owned state and publishes atomically.
    emit("disk-inventory.json", collect_disk())
    emit("cleanup-candidates.json", collect_cleanup())


if __name__ == "__main__":
    main()
