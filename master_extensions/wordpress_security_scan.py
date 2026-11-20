"""Independent, no-license WordPress threat-triage scanner (offline engine).

This code never modifies site files and does not claim to replicate the paid
CyberPanel/CyberPersons AI service. It provides *real bounded evidence-based
static indicators* rather than simulated results. AI reasoning/vulnerability
feed are separate opt-in adapters, not silently enabled or billed.

SECURITY CONTRACT:
- Inputs come ONLY from a validated site ID resolved by a future ACL-aware
  worker (never accept arbitrary client filesystem paths in the HTTP route).
- Directory-fd anchored traversal, O_NOFOLLOW, no mount crossing.
- No subprocess, PHP execution, data uploads, code excerpts or automatic fixes.
- Maximum entries/depth/bytes/time, explicit partial scan state.
- Results are advisory indicators, not definitive malware/CVE verdicts.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import stat
import time

MAX_FILES = 1500
MAX_BYTES_PER_FILE = 128 * 1024
MAX_BYTES_TOTAL = 8 * 1024 * 1024
MAX_DEPTH = 7
MAX_SECONDS = 12.0
MAX_FINDINGS = 80

@dataclass(frozen=True)
class Rule:
    id: str
    severity: str
    description_en: str
    description_fa: str
    pattern: re.Pattern[bytes]


RULES = (
    Rule("PHP_EVAL_BASE64", "high", "PHP eval wrapping base64_decode",
         "استفاده مشکوک eval همراه base64_decode در PHP",
         re.compile(rb"\beval\s*\(\s*base64_decode\s*\(", re.I)),
    Rule("PHP_EVAL_GZINFLATE", "high", "PHP eval wrapping gzinflate",
         "اجرای کد فشرده‌شده با eval و gzinflate",
         re.compile(rb"\beval\s*\(\s*gzinflate\s*\(", re.I)),
    Rule("PHP_INPUT_COMMAND", "critical", "User-controlled input used in a shell command",
         "ارسال مستقیم داده کاربر به فرمان پوسته در PHP",
         re.compile(rb"\b(?:shell_exec|system|passthru|exec)\s*\(\s*\$_(?:GET|POST|REQUEST)\s*\[", re.I)),
    Rule("PHP_ASSERT_INPUT", "high", "PHP assert directly receives request input",
         "ورودی مستقیم درخواست در assert در PHP",
         re.compile(rb"\bassert\s*\(\s*\$_(?:GET|POST|REQUEST)\s*\[", re.I)),
)

SEVERITIES = ("critical", "high", "medium", "low")
FILE_SUFFIXES = (".php", ".phtml", ".php5", ".inc")
SKIP_DIRS = {"node_modules", ".git", "vendor", "cache", "backups"}


def _short(s: str, limit=180):
    return s[:limit] if isinstance(s, str) else ""


def _read_regular(dir_fd: int, name: str, before: os.stat_result, limit: int) -> bytes | None:
    fd = None
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dir_fd)
        after = os.fstat(fd)
        if (not stat.S_ISREG(after.st_mode) or after.st_dev != before.st_dev
                or after.st_ino != before.st_ino or after.st_size != before.st_size
                or after.st_nlink != 1 or after.st_size > limit):
            return None
        chunks = []
        remaining = limit
        while remaining > 0:
            part = os.read(fd, min(remaining, 32768))
            if not part:
                break
            chunks.append(part)
            remaining -= len(part)
        return b"".join(chunks)
    except OSError:
        return None
    finally:
        if fd is not None:
            os.close(fd)


def scan_wordpress(root: Path | str, *, max_files=MAX_FILES,
                   max_bytes=MAX_BYTES_TOTAL, seconds=MAX_SECONDS,
                   max_depth=MAX_DEPTH, now=time.monotonic) -> dict:
    """Run one bounded scan on a server-resolved, authorized WordPress root."""
    if (not 1 <= max_files <= MAX_FILES or not 1 <= max_bytes <= MAX_BYTES_TOTAL
            or not 0 < seconds <= MAX_SECONDS or not 1 <= max_depth <= MAX_DEPTH):
        raise ValueError("invalid scan resource budget")
    root = Path(root)
    if not root.is_absolute():
        raise ValueError("server-resolved absolute site root required")
    try:
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError:
        return {"status": "unavailable", "complete": False, "files_scanned": 0,
                "bytes_read": 0, "findings": [], "engine": "static-indicators-v1"}

    deadline = now() + seconds
    visited = set()
    findings = []
    files_scanned = 0
    bytes_read = 0
    complete = True
    device = os.fstat(fd).st_dev

    def walk(parent_fd: int, parts: tuple[str, ...], depth: int):
        nonlocal complete, files_scanned, bytes_read
        ident = os.fstat(parent_fd)
        key = (ident.st_dev, ident.st_ino)
        if key in visited:
            return
        visited.add(key)
        try:
            with os.scandir(parent_fd) as entries:
                for entry in entries:
                    if now() >= deadline or files_scanned >= max_files or bytes_read >= max_bytes:
                        complete = False
                        break
                    name = entry.name
                    if not name or name in (".", ".."):
                        continue
                    try:
                        info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
                        if info.st_dev != device:
                            complete = False
                            continue
                        if stat.S_ISDIR(info.st_mode):
                            if name in SKIP_DIRS:
                                continue
                            if depth >= max_depth:
                                complete = False
                                continue
                            child_fd = None
                            try:
                                child_fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                                   dir_fd=parent_fd)
                                changed = os.fstat(child_fd)
                                if (changed.st_dev, changed.st_ino) == (info.st_dev, info.st_ino):
                                    walk(child_fd, parts + (name,), depth + 1)
                                else:
                                    complete = False
                            except OSError:
                                complete = False
                            finally:
                                if child_fd is not None:
                                    os.close(child_fd)
                        elif (stat.S_ISREG(info.st_mode)
                              and name.lower().endswith(FILE_SUFFIXES)):
                            if info.st_size > MAX_BYTES_PER_FILE or info.st_nlink != 1:
                                complete = False
                                continue
                            remaining = min(MAX_BYTES_PER_FILE, max_bytes - bytes_read)
                            if remaining < info.st_size:
                                complete = False
                                continue
                            raw = _read_regular(parent_fd, name, info, remaining)
                            if raw is None:
                                complete = False
                                continue
                            bytes_read += len(raw)
                            files_scanned += 1
                            for rule in RULES:
                                if len(findings) >= MAX_FINDINGS:
                                    complete = False
                                    break
                                if rule.pattern.search(raw):
                                    findings.append({
                                        "rule_id": rule.id, "severity": rule.severity,
                                        "relative_path": _short("/".join(parts + (name,))),
                                        "evidence_sha256": hashlib.sha256(raw).hexdigest(),
                                        "classification": "indicator_requires_review",
                                        # Never echo the PHP source or its secrets.
                                    })
                        # No other file type is inspected.
                    except OSError:
                        complete = False
        except OSError:
            complete = False

    try:
        walk(fd, (), 1)
    finally:
        os.close(fd)
    severity_counts = {name: sum(f["severity"] == name for f in findings)
                       for name in SEVERITIES}
    return {
        "status": "completed" if complete else "partial",
        "complete": complete, "files_scanned": files_scanned,
        "bytes_read": bytes_read, "findings": findings,
        "severity_counts": severity_counts,
        "engine": "static-indicators-v1",
        "ai_analysis_performed": False, "files_modified": 0,
        "confidence_notice": "Heuristic matches require human review; no zero-day guarantee",
    }
