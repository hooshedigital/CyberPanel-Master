"""Read-only confined file listing foundation for a future CyberPanel UI.

NOT a Django view; caller must independently enforce admin/tenant RBAC.
Root IDs map to fixed, server-side roots. User input is only a relative path.
No file contents, uploads, downloads, moves, deletes or shell access.
Uses directory file descriptors and O_NOFOLLOW to resist symlink races.
"""
from __future__ import annotations

import os
import stat
import time

# Explicit roots are not user-selectable absolute paths. These are defaults
# for a future admin-only interface, not a production enablement toggle.
ROOTS = {
    "websites": "/home",
    "backups": "/var/backups",
    "logs": "/var/log",
}
MAX_ITEMS_SCANNED = 5000
MAX_PAGE = 100
MAX_SECONDS = 2.0
DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


class FileBrowserError(ValueError):
    """Invalid request or restricted filesystem path."""


def _valid_segment(value: str) -> bool:
    return bool(value) and value not in (".", "..") and len(value) <= 255 and not any(
        ch in value for ch in ("\\", "\x00", "\n", "\r")
    )


def _segments(relative: str) -> list[str]:
    if not isinstance(relative, str) or len(relative) > 1024 or relative.startswith("/"):
        raise FileBrowserError("invalid relative path")
    if not relative:
        return []
    segments = relative.split("/")
    if len(segments) > 32 or not all(_valid_segment(s) for s in segments):
        raise FileBrowserError("invalid path segment")
    return segments


def _open_beneath(root: str, segments: list[str]) -> int:
    """Open each component relative to the previous FD, never via realpath."""
    fd = os.open(root, DIR_FLAGS)
    try:
        device = os.fstat(fd).st_dev
        for segment in segments:
            child = os.open(segment, DIR_FLAGS, dir_fd=fd)
            if os.fstat(child).st_dev != device:
                os.close(child)
                raise FileBrowserError("cross-device directory is not allowed")
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def list_directory(scope: str, relative: str = "", *, after: str = "",
                   page_size: int = 50, roots=None) -> dict:
    """Return a single bounded, sorted metadata page without mutation.

    If scan cap/time is reached, the incomplete listing has no next cursor.
    Callers must not mistake the page for a complete inventory.
    """
    if roots is None:
        roots = ROOTS
    if not isinstance(scope, str) or scope not in roots:
        raise FileBrowserError("unknown server-side scope")
    if type(page_size) is not int or not 1 <= page_size <= MAX_PAGE:
        raise FileBrowserError("invalid page size")
    if not isinstance(after, str) or (after and not _valid_segment(after)):
        raise FileBrowserError("invalid cursor")
    segments = _segments(relative)
    directory = roots[scope]
    if not isinstance(directory, str) or not os.path.isabs(directory):
        raise FileBrowserError("server root is not configured")
    started = time.monotonic()
    try:
        fd = _open_beneath(directory, segments)
    except (OSError, FileBrowserError) as exc:
        raise FileBrowserError("directory not accessible") from exc
    rows = []
    truncated = False
    count = 0
    try:
        with os.scandir(fd) as entries:
            for entry in entries:
                if count >= MAX_ITEMS_SCANNED or time.monotonic() - started >= MAX_SECONDS:
                    truncated = True
                    break
                count += 1
                if not _valid_segment(entry.name):
                    continue
                try:
                    info = entry.stat(follow_symlinks=False)
                except OSError:
                    continue
                mode = info.st_mode
                kind = ("directory" if stat.S_ISDIR(mode) else
                        "file" if stat.S_ISREG(mode) else
                        "symlink" if stat.S_ISLNK(mode) else "other")
                rows.append({
                    "name": entry.name,
                    "kind": kind,
                    "size_bytes": info.st_size if kind == "file" else None,
                    "modified_unix": int(info.st_mtime),
                    "navigable": kind == "directory",
                })
    finally:
        os.close(fd)
    rows.sort(key=lambda item: item["name"])
    visible = [item for item in rows if item["name"] > after]
    page = visible[:page_size]
    has_more = not truncated and len(visible) > page_size
    return {
        "scope": scope,
        "relative": "/".join(segments),
        "items": page,
        "next_after": page[-1]["name"] if has_more and page else None,
        "incomplete": truncated,
        "entries_scanned": count,
        "read_only": True,
    }
