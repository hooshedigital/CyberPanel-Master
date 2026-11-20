"""Small, dependency-free GNU gettext .po -> .mo compiler for audited catalogs.

Supports singular msgid/msgstr and continuation lines (the only format
maintained in master_extensions/locale). Deliberately rejects plural/fuzzy,
invalid headers, duplicate or empty translated entries; never executes code.
"""
from __future__ import annotations
import io
import json
import struct
from pathlib import Path

def parse_po(raw: str) -> dict[str, str]:
    if not isinstance(raw, str) or len(raw) > 2_000_000:
        raise ValueError("invalid PO data")
    entries: dict[str, str] = {}
    current_id = current_str = None
    mode = None

    def flush() -> None:
        nonlocal current_id, current_str, mode
        if current_id is None and current_str is None:
            return
        if current_id is None or current_str is None:
            raise ValueError("incomplete PO pair")
        if current_id in entries:
            raise ValueError("duplicate msgid")
        entries[current_id] = current_str
        current_id = current_str = mode = None

    for line in raw.splitlines() + [""]:
        text = line.strip()
        if not text:
            flush()
            continue
        if text.startswith("#, fuzzy") or text.startswith("msgid_plural") or text.startswith("msgstr["):
            raise ValueError("unsupported or fuzzy PO entry")
        if text.startswith("#"):
            continue
        if text.startswith("msgid "):
            if current_id is not None:
                raise ValueError("missing msgstr")
            current_id = json.loads(text[6:])
            mode = "id"
        elif text.startswith("msgstr "):
            if current_id is None or current_str is not None:
                raise ValueError("unexpected msgstr")
            current_str = json.loads(text[7:])
            mode = "str"
        elif text.startswith('"'):
            chunk = json.loads(text)
            if mode == "id":
                current_id += chunk
            elif mode == "str":
                current_str += chunk
            else:
                raise ValueError("PO continuation without current key")
        else:
            raise ValueError("unexpected PO record")
    if "" not in entries or "Content-Type: text/plain; charset=UTF-8" not in entries[""]:
        raise ValueError("missing UTF-8 translation metadata")
    for key, value in entries.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("non-string entry")
        if key and not value.strip():
            raise ValueError("untranslated PO entry")
    return entries


def compile_mo(entries: dict[str, str]) -> bytes:
    pairs = [(k.encode("utf-8"), v.encode("utf-8")) for k, v in entries.items()]
    pairs.sort(key=lambda pair: pair[0])
    count = len(pairs)
    ids = b"".join(k + b"\x00" for k, _ in pairs)
    values = b"".join(v + b"\x00" for _, v in pairs)
    key_offset = 28 + 16 * count
    value_offset = key_offset + len(ids)
    header = struct.pack("<7I", 0x950412de, 0, count, 28, 28 + 8 * count, 0, 0)
    keys = b""
    translations = b""
    p1 = p2 = 0
    for k, v in pairs:
        keys += struct.pack("<2I", len(k), key_offset + p1)
        translations += struct.pack("<2I", len(v), value_offset + p2)
        p1 += len(k) + 1
        p2 += len(v) + 1
    return header + keys + translations + ids + values


def compile_file(path: Path, output: Path) -> int:
    source = Path(path)
    raw = source.read_bytes()
    if len(raw) > 2_000_000:
        raise ValueError("oversized gettext catalog")
    translations = parse_po(raw.decode("utf-8"))
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise ValueError("refuse to overwrite compiled catalog")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(compile_mo(translations))
    return len(translations) - 1


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("po", type=Path)
    parser.add_argument("mo", type=Path)
    args = parser.parse_args()
    print(f"compiled {compile_file(args.po, args.mo)} translated strings")
