#!/usr/bin/env python3
"""Prepare a Compose copy with an explicit log policy. Never deploy or edit input."""
import argparse
import copy
import os
from pathlib import Path
import stat
import yaml

POLICY = {"driver": "json-file", "options": {"max-size": "10m", "max-file": "3"}}
MAX_BYTES = 128 * 1024

def mapping(node):
    if not isinstance(node, yaml.MappingNode) or node.flow_style:
        raise ValueError("block mapping required")
    result = {}
    for key, val in node.value:
        if not isinstance(key, yaml.ScalarNode) or key.tag != "tag:yaml.org,2002:str":
            raise ValueError("plain string key required")
        if key.value in result or key.value == "<<":
            raise ValueError("duplicate or merged mapping")
        result[key.value] = (key, val)
    return result

def transform(text, selected):
    if not selected or len(set(selected)) != len(selected):
        raise ValueError("invalid service selection")
    if len(text.encode("utf-8")) > MAX_BYTES or "\r" in text or "\t" in text:
        raise ValueError("unsupported source layout")
    # Reject aliases/anchors, ambiguous merge semantics and nonstandard tags.
    for event in yaml.parse(text, Loader=yaml.SafeLoader):
        if getattr(event, "anchor", None):
            raise ValueError("anchors require manual review")
    top = mapping(yaml.compose(text, Loader=yaml.SafeLoader))
    services = mapping(top["services"][1])
    before = yaml.safe_load(text)
    expected = copy.deepcopy(before)
    lines = text.splitlines(keepends=True)
    insertions = []
    for name in selected:
        if name not in services or "feast" in name.lower():
            raise ValueError("service not eligible")
        key, node = services[name]
        fields = mapping(node)
        if "logging" in fields:
            if before["services"][name]["logging"] != POLICY:
                raise ValueError("existing log policy requires review")
            continue
        if not fields:
            raise ValueError("empty service")
        first = node.value[0][0]
        indent = first.start_mark.column
        line = first.start_mark.line
        if indent <= key.start_mark.column or lines[line][:indent] != " " * indent:
            raise ValueError("unsupported service layout")
        block = (
            " " * indent + "logging:\n"
            + " " * (indent+2) + "driver: json-file\n"
            + " " * (indent+2) + "options:\n"
            + " " * (indent+4) + 'max-size: "10m"\n'
            + " " * (indent+4) + 'max-file: "3"\n'
        )
        insertions.append((line, block))
        expected["services"][name]["logging"] = copy.deepcopy(POLICY)
    for index, block in sorted(insertions, reverse=True):
        lines.insert(index, block)
    output = "".join(lines)
    if yaml.safe_load(output) != expected:
        raise ValueError("non-policy change")
    return output

def read_source(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as f:
        st = os.fstat(f.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_size > MAX_BYTES:
            raise ValueError("unsupported source file")
        raw = f.read(MAX_BYTES+1)
        if len(raw) > MAX_BYTES:
            raise ValueError("source too large")
        return raw.decode("utf-8")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("services", nargs="+")
    args = parser.parse_args()
    try:
        output = transform(read_source(args.source), args.services)
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(output)
            f.flush()
            os.fsync(f.fileno())
        print("LOG_POLICY_STAGED")
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError):
        raise SystemExit("Log policy staging refused; review source locally")

if __name__ == "__main__":
    main()
