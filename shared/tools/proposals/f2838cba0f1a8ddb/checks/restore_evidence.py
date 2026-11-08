#!/usr/bin/env python3
"""Verify or restore this review's losslessly compressed evidence."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
from pathlib import Path

def digest(data):
    return hashlib.sha256(data).hexdigest()

def inside(root, relative):
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"Unsafe relative evidence path: {relative}")
    path = (root / rel).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Evidence path escapes destination: {relative}")
    return path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--out-dir", type=Path, help="WORK-equivalent restoration root; defaults to this return root")
    args = parser.parse_args()
    source_root = Path(__file__).resolve().parent.parent
    output_root = (args.out_dir or source_root).resolve()
    manifest = json.loads((source_root / "checks/evidence-compression.json").read_text())
    checked = []
    for item in manifest["entries"]:
        packed = inside(source_root, item["retained_path"]).read_bytes()
        if len(packed) != item["retained_size_bytes"] or digest(packed) != item["retained_sha256"]:
            raise ValueError(f"Compressed evidence mismatch: {item['retained_path']}")
        raw = gzip.decompress(packed)
        if len(raw) != item["original_size_bytes"] or digest(raw) != item["original_sha256"]:
            raise ValueError(f"Restored evidence mismatch: {item['original_path']}")
        destination = inside(output_root, item["original_path"])
        status = "verified"
        if not args.verify_only:
            if destination.exists():
                if digest(destination.read_bytes()) != item["original_sha256"]:
                    raise FileExistsError(f"Refusing conflicting overwrite: {destination}")
                status = "already_matches"
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open("xb") as stream:
                    stream.write(raw)
                status = "restored"
        checked.append({"original_path": item["original_path"], "status": status,
                        "sha256": item["original_sha256"], "size_bytes": len(raw)})
    print(json.dumps({"status": "passed", "verify_only": args.verify_only,
                      "files": len(checked), "entries": checked}, indent=2))

if __name__ == "__main__":
    main()
