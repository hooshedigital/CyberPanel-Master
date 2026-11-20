"""Bounded, non-mutating inventory of Core-wide gettext translation coverage.

No arbitrary runtime sources or personal site files are scanned. Only static
CyberPanel application templates/source from explicitly selected modules.
It reports coverage, NOT that every visible raw string is localized.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import json
import re

from scripts.compile_po import parse_po

MAX_FILES = 12_000
MAX_FILE_BYTES = 180_000
CORE_MODULES = (
    "baseTemplate", "loginSystem", "websiteFunctions", "userManagment",
    "packages", "backup", "serverStatus", "databases", "mailServer",
    "firewall", "manageSSL", "managePHP", "filemanager", "aiScanner",
    "dockerManager", "dns", "serverLogs", "plogical",
)
PATTERNS = (
    re.compile(r"""\{%\s*trans\s+["']([^"']+)["']\s*%\}"""),
    re.compile(r"""\b(?:gettext|gettext_lazy|_)\(\s*["']([^"']+)["']\s*\)"""),
)

def scan_translation_coverage(core: Path, catalog: dict[str, str]) -> dict:
    core = Path(core)
    if not core.is_dir():
        raise ValueError("invalid CyberPanel Core root")
    if not isinstance(catalog, dict):
        raise ValueError("invalid translation catalog")
    extracted: set[str] = set()
    locations: dict[str, set[str]] = {}
    seen_files = scanned_files = oversized = 0
    for module in CORE_MODULES:
        folder = core / module
        if not folder.is_dir() or folder.is_symlink():
            continue
        for path in folder.rglob("*"):
            if seen_files >= MAX_FILES:
                break
            try:
                if path.is_symlink() or not path.is_file() or path.suffix not in (".py",".html",".js"):
                    continue
                seen_files += 1
                if path.stat().st_size > MAX_FILE_BYTES:
                    oversized += 1
                    continue
                raw = path.read_text("utf-8",errors="replace")
            except OSError:
                continue
            scanned_files += 1
            for expression in PATTERNS:
                for match in expression.finditer(raw):
                    msgid = match.group(1)
                    if not msgid or len(msgid)>400:
                        continue
                    extracted.add(msgid)
                    locations.setdefault(module,set()).add(msgid)
        if seen_files >= MAX_FILES:
            break
    translated = {msg for msg in extracted if catalog.get(msg)}
    missing = extracted - translated
    by_module = {
        name: {
            "keys": len(keys),
            "translated": len(keys & translated),
            "missing": len(keys - translated),
        }
        for name, keys in sorted(locations.items())
    }
    coverage = (100*len(translated)/len(extracted)) if extracted else 0
    return {
        "schema":1,"source":"static-core-source-only",
        "en_primary":True,
        "fa_catalog_keys":len(catalog)-int("" in catalog),
        "files_examined":scanned_files,"files_skipped_oversize":oversized,
        "bounded_traversal":seen_files < MAX_FILES,
        "unique_source_keys":len(extracted),"translated_keys":len(translated),
        "missing_keys":len(missing),"coverage_percent":round(coverage,1),
        "by_module":by_module,
        "deployment_ready":bool(extracted) and not missing and seen_files<MAX_FILES,
        "note":"Only marked gettext strings; unmarked hardcoded page or JS text requires separate audit",
    }

if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--core",type=Path,required=True)
    parser.add_argument("--po",type=Path,required=True)
    args=parser.parse_args()
    report=scan_translation_coverage(args.core,parse_po(args.po.read_text("utf-8")))
    print(json.dumps(report,ensure_ascii=False,indent=2))
