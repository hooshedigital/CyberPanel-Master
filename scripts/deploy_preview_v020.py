"""Deploy a narrowly scoped v0.2 *preview* of CyberPanel Master.

Safety: SHA-locked installed-source parity, 16 allowlisted preview files, root-only
byte backups and metadata, atomic writes, real Django view/ACL tests, lscpd-only
restart, HTTPS login smoke, best-effort automatic rollback on failure. Must be
executed only under the independent owner-approved root task broker.

The release is a preview. Persian is partial, and licensed AI scanning is not
modified. This file intentionally contains no owner credential or secret.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

SOURCES = ("_core_i18n_preview", "_ops_console_preview", "_agent_console_preview")
COUNT = 16

TEST_DJANGO = r'''
import json
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CyberCP.settings")
import django
django.setup()
from django.conf import settings
from django.urls import reverse
from django.test import RequestFactory
from unittest.mock import patch
from master_extensions.master_view import dashboard as master
from backup.cyber_agent import dashboard as agent

assert settings.LANGUAGE_CODE == "en"
assert any(code == "fa" for code, _ in settings.LANGUAGES)
assert settings.LANGUAGE_COOKIE_SECURE and settings.LANGUAGE_COOKIE_HTTPONLY
assert reverse("hooshMasterSetLanguage") == "/master/i18n/set-language/"
results = []
for view, css in ((master, b"hm-root"), (agent, b"ha-app")):
    for lang in ("en", "fa"):
        r = RequestFactory().get("/backup/master/?lang=" + lang, secure=True)
        r.session = {"userID": 1}
        with patch("plogical.acl.ACLManager.loadedACL", return_value={"admin": True}):
            response = view(r)
        assert response.status_code == 200, (lang, response.status_code)
        assert css in response.content
        root_marker = b'class="dashboard-wrapper ' + css + b'" dir="rtl"'
        assert (root_marker in response.content) == (lang == "fa")
        results.append([css.decode(), lang, response.status_code])
    guest = RequestFactory().get("/backup/master/", secure=True)
    guest.session = {}
    assert view(guest).status_code == 302
    guest.session = {"userID": 1}
    with patch("plogical.acl.ACLManager.loadedACL", return_value={"admin": False}):
        assert view(guest).status_code == 403
print(json.dumps({"ok": True, "renders": results, "acl": "302/403", "default": "en"}))
'''


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_staging(core: Path, stage: Path) -> list[dict]:
    items, names = [], set()
    for folder in SOURCES:
        manifest = json.loads((stage / folder / "manifest.json").read_text())
        if manifest["version"] != "0.2.0-dev" or manifest["production_changes"] != 0:
            raise ValueError("unverified manifest version or scope")
        for info in manifest["files"]:
            rel = info["path"]
            p = Path(rel)
            if (p.is_absolute() or ".." in p.parts or not p.parts
                    or p.parts[0] not in {"CyberCP", "baseTemplate", "master_extensions", "backup"}
                    or rel in names):
                raise ValueError("duplicate/unsafe preview path")
            names.add(rel)
            live = core / p
            staged = stage / folder / p
            if (live.is_symlink() or staged.is_symlink() or not staged.is_file()):
                raise ValueError("unsafe file/symlink")
            parent = core
            for component in p.parts[:-1]:
                parent = parent / component
                if parent.is_symlink():
                    raise ValueError("symlinked installed parent")
            after = staged.read_bytes()
            before = live.read_bytes() if live.exists() else None
            if (sha(after) != info["after_sha256"]
                    or (sha(before) if before is not None else None) != info["before_sha256"]
                    or len(after) > 250_000):
                raise ValueError("SHA/source drift")
            if rel.endswith(".py"):
                compile(after, rel, "exec")
            statbuf = live.stat() if before is not None else None
            items.append({
                "rel": rel, "live": live, "after": after, "before": before,
                "mode": stat.S_IMODE(statbuf.st_mode) if statbuf else 0o644,
                "uid": statbuf.st_uid if statbuf else 0,
                "gid": statbuf.st_gid if statbuf else 0,
                "old_sha": info["before_sha256"], "new_sha": info["after_sha256"],
            })
    if len(items) != COUNT:
        raise ValueError("release file count differs from approved 16-file set")
    return items


def atomic_write(path: Path, contents: bytes, mode: int, uid: int, gid: int):
    path.parent.mkdir(parents=True, mode=0o755, exist_ok=True)
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError("destination symlink")
    fd, name = tempfile.mkstemp(prefix=".hoosh-v020-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(contents)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, mode)
        os.chown(name, uid, gid)
        os.replace(name, path)
        dirfd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dirfd)
        finally:
            os.close(dirfd)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def restart_panel():
    run = subprocess.run(
        ["/usr/bin/systemctl", "restart", "lscpd.service"],
        capture_output=True, text=True, timeout=32
    )
    if run.returncode:
        raise RuntimeError("lscpd restart failure")


def django_checks(core: Path):
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    run = subprocess.run(
        [str(core / "bin/python"), "-c", TEST_DJANGO],
        cwd=str(core), env=env, capture_output=True, text=True, timeout=27,
    )
    if run.returncode:
        raise RuntimeError("Django view/ACL check failed: " + run.stderr[-700:])
    output = json.loads(run.stdout)
    if not output.get("ok"):
        raise RuntimeError("Django semantic result missing")
    return output


def http_checks():
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    routes = {
        "/": 200, "/backup/master/": 302, "/backup/cyber-agent/": 302,
        "/backup/smart/": 302, "/aiscanner/": 302,
    }
    result = {}
    for route, expected in routes.items():
        code = None
        for _ in range(6):
            try:
                url = "https://manage.hooshedigital.ir:8090" + route
                response = opener.open(urllib.request.Request(
                    url, headers={"User-Agent": "HooshDigital-MasterPreview/0.2"}
                ), timeout=5)
                code = response.status
            except urllib.error.HTTPError as error:
                code = error.code
            except Exception:
                code = None
            if code == expected:
                break
            time.sleep(1)
        if code != expected:
            raise RuntimeError("HTTPS route failed: " + route)
        result[route] = code
    return result


def deploy(core: Path, stage: Path, backup: Path):
    if backup.exists() or backup.is_symlink():
        raise ValueError("backup directory already exists")
    items = validate_staging(core, stage)
    backup.mkdir(mode=0o700, parents=False)
    os.chmod(backup, 0o700)
    records = []
    for item in items:
        record = {
            key: item[key] for key in
            ("rel", "mode", "uid", "gid", "old_sha", "new_sha")
        }
        record["existed"] = item["before"] is not None
        records.append(record)
        if item["before"] is not None:
            dst = backup / "original" / item["rel"]
            dst.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            dst.write_bytes(item["before"])
            os.chmod(dst, 0o600)
            if sha(dst.read_bytes()) != item["old_sha"]:
                raise ValueError("backup copy SHA mismatch")
    manifest = backup / "restore_manifest.json"
    manifest.write_text(json.dumps({"state": "BACKUP_READY", "files": records}, indent=2))
    os.chmod(manifest, 0o600)

    changed = []
    try:
        for item in items:
            changed.append(item)
            atomic_write(item["live"], item["after"],
                         item["mode"], item["uid"], item["gid"])
            if sha(item["live"].read_bytes()) != item["new_sha"]:
                raise RuntimeError("deployed SHA mismatch")
        runtime = django_checks(core)
        restart_panel()
        http = http_checks()
        if subprocess.run(
            ["/usr/bin/systemctl", "is-active", "lscpd.service"],
            capture_output=True, text=True, timeout=4
        ).stdout.strip() != "active":
            raise RuntimeError("lscpd not active after restart")
        manifest.write_text(json.dumps({
            "state": "COMMITTED", "files": records, "runtime": runtime, "http": http
        }, indent=2))
        print(json.dumps({
            "ok": True, "version": "0.2.0-dev", "installed_files": len(changed),
            "backup": str(backup), "runtime": runtime, "http": http
        }))
    except BaseException as exc:
        failed = []
        for item in reversed(changed):
            try:
                if item["before"] is None:
                    item["live"].unlink(missing_ok=True)
                else:
                    payload = (backup / "original" / item["rel"]).read_bytes()
                    if sha(payload) != item["old_sha"]:
                        raise ValueError("invalid rollback backup")
                    atomic_write(item["live"], payload,
                                 item["mode"], item["uid"], item["gid"])
            except Exception as err:
                failed.append(item["rel"] + ": " + type(err).__name__)
        try:
            restart_panel()
        except Exception:
            failed.append("lscpd rollback restart")
        manifest.write_text(json.dumps({
            "state": "ROLLBACK_ATTEMPTED", "error": type(exc).__name__,
            "rollback_errors": failed, "files": records
        }, indent=2))
        print(json.dumps({
            "ok": False, "rolled_back": not failed, "error": str(exc)[:650],
            "rollback_errors": failed, "backup": str(backup)
        }))
        raise SystemExit(12)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({
            "ready": True,
            "paths": [item["rel"] for item in validate_staging(args.core, args.stage)]
        }))
    else:
        deploy(args.core, args.stage, args.backup)
