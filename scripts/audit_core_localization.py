"""Measure *whole Core* internationalization gaps without changing its source.

This audit is deliberately conservative: template nodes and JavaScript string
literals are review candidates, not proof that a translation is absent. Static
results help prioritize every module, instead of declaring a few translated
cards to be 'full bilingual CyberPanel Master'.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import stat

TRANSLATED = re.compile(r"{%\s*(?:trans|blocktrans)\b|\b(?:gettext|gettext_lazy|_\()\s*\(")
NATIVE_UI = re.compile(r">\s*([A-Za-z][A-Za-z0-9 ,.?!:/()&;'\-]{3,90})\s*<")
JS_QUOTED = re.compile(r"""(?<![\\])(["'])([A-Za-z][A-Za-z0-9 !?.,:;'\-/()]{5,100})\1""")
SKIP_PARTS = {
    "node_modules", "__pycache__", "vendor", "bower_components",
    "jquery", "bootstrap", "ckeditor", "codemirror", "fontawesome",
    ".git", "dist", "build", "min",
}
MAX_FILES = 12000
MAX_BYTES = 1024 * 1024


def inspect_file(path: Path) -> dict:
    s = path.lstat()
    if not stat.S_ISREG(s.st_mode) or s.st_size > MAX_BYTES or s.st_size < 1:
        return {"skipped": True}
    raw = path.read_text("utf-8", errors="replace")
    source_anchors = len(re.findall(r"{%\s*(?:trans|blocktrans)\b", raw))
    if path.suffix == ".html":
        # Remove non-visible style/script blocks and Django comments; not all
        # candidate text is necessarily visible in the full rendered page.
        clean = re.sub(r"(?is)<(?:style|script)\b[^>]*>.*?</(?:style|script)\s*>", "", raw)
        clean = re.sub(r"(?s){#.*?#}", "", clean)
        candidates = [m.group(1) for m in NATIVE_UI.finditer(clean)
                      if "{%" not in m.group(1) and "{{" not in m.group(1)]
    else:
        candidates = [m.group(2) for m in JS_QUOTED.finditer(raw)
                      if "$" not in m.group(2) and len(m.group(2).split()) >= 2]
    return {
        "skipped": False,
        "trans_tags": source_anchors,
        "possible_hardcoded_strings": len(candidates),
        "examples": candidates[:5],  # only developer UI strings, never secrets
    }


def inspect_tree(root: Path, max_files: int = MAX_FILES) -> dict:
    if not root.is_dir() or not 1 <= max_files <= MAX_FILES:
        raise ValueError("invalid source directory or scan limit")
    records = []
    total_scanned = 0
    for path in sorted(root.rglob("*")):
        if len(records) >= max_files:
            break
        if not path.is_file() or path.suffix not in (".html", ".js"):
            continue
        rel = path.relative_to(root)
        if any(p.lower() in SKIP_PARTS or p.endswith(".min.js") for p in rel.parts):
            continue
        total_scanned += 1
        try:
            data = inspect_file(path)
        except (OSError, UnicodeError):
            continue
        if data.get("skipped"):
            continue
        records.append({
            "module": rel.parts[0] if len(rel.parts) > 1 else "root",
            "relative": str(rel),
            **data,
        })
    module_totals = {}
    for record in records:
        name = record["module"]
        group = module_totals.setdefault(name, {"files": 0, "trans_tags": 0,
                                                "possible_hardcoded_strings": 0})
        group["files"] += 1
        group["trans_tags"] += record["trans_tags"]
        group["possible_hardcoded_strings"] += record["possible_hardcoded_strings"]
    return {
        "scope": "full_cyberpanel_source_tree",
        "coverage_is_verified": False,
        "stats_are_heuristic": True,
        "scanned": total_scanned,
        "counted": len(records),
        "truncated": len(records) >= max_files,
        "summary": {
            "modules": len(module_totals),
            "django_template_translation_tags": sum(x["trans_tags"] for x in records),
            "possible_untranslated_display_strings": sum(x["possible_hardcoded_strings"] for x in records),
        },
        "modules": {k: module_totals[k] for k in sorted(module_totals)},
        # The report deliberately excludes source lines, strings or user data.
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--core", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = inspect_tree(args.core)
    data = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(data, encoding="utf-8")
    else:
        print(data)


if __name__ == "__main__":
    main()
