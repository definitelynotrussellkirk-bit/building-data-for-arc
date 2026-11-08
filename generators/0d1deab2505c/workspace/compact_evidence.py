"""Compact JSON evidence without changing data, with byte-exact restoration.

Only the common indent=2 JSON representation is accepted. Unexpected formatting,
duplicate keys, NaN/Infinity, or existing receipt/output files fail explicitly.
The receipt binds both representations and the exact reconstruction settings.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key: " + key)
        value[key] = item
    return value


def parse(raw):
    def invalid(value):
        raise ValueError("nonfinite JSON value: " + value)
    return json.loads(raw, object_pairs_hook=unique_object, parse_constant=invalid)


def original_bytes(value, newline):
    return (json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False)
            + ("\n" if newline else "")).encode("utf-8")


def compact(path, receipt_path):
    if path.is_symlink() or not path.is_file() or receipt_path.exists():
        raise ValueError("input must be a regular file and receipt must be new")
    raw = path.read_bytes()
    value = parse(raw)
    newline = raw.endswith(b"\n")
    rebuilt = original_bytes(value, newline)
    if rebuilt != raw:
        raise ValueError("input is not the supported byte-exact indent=2 JSON format")
    packed = (json.dumps(value, separators=(",", ":"), ensure_ascii=True,
                         allow_nan=False) + "\n").encode("utf-8")
    if len(packed) >= len(raw):
        raise ValueError("compaction would not save space")
    # Reconstruction is verified before any original bytes are replaced.
    if original_bytes(parse(packed), newline) != raw:
        raise AssertionError("round-trip changed data or original formatting")
    receipt = {
        "schema": "reversible-json-compaction-v1",
        "path": os.path.relpath(path.resolve(), receipt_path.resolve().parent),
        "original_sha256": sha(raw), "original_bytes": len(raw),
        "compacted_sha256": sha(packed), "compacted_bytes": len(packed),
        "reconstruction": {"indent": 2, "ensure_ascii": True,
                           "allow_nan": False, "trailing_newline": newline},
        "claim": "Whitespace encoding only; all original bytes can be restored.",
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    with receipt_path.open("x") as handle:
        json.dump(receipt, handle, indent=2)
        handle.write("\n")
    temporary = path.with_name(path.name + ".compacting")
    with temporary.open("xb") as handle:
        handle.write(packed)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)
    print(json.dumps(receipt))


def restore(receipt_path, output):
    receipt = parse(receipt_path.read_bytes())
    if receipt["schema"] != "reversible-json-compaction-v1":
        raise ValueError("unknown receipt schema")
    source = receipt_path.parent / receipt["path"]
    packed = source.read_bytes()
    if sha(packed) != receipt["compacted_sha256"]:
        raise ValueError("compacted evidence hash mismatch")
    raw = original_bytes(parse(packed), receipt["reconstruction"]["trailing_newline"])
    if sha(raw) != receipt["original_sha256"] or len(raw) != receipt["original_bytes"]:
        raise ValueError("original evidence reconstruction mismatch")
    if output is not None:
        with output.open("xb") as handle:
            handle.write(raw)
    print(json.dumps({"verified": True, "original_sha256": sha(raw),
                      "original_bytes": len(raw),
                      "output": str(output) if output is not None else None}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    compactor = commands.add_parser("compact")
    compactor.add_argument("input", type=Path)
    compactor.add_argument("--receipt", required=True, type=Path)
    restorer = commands.add_parser("restore")
    restorer.add_argument("receipt", type=Path)
    restorer.add_argument("--out", type=Path, help="new file; omit to verify without writing")
    args = parser.parse_args()
    if args.command == "compact":
        compact(args.input, args.receipt)
    else:
        restore(args.receipt, args.out)


if __name__ == "__main__":
    main()
