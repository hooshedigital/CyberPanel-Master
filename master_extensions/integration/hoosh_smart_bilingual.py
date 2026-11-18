"""CyberPanel 3.0 build 4 read-only dashboard: no subprocess, no privileged operations.

Install as backup/hoosh_smart.py only after guarded patching of backup/urls.py,
baseTemplate templates and explicit owner approval.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import stat

from django.http import HttpResponseForbidden, HttpResponseNotAllowed
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache

from loginSystem.views import loadLoginPage
from plogical.acl import ACLManager
from plogical.httpProc import httpProc

DAILY_DIR = Path("/home/backup")
STATUS_FILE = Path("/var/lib/hoosh-smart-backup/status.json")

def _safe_file(p: Path, limit: int) -> bytes | None:
    try:
        info = p.lstat()
        if stat.S_ISREG(info.st_mode) and info.st_size <= limit:
            return p.read_bytes()
    except (OSError, ValueError):
        pass
    return None

def snapshot_status():
    result = {"state": "not_configured", "count": None, "updated": None}
    raw = _safe_file(STATUS_FILE, 4096)
    if raw is None:
        return result
    try:
        item = json.loads(raw)
        if not isinstance(item, dict):
            return result
        state = item.get("state")
        if state in {"idle", "running", "success", "error"}:
            result["state"] = state
        count = item.get("snapshot_count")
        if type(count) is int and 0 <= count <= 1_000_000:
            result["count"] = count
        updated = item.get("updated_utc")
        if isinstance(updated, str) and len(updated) <= 48:
            result["updated"] = updated
    except (ValueError, UnicodeError, TypeError):
        result["state"] = "error"
    return result

def local_backups():
    """Consume only the sanitized public report, never traverse private archives."""
    raw = _safe_file(Path("/var/lib/hoosh-smart-backup/daily-summary.json"), 65536)
    if raw is None:
        return []
    try:
        report = json.loads(raw)
        if not isinstance(report, dict) or report.get("schema") != 1:
            return []
        records = report.get("daily", [])
        if not isinstance(records, list):
            return []
        result = []
        for item in records[:32]:
            if not isinstance(item, dict):
                continue
            date = item.get("date")
            size = item.get("size_gb")
            recorded = item.get("checksum_recorded")
            if (not isinstance(date, str) or len(date) != 10
                    or date[4:5] != "-" or date[7:8] != "-"
                    or not all(date[i].isdigit() for i in (0,1,2,3,5,6,8,9))
                    or type(size) not in (float, int) or not 0 <= size <= 100_000
                    or type(recorded) is not bool):
                continue
            result.append({"date": date, "size_gb": round(size, 2),
                           "checksum_recorded": recorded})
        return result
    except (ValueError, UnicodeError, TypeError):
        return []

def summary():
    try:
        used,total,free = (None,None,None)
        disk = shutil.disk_usage("/")
        total,used,free = disk.total,disk.used,disk.free
        disk_used = round(100*used/max(total,1),1)
        free_gb = round(free/1e9,2)
    except (OSError,ValueError):
        disk_used,free_gb = None,None
    copies = local_backups()
    return {"backup": snapshot_status(), "daily": copies,
            "daily_count": len(copies),
            "total_daily_gb": round(sum(x["size_gb"] for x in copies),2),
            "disk_used": disk_used, "disk_free_gb": free_gb,
            "configured": STATUS_FILE.exists(),
            "version": "1.0.0-staging"}

@never_cache
def dashboard(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    uid = request.session.get("userID")
    if uid is None:
        return redirect(loadLoginPage)
    # The installed CyberPanel 3.0 B4 uses its own ACL, NOT Django auth.User.
    try:
        acl = ACLManager.loadedACL(uid)
    except Exception:
        return HttpResponseForbidden("Access denied")
    if not isinstance(acl, dict) or not acl.get("admin"):
        return HttpResponseForbidden("Administrator access required")
    from .master_extensions.i18n import COOKIE, BACKUP_LABELS, resolve_language
    requested = request.GET.get("lang")
    lang = resolve_language(requested, request.COOKIES.get(COOKIE))
    data = summary()
    data.update({"backup_lang": lang, "backup_dir": "rtl" if lang == "fa" else "ltr",
                 "backup_t": BACKUP_LABELS[lang]})
    response = httpProc(request, "backup/hoosh_smart.html", data, "admin").render()
    if requested in ("en", "fa"):
        response.set_cookie(COOKIE, lang, secure=True, httponly=True, samesite="Lax",
                            path="/backup/", max_age=180 * 86400)
    return response
