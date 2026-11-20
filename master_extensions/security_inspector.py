"""Hoosh CyberPanel Master independent *static* WordPress security inspector.

Legal, read-only alternative foundation to commercial hosted AI scanning.
No use of proprietary CyberPanel scanning APIs, paid credits, cloud inference,
root execution, malware deletion, file upload, database writes, or WP mutation.
Execute only via an independently approved non-root worker, never Django HTTP.

A rule hit is *suspicious*, not proof of malware; a clean result is not proof
that a site is malware-free. Report source files locally and show administrator
review guidance rather than taking remediation actions.
"""
from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import re
import stat
import time

MAX_ENTRIES = 3500
MAX_SECONDS = 4.0
MAX_PHP_SIZE = 512 * 1024
MAX_READ_TOTAL = 16 * 1024 * 1024
MAX_FINDINGS = 40

RULES = (
    ("PHP_OBFUSCATED_EVAL", "high",
     re.compile(rb"(?i)\beval\s*\(\s*base64_decode\s*\(")),
    ("PHP_INPUT_EXECUTION", "critical",
     re.compile(rb"(?i)\b(?:assert|system|exec|shell_exec|passthru)\s*\(\s*\$_(?:GET|POST|REQUEST)\s*\[")),
    ("PHP_OBFUSCATED_GZ", "medium",
     re.compile(rb"(?i)\b(?:eval|assert)\s*\(\s*gzinflate\s*\(")),
)

def _approved_root(root: Path, allowed_roots: tuple[Path, ...]) -> Path:
    """Accept only an exact site root chosen from an external trusted config."""
    root = Path(root)
    if not root.is_absolute() or not allowed_roots:
        raise PermissionError("no approved site root")
    if root.is_symlink():
        raise PermissionError("symlink site root")
    try:
        canonical = root.resolve(strict=True)
        if not any(canonical == Path(x).resolve(strict=True) for x in allowed_roots):
            raise PermissionError("site root not allowlisted")
        if not canonical.is_dir():
            raise PermissionError("site root not a directory")
        return canonical
    except OSError as exc:
        raise PermissionError("site root cannot be verified") from exc


def inspect_site(
    root: Path,
    *,
    allowed_roots: tuple[Path, ...],
    max_entries: int = MAX_ENTRIES,
    max_seconds: float = MAX_SECONDS,
    max_read: int = MAX_READ_TOTAL,
    clock=time.monotonic,
) -> dict:
    """Bounded independent static file audit, directory-fd anchored, no symlink walk.

    Approved roots are supplied solely by a trusted server-side worker config.
    A browser or URL parameter must never define allowed_roots.
    """
    if (type(max_entries) is not int or not 1 <= max_entries <= MAX_ENTRIES
            or not 0 < max_seconds <= MAX_SECONDS
            or type(max_read) is not int or not 0 <= max_read <= MAX_READ_TOTAL):
        raise ValueError("invalid resource budget")
    root = _approved_root(root, allowed_roots)
    if not ((root / "wp-includes").is_dir() and (root / "wp-content").is_dir()):
        return {"schema": 1, "engine": "independent-static-wordpress-v1",
                "ready": False, "reason": "not_a_verified_wordpress_tree",
                "scanned_files": 0, "findings": [], "partial": True,
                "ai_provider_used": False, "files_modified": 0}
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    rootfd = os.open(root, flags)
    stack: list[tuple[int, str]] = [(rootfd, "")]
    deadline = clock() + max_seconds
    try:
        device = os.fstat(rootfd).st_dev
        visited = 0
        php_files = 0
        bytes_read = 0
        findings: list[dict] = []
        partial = False

        while stack:
            fd, prefix = stack.pop()
            try:
                try:
                    iterator = os.scandir(fd)
                except OSError:
                    partial = True
                    continue
                with iterator:
                    for entry in iterator:
                        if clock() > deadline or visited >= max_entries:
                            partial = True
                            break
                        visited += 1
                        name = entry.name
                        # Do not expose secret or absolute paths in security reports.
                        if (not name or name in (".", "..") or "/" in name
                                or len(name) > 255):
                            partial = True
                            continue
                        rel = name if not prefix else prefix + "/" + name
                        if len(rel) > 420:
                            partial = True
                            continue
                        try:
                            info = entry.stat(follow_symlinks=False)
                        except OSError:
                            partial = True
                            continue
                        if info.st_dev != device:
                            partial = True
                            continue
                        if stat.S_ISLNK(info.st_mode):
                            continue
                        if stat.S_ISDIR(info.st_mode):
                            try:
                                child = os.open(name, flags, dir_fd=fd)
                                verified = os.fstat(child)
                                if (verified.st_dev != device or verified.st_ino != info.st_ino
                                        or not stat.S_ISDIR(verified.st_mode)):
                                    os.close(child)
                                    partial = True
                                    continue
                                stack.append((child, rel))
                            except OSError:
                                partial = True
                            continue
                        if not stat.S_ISREG(info.st_mode):
                            continue
                        if name.lower().endswith(".php"):
                            php_files += 1
                        if rel == "wp-config.php" and info.st_mode & 0o022:
                            findings.append({"rule": "WP_CONFIG_WRITABLE", "severity": "high",
                                             "relative_path": rel})
                        if rel.startswith("wp-content/uploads/") and name.lower().endswith((".php", ".phtml")):
                            findings.append({"rule": "PHP_IN_UPLOADS", "severity": "high",
                                             "relative_path": rel})
                        if name.lower().endswith((".php", ".phtml")) and 0 <= info.st_size <= MAX_PHP_SIZE:
                            if bytes_read >= max_read:
                                partial = True
                                continue
                            try:
                                handle = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                                                 dir_fd=fd)
                                try:
                                    actual = os.fstat(handle)
                                    if (not stat.S_ISREG(actual.st_mode)
                                            or (actual.st_dev, actual.st_ino) != (info.st_dev,info.st_ino)):
                                        partial = True
                                        continue
                                    limit = min(actual.st_size, max_read-bytes_read, MAX_PHP_SIZE)
                                    payload = os.read(handle, limit + 1)
                                    bytes_read += min(len(payload), limit)
                                    if len(payload) > limit:
                                        partial = True
                                        continue
                                finally:
                                    os.close(handle)
                                for rule, severity, pattern in RULES:
                                    if pattern.search(payload):
                                        findings.append({"rule": rule, "severity": severity,
                                                         "relative_path": rel})
                            except OSError:
                                partial = True
                        if len(findings) >= MAX_FINDINGS:
                            partial = True
                            break
            finally:
                os.close(fd)
            if partial and (clock() > deadline or visited >= max_entries or len(findings) >= MAX_FINDINGS):
                break
        findings = findings[:MAX_FINDINGS]
        return {
            "schema": 1,
            "engine": "independent-static-wordpress-v1",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "ready": True,
            "scanned_entries": visited,
            "scanned_php_files": php_files,
            "read_bytes": bytes_read,
            "partial": partial,
            "findings": findings,
            "finding_count": len(findings),
            "ai_provider_used": False,
            "files_modified": 0,
            "autofix_enabled": False,
            "scope": "explicit-allowlist-only",
        }
    finally:
        # Every directory on the stack owns one descriptor; close remaining
        # descriptors when scan aborts early or an unexpected exception occurs.
        for pending, _ in stack:
            try:
                os.close(pending)
            except OSError:
                pass
