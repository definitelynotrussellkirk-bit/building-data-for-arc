"""Losslessly compact large review evidence with a verifiable restoration map.

Run through review.py run. Example:
  python3 generators/0eb4eaa46003/workspace/compact_evidence.py compress \
    ../checks/before/checks/REPORT.json --root ../checks --remove-original
  python3 generators/0eb4eaa46003/workspace/compact_evidence.py restore \
    ../checks/before/checks/REPORT.json.compression.json --root ../checks

This only handles explicitly named regular files below the evidence root.
It refuses replacement of an existing archive or a conflicting restored file.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def regular_within(path, root):
    if path.is_symlink() or not path.resolve().is_relative_to(root):
        raise ValueError("evidence path must remain inside the explicit root")
    if not path.is_file():
        raise ValueError(f"not a regular file: {path}")
    return path.resolve()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("compress", "restore"))
    parser.add_argument("path", type=Path)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--remove-original", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    source = regular_within(args.path, root)
    if args.operation == "compress":
        raw = source.read_bytes()
        archive = source.with_name(source.name + ".gz")
        sidecar = source.with_name(source.name + ".compression.json")
        if any(path.is_symlink() or path.exists() for path in (archive, sidecar)):
            raise ValueError("archive or restoration map already exists")
        packed = gzip.compress(raw, compresslevel=9, mtime=0)
        with archive.open("xb") as stream:
            stream.write(packed)
        if gzip.decompress(archive.read_bytes()) != raw:
            raise ValueError("archive round-trip verification failed; original retained")
        metadata = {"schema": "review-evidence-gzip-v1",
                    "original_path": source.relative_to(root).as_posix(),
                    "original_size": len(raw), "original_sha256": digest(raw),
                    "archive_path": archive.relative_to(root).as_posix(),
                    "archive_size": len(packed), "archive_sha256": digest(packed),
                    "round_trip_verified": True}
        with sidecar.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(metadata, indent=2) + "\n")
        if args.remove_original:
            source.unlink()
        print(json.dumps(metadata))
        return
    metadata = json.loads(source.read_text())
    archive = regular_within(root / metadata["archive_path"], root)
    packed = archive.read_bytes()
    if digest(packed) != metadata["archive_sha256"]:
        raise ValueError("compressed evidence hash mismatch")
    raw = gzip.decompress(packed)
    if len(raw) != metadata["original_size"] or digest(raw) != metadata["original_sha256"]:
        raise ValueError("restored evidence size/hash mismatch")
    target = root / metadata["original_path"]
    if target.is_symlink() or not target.resolve().is_relative_to(root):
        raise ValueError("restored path must remain inside the explicit root")
    if target.exists():
        if not target.is_file() or target.read_bytes() != raw:
            raise ValueError("refusing to replace differing restored evidence")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)
    print(json.dumps({"restored": metadata["original_path"], "sha256": digest(raw)}))


if __name__ == "__main__":
    main()
