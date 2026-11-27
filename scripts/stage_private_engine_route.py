#!/usr/bin/python3
"""Produce a review copy of the independent panel route; never edit live files."""
import argparse
import ast
from pathlib import Path

IMPORT = "from . import views\n"
ANCHOR = "    path('createWebsite', views.createWebsite, name='createWebsite'),\n"
ADD_IMPORT = "from master_extensions.web_engine_plan_view import private_engine_plan\n"
ADD_ROUTE = "    path('hooshPrivateEnginePlan', private_engine_plan, name='hoosh_private_engine_plan'),\n"

def overlay(source):
    if source.count(IMPORT) != 1 or source.count(ANCHOR) != 1 or "hoosh_private_engine_plan" in source:
        raise ValueError("unexpected URL configuration")
    result = source.replace(IMPORT, IMPORT + ADD_IMPORT, 1).replace(ANCHOR, ANCHOR + ADD_ROUTE, 1)
    ast.parse(result)
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.source.is_symlink() or not args.source.is_file() or args.source.stat().st_size > 256000:
        raise ValueError("invalid source")
    result = overlay(args.source.read_text(encoding="utf-8"))
    with args.output.open("x", encoding="utf-8") as f:
        f.write(result)
    print("REVIEW_COPY_ONLY")

if __name__ == "__main__":
    main()
