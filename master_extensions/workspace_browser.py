"""Read-only admin workspace browser with strict directory-fd containment.

This is NOT an unrestricted Root File Manager or a replacement for the existing
CyberPanel website File Manager. The fixed dedicated sandbox root defaults to
/var/lib/hoosh-cybermaster/workspaces; no file content, delete, edit or move
actions are offered over HTTP. Future brokered move actions require separate
owner approval, no-overwrite semantics, audit and rollback.
"""
from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import stat
from urllib.parse import quote

ROOT = Path("/var/lib/hoosh-cybermaster/workspaces")
MAX_DEPTH = 6
MAX_ITEMS = 80


def valid_relative(relative: object) -> list[str] | None:
    if not isinstance(relative, str) or len(relative) > 300:
        return None
    if not relative:
        return []
    if "\\" in relative or "\x00" in relative or relative.startswith("/"):
        return None
    parts = relative.split("/")
    if (len(parts) > MAX_DEPTH or
            any(p in ("", ".", "..") or len(p) > 100 for p in parts)):
        return None
    return parts


def browse(relative="", *, root: Path = ROOT, max_items=MAX_ITEMS) -> dict:
    parts = valid_relative(relative)
    if parts is None or not 1 <= max_items <= MAX_ITEMS:
        return {"ready": False, "error": "invalid_path", "items": []}
    if not root.is_absolute():
        return {"ready": False, "error": "invalid_root", "items": []}
    fd = None
    try:
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        root_device = os.fstat(fd).st_dev
        for part in parts:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                              dir_fd=fd)
            if os.fstat(next_fd).st_dev != root_device:
                os.close(next_fd)
                return {"ready": False, "error": "mount_boundary", "items": []}
            os.close(fd)
            fd = next_fd
        items = []
        truncated = False
        with os.scandir(fd) as entries:
            for entry in entries:
                if len(items) >= max_items:
                    truncated = True
                    break
                try:
                    info = entry.stat(follow_symlinks=False)
                    kind = ("folder" if stat.S_ISDIR(info.st_mode) else
                            "file" if stat.S_ISREG(info.st_mode) else "blocked")
                    if info.st_dev != root_device:
                        kind = "blocked"
                    if entry.name in (".", "..") or "\x00" in entry.name:
                        continue
                    path = "/".join(parts + [entry.name])
                    items.append({"name": entry.name[:120], "kind": kind,
                                  "size_bytes": info.st_size if kind == "file" else None,
                                  "href": quote(path, safe="") if kind == "folder" else ""})
                except OSError:
                    continue
        items.sort(key=lambda x: (x["kind"] != "folder", x["name"].casefold()))
        return {"ready": True, "error": None, "items": items,
                "current": "/".join(parts) or "/",
                "parent": quote("/".join(parts[:-1]), safe="") if parts else None,
                "truncated": truncated}
    except (OSError, ValueError):
        return {"ready": False, "error": "not_configured", "items": []}
    finally:
        if fd is not None:
            os.close(fd)
