"""Lossless large-report packing with hashes and explicit restoration.

Run from any directory:
  python path/to/checks/evidence_archive.py pack
  python path/to/checks/evidence_archive.py verify
  python path/to/checks/evidence_archive.py restore --out restored

Packing replaces only >=1 MB JSON reports under this checks directory after a
verified gzip round trip. Original paths, sizes and hashes remain in the manifest.
Restoration never overwrites different existing bytes and writes only checks/.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath

CHECKS = Path(__file__).resolve().parent
ROOT = CHECKS.parent
MANIFEST = CHECKS / "COMPRESSED_EVIDENCE.json"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def safe(root, name):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not name.startswith("checks/") or "\\" in name:
        raise ValueError(f"invalid evidence path: {name}")
    target = root.joinpath(*path.parts)
    if not target.resolve().is_relative_to(root.resolve()) or target.is_symlink():
        raise ValueError(f"evidence path leaves destination: {name}")
    return target


def original(row):
    path = safe(ROOT, row["compressed_path"])
    compressed = path.read_bytes()
    if len(compressed) != row["compressed_bytes"] or digest(compressed) != row["compressed_sha256"]:
        raise ValueError(f"compressed identity mismatch: {path}")
    with gzip.open(path, "rb") as source:
        raw = source.read(row["original_bytes"] + 1)
    if len(raw) != row["original_bytes"] or digest(raw) != row["original_sha256"]:
        raise ValueError(f"restored identity mismatch: {path}")
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("pack", "verify", "restore"))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {"schema": "review-gzip-evidence-v1", "files": []}
    if args.action == "pack":
        for path in sorted(CHECKS.rglob("*.json")):
            if path == MANIFEST or path.stat().st_size < 1_000_000:
                continue
            raw = path.read_bytes()
            name = path.relative_to(ROOT).as_posix()
            if any(row["original_path"] == name for row in manifest["files"]):
                raise ValueError(f"already packed path was recreated: {name}")
            packed = path.with_suffix(path.suffix + ".gz")
            if packed.exists():
                raise FileExistsError(packed)
            encoded = gzip.compress(raw, compresslevel=9, mtime=0)
            packed.write_bytes(encoded)
            row = {"original_path": name, "original_bytes": len(raw), "original_sha256": digest(raw),
                   "compressed_path": packed.relative_to(ROOT).as_posix(),
                   "compressed_bytes": len(encoded), "compressed_sha256": digest(encoded)}
            if original(row) != raw:
                raise ValueError(f"round-trip verification failed: {name}")
            manifest["files"].append(row)
            MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
            path.unlink()
    if args.action == "restore" and args.out is None:
        parser.error("restore requires --out; choose an evidence destination")
    for row in manifest["files"]:
        raw = original(row)
        if args.action == "restore":
            target = safe(args.out.resolve(), row["original_path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and target.read_bytes() != raw:
                raise FileExistsError(f"refusing to overwrite different evidence: {target}")
            if not target.exists():
                with target.open("xb") as output:
                    output.write(raw)
    print(json.dumps({"action": args.action, "verified_files": len(manifest["files"]),
                      "original_bytes": sum(row["original_bytes"] for row in manifest["files"]),
                      "compressed_bytes": sum(row["compressed_bytes"] for row in manifest["files"])}))


if __name__ == "__main__":
    main()
