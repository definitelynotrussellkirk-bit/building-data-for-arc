#!/usr/bin/env python3
"""Losslessly package an already-completed JSON census without rerunning it.

The native lesson-census --gzip option is preferable for new runs.  This helper
retains the exact original bytes and writes the same documented retention
manifest for a completed uncompressed run. It never deletes the source.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def compress(path):
    path = Path(path)
    if path.suffix != ".json" or path.is_symlink():
        raise ValueError("input must be a regular .json file")
    compressed = path.with_suffix(".json.gz")
    manifest_path = path.with_suffix(".compression.json")
    if compressed.exists() or manifest_path.exists():
        raise FileExistsError("compressed output or manifest already exists")
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict) or not isinstance(value.get("schema"), str):
        raise ValueError("expected a schema-bearing JSON report")
    payload = gzip.compress(raw, mtime=0)
    if gzip.decompress(payload) != raw:
        raise AssertionError("gzip round-trip mismatch")
    manifest = {
        "schema": "arcpuzzles-evidence-gzip-v1", "compression": "gzip",
        "report_schema": value["schema"], "status": value.get("status"),
        "training_admitted": False,
        "restore_argv": ["python3", "-m", "gzip", "-d", compressed.name],
        "restore_note": "Restore a copy in a new directory; verify raw_size and raw_sha256 before using it.",
        "files": [{"path": path.name, "compressed_path": compressed.name,
                   "raw_size": len(raw), "raw_sha256": digest(raw),
                   "compressed_size": len(payload), "compressed_sha256": digest(payload)}],
    }
    with compressed.open("xb") as stream:
        stream.write(payload)
    if gzip.decompress(compressed.read_bytes()) != raw:
        raise AssertionError("written evidence failed byte verification")
    with manifest_path.open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2)
        stream.write("\n")
    return {"source": str(path), "compressed": str(compressed),
            "manifest": str(manifest_path), "round_trip_verified": True,
            **manifest["files"][0]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    args = parser.parse_args()
    for source in args.inputs:
        print(json.dumps(compress(source), sort_keys=True))
