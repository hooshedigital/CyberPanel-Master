#!/usr/bin/env python3
"""Read-only infrastructure inventory; no network requests, secrets or writes."""
import json
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path


def read(path, limit=8192):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read(limit).strip()
    except (OSError, UnicodeError):
        return None


def command(argv, pattern):
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=4,
                           check=False, env={**os.environ, "LC_ALL": "C"})
        match = re.search(pattern, r.stdout + "\n" + r.stderr)
        return match.group(1) if r.returncode == 0 and match else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def report():
    raw = read("/proc/meminfo") or ""
    memory = {}
    for key in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
        m = re.search(r"(?m)^" + key + r":\s+(\d+)\s+kB$", raw)
        memory[key + "_mib"] = round(int(m.group(1)) / 1024, 1) if m else None
    disk = shutil.disk_usage("/")
    return {
        "schema": 1, "read_only": True,
        "kernel": platform.release(),
        "mglru": read("/sys/kernel/mm/lru_gen/enabled"),
        "zswap": {k: read("/sys/module/zswap/parameters/" + k, 128)
                  for k in ("enabled", "compressor", "zpool", "max_pool_percent")},
        "zswap_stats": {k: read("/sys/kernel/debug/zswap/" + k, 128)
                        for k in ("pool_total_size", "stored_pages",
                                  "written_back_pages", "pool_limit_hit",
                                  "reject_alloc_fail")},
        "versioned_runtimes": {
            "frankenphp": command(
                ["/opt/hoosh-runtimes/frankenphp/1.14.0/frankenphp", "version"],
                r"FrankenPHP v?([0-9.]+)"),
            "valkey": command(
                ["/opt/hoosh-runtimes/valkey/8.1.12/valkey-server", "--version"],
                r"Valkey server v=([0-9.]+)")
        },
        "memory": memory,
        "disk_available_mib": disk.free // (1024 * 1024),
        "docker": {
            "version": command(["docker", "--version"], r"Docker version ([0-9.]+)"),
            "buildx": command(["docker", "buildx", "version"], r"buildx v?([0-9.]+)"),
            "live_restore": command(["docker", "info", "--format",
                                      "{{.LiveRestoreEnabled}}"], r"(?m)^(true|false)$")
        },
        "openlitespeed": command(["/usr/local/lsws/bin/openlitespeed", "-v"],
                                 r"LiteSpeed/([0-9.]+)"),
        "restic": command(["restic", "version"], r"restic ([0-9.]+)"),
        "php": command(["php", "-v"], r"PHP ([0-9.]+)"),
        "apache": command(["apache2", "-v"], r"Apache/([0-9.]+)"),
        "installed_kernels": sorted(p.name.removeprefix("vmlinuz-")
                                    for p in Path("/boot").glob("vmlinuz-*"))
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True))
