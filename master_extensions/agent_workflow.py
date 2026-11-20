"""Strict non-root CyberAgent CLI adapter for a future approved worker.

THIS MODULE IS NOT CALLED BY DJANGO. Server-side browser endpoints MUST NOT
spawn this process. A separate, service-account worker may use the fixed
allowlist after verifying the owner/role/approval record and writing its audit.
"""
from __future__ import annotations

import json
import os
import pwd
import subprocess
from typing import Callable

# Exact CLI commands verified from hoosh-cyberagent 0.9.0 source.
COMMANDS = {
    "ops_status": ("ops-status",),
    "resource_status": ("resource-status",),
    "inspect_dry_run": ("ops-once", "--dry-run"),
}
CONFIG_PATH = "/etc/hoosh-cyberagent/config.json"
EXECUTABLE = "/usr/local/bin/hoosh-cyberagent"
MAX_OUTPUT = 32768


def command_plan(operation: str) -> dict:
    if operation not in COMMANDS:
        raise ValueError("operation not allowlisted")
    return {
        "operation": operation,
        "argv": [EXECUTABLE, *COMMANDS[operation], "--config", CONFIG_PATH],
        "privilege": "non-root hooshagent service account",
        "requires_separate_owner_approval": operation == "inspect_dry_run",
        "dry_run": operation == "inspect_dry_run",
        "invoked_from_web": False,
    }


def run_approved_nonroot(operation: str, *, worker_approval=False,
                         runner: Callable | None = None,
                         uid: int | None = None) -> dict:
    """Run only with a separate worker identity; never with root or HTTP session.

    The return value whitelists non-sensitive metadata; raw command stdout,
    private config, logs, email addresses and secrets are never returned.
    """
    plan = command_plan(operation)
    uid = os.geteuid() if uid is None else uid
    if uid == 0 or pwd.getpwuid(uid).pw_name != "hooshagent":
        raise PermissionError("dedicated_agent_user_required")
    if not worker_approval:
        raise PermissionError("worker_owner_approval_required")
    runner = subprocess.run if runner is None else runner
    try:
        result = runner(
            plan["argv"], capture_output=True, text=True, timeout=15,
            check=False, env={
                "PATH": "/usr/local/bin:/usr/bin:/bin",
                "LANG": "C.UTF-8",
                "HOME": "/var/lib/hoosh-cyberagent",
            },
        )
        if result.returncode not in (0, 1, 2) or len(result.stdout) > MAX_OUTPUT:
            return {"operation": operation, "state": "unverified"}
        payload = json.loads(result.stdout)
        if not isinstance(payload, dict):
            return {"operation": operation, "state": "unverified"}
        # Do not reflect the entire CLI JSON into the web UI.
        status = payload.get("status")
        if status not in ("ok", "warning", "critical", "dry_run"):
            status = "unverified"
        version = payload.get("version")
        if not isinstance(version, str) or len(version) > 32:
            version = None
        return {"operation": operation, "state": status,
                "version": version, "exit_code": result.returncode}
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return {"operation": operation, "state": "unverified"}
