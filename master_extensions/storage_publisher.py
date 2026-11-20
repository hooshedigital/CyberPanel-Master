"""Atomic publisher for *read-only* storage and cleanup preview reports.

Run outside HTTP as the unprivileged hooshagent via an explicitly installed
systemd oneshot/timer. This code does not delete/modify scanned files and is
NOT installed or enabled by committing it to GitHub.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
import stat

from .storage_probe import snapshot as storage_snapshot
from .cleanup_preview import snapshot as cleanup_snapshot

OUTPUT = Path("/var/lib/hoosh-cybermaster")
FILES = ("storage-report.json", "cleanup-preview.json")
MAX_SIZE = 65536


def publish_document(directory: Path, filename: str, payload: dict) -> None:
    if filename not in FILES or not isinstance(payload, dict):
        raise ValueError("invalid report")
    data = json.dumps(payload, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")
    if len(data) > MAX_SIZE:
        raise ValueError("report too large")
    directory = Path(directory)
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    temp = ".hoosh-report-" + secrets.token_hex(8)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISDIR(info.st_mode) or
                info.st_uid not in (0, os.geteuid()) or info.st_mode & 0o022):
            raise PermissionError("unsafe report directory")
        n = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o644, dir_fd=fd)
        try:
            with os.fdopen(n, "wb") as target:
                target.write(data)
                target.flush()
                os.fsync(target.fileno())
            os.replace(temp, filename, src_dir_fd=fd, dst_dir_fd=fd)
            os.fsync(fd)
        finally:
            try:
                os.unlink(temp, dir_fd=fd)
            except FileNotFoundError:
                pass
    finally:
        os.close(fd)


def run_once(directory: Path = OUTPUT, *, storage=None, cleanup=None) -> dict:
    storage = storage_snapshot() if storage is None else storage
    cleanup = cleanup_snapshot() if cleanup is None else cleanup
    publish_document(directory, FILES[0], storage)
    publish_document(directory, FILES[1], cleanup)
    return {"reports_written": 2, "cleanup_actions_performed": 0,
            "files_deleted": 0}


if __name__ == "__main__":
    # Output dir is provisioned by StateDirectory in systemd unit.
    print(json.dumps(run_once(), separators=(",", ":")))
