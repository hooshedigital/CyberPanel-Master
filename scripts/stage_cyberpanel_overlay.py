#!/usr/bin/env python3
"""Build a deterministic, inspectable overlay against the INSTALLED CyberPanel.

Never mutates the live server. Preserves installed login/Turnstile, SSL, core
routes, local Master monitoring block, and Smart Backup controller differences.
Produces only review files under this Git checkout's _live_overlay directory.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import runpy
import shutil
import stat
import sys

REPO = Path(__file__).resolve().parents[1]
CORE = Path("/usr/local/CyberCP")
OUTPUT = REPO / "_live_overlay"
BOUND = 256_000
MODULES = (
    "operations_center.py",
    "storage_probe.py",
    "cleanup_preview.py",
    "workspace_browser.py",
    "agent_workflow.py",
    "storage_publisher.py",
)
LABEL_PREFIXES = ("storage_", "cleanup_", "workspace_", "agent_ops_")


def source(root: Path, relative: str) -> str:
    path = root / relative
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= BOUND:
        raise ValueError("invalid or oversized source: " + relative)
    return path.read_text("utf-8")


def one(source_text: str, before: str, after: str, path: str) -> str:
    if source_text.count(before) != 1:
        raise ValueError(f"parity mismatch: {path} anchor {before[:48]!r}")
    return source_text.replace(before, after, 1)


def labels_overlay(target: str, original: str) -> str:
    mine = runpy.run_path(str(CORE / target))["LABELS"]
    stage = runpy.run_path(str(REPO / target))["LABELS"]
    for language in ("en", "fa"):
        extra = {k: value for k, value in stage[language].items()
                 if (k.startswith(LABEL_PREFIXES) or
                     (target.endswith("backup_i18n.py") and k == "snapshot"))
                 and k not in mine[language]}
        if not extra:
            raise ValueError("expected new bilingual labels missing " + target + language)
        original += '\nLABELS[' + repr(language) + '].update(' + repr(extra) + ')\n'
    return original


def main() -> int:
    if not CORE.is_dir() or not (REPO / "master_extensions/operations_center.py").is_file():
        raise RuntimeError("live CyberPanel or staged source missing")
    if OUTPUT.exists():
        raise RuntimeError("overlay output already exists: leave prior inspection intact")
    assembled: dict[str, str] = {}
    for name in ("__init__.py", "master_view.py", "i18n.py",
                 "backup_i18n.py", "bridge.py", "version.py",
                 "login_captcha.py", "turnstile_core.py"):
        rel = "master_extensions/" + name
        assembled[rel] = source(CORE, rel)
    for name in MODULES:
        rel = "master_extensions/" + name
        assembled[rel] = source(REPO, rel)

    v = assembled["master_extensions/master_view.py"]
    v = one(v, "from .version import MASTER_VERSION,label",
            "from .version import MASTER_VERSION,label\n"
            "from .operations_center import operations_context\n"
            "from .workspace_browser import browse as browse_workspace", "master_view")
    v = one(v, "def display_context(lang):", "def display_context(lang, folder=''):", "master_view")
    v = one(v, '"updated":health.get("generated_utc")',
            '"updated":health.get("generated_utc"),\n'
            '        "ops":{**operations_context(lang),"workspace":browse_workspace(folder)}',
            "master_view")
    v = one(v, 'display_context(lang),"admin"',
            'display_context(lang,request.GET.get("folder","")),"admin"', "master_view")
    assembled["master_extensions/master_view.py"] = v

    assembled["master_extensions/i18n.py"] = labels_overlay(
        "master_extensions/i18n.py", assembled["master_extensions/i18n.py"])
    assembled["master_extensions/backup_i18n.py"] = labels_overlay(
        "master_extensions/backup_i18n.py", assembled["master_extensions/backup_i18n.py"])

    backup_rel = "backup/hoosh_smart.py"
    backup_view = source(CORE, backup_rel)
    backup_view = one(backup_view, "    context = summary()",
        "    from master_extensions.operations_center import cleanup_summary\n"
        "    context = summary()\n"
        "    context['cleanup_preview'] = cleanup_summary()",
        backup_rel)
    assembled[backup_rel] = backup_view

    existing_master = source(CORE, "backup/templates/backup/cyberpanel_master.html")
    staged_master = source(REPO, "master_extensions/templates/backup/cyberpanel_master.html")
    begin = '    <section class="panel" id="linux-storage"'
    end = '    <section class="panel" id="whmcs-center"'
    if staged_master.count(begin) != 1 or staged_master.count(end) != 1:
        raise ValueError("new Master operations sections not found")
    sections = staged_master[staged_master.index(begin):staged_master.index(end)]
    existing_master = one(existing_master,
        '    <section class="panel" aria-label="HooshDigital monitoring integration">',
        sections + '    <section class="panel" aria-label="HooshDigital monitoring integration">',
        "cyberpanel_master.html")
    assembled["backup/templates/backup/cyberpanel_master.html"] = existing_master

    rel = "backup/templates/backup/hoosh_smart.html"
    live_smart = source(CORE, rel)
    staged_smart = source(REPO, "master_extensions/templates/backup/hoosh_smart.html")
    start = '<section class="hb-card hb-section" aria-labelledby="hb-cleanup-heading">'
    stop = '<div class="hb-actions">'
    if staged_smart.count(start) != 1 or staged_smart.count(stop) != 1:
        raise ValueError("new Smart Backup section not found")
    cleanup_html = staged_smart[staged_smart.index(start):staged_smart.index(stop)]
    assembled[rel] = one(live_smart, stop, cleanup_html + stop, rel)

    # Preflight validates all target types and creates an isolated mirror only.
    for rel in assembled:
        target = CORE / rel
        if rel not in [f"master_extensions/{item}" for item in MODULES]:
            info = target.lstat()
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("non-regular live target: " + rel)
    written = []
    for rel, data in assembled.items():
        dest = OUTPUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(data, encoding="utf-8")
        written.append({"path": rel, "sha256": hashlib.sha256(data.encode()).hexdigest(),
                        "bytes": len(data.encode("utf-8"))})
    for name in ("hoosh-cybermaster-storage.service", "hoosh-cybermaster-storage.timer"):
        rel = "master_extensions/systemd/" + name
        data = source(REPO, rel)
        dest = OUTPUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(data)
    manifest = {"staging_only": True, "production_modified": False, "files": written}
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2))
    print(json.dumps({"result": "STAGING_OVERLAY_READY", "files": len(written),
                      "output": str(OUTPUT), "production_modified": False}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
