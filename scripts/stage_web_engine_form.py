#!/usr/bin/env python3
"""Write a separate review copy; never replace the live website creation form."""
import argparse
from pathlib import Path
import stat

ROOT = Path(__file__).resolve().parents[1]
FRAGMENT = ROOT / "master_extensions/templates/websiteFunctions/hoosh_web_engine_preview.html"
ANCHOR = '<label class="form-label">{% trans "Additional Features" %}</label>'
MARKER = 'id="hoosh-web-engine-stage-preview"'


def overlay(original, fragment):
    if original.count(ANCHOR) != 1 or MARKER in original:
        raise ValueError("form_anchor_mismatch")
    if fragment.count(MARKER) != 1:
        raise ValueError("invalid_preview")
    return original.replace(ANCHOR, fragment + "\n" + ANCHOR, 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    info = args.source.lstat()
    if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= 256000:
        raise ValueError("invalid_source")
    if args.source.resolve() == args.output.resolve():
        raise ValueError("source_overwrite_forbidden")
    result = overlay(args.source.read_text(encoding="utf-8"),
                     FRAGMENT.read_text(encoding="utf-8"))
    with args.output.open("x", encoding="utf-8") as f:
        f.write(result)
    print("STAGING_PREVIEW_ONLY; original unchanged")


if __name__ == "__main__":
    main()
