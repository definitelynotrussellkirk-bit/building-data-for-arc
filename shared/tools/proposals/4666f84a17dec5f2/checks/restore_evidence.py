"""Restore byte-identical compressed review evidence using its recorded manifest.

Run after restoring the packager's outer EVIDENCE-BUNDLE, if present:
    python3 checks/restore_evidence.py --check-only
    python3 checks/restore_evidence.py
An existing different destination is never overwritten.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import tempfile


def safe_path(root, name):
    relative = PurePosixPath(name)
    if relative.is_absolute() or ".." in relative.parts or relative.parts[0] != "checks":
        raise ValueError(f"Unsafe evidence path: {name}")
    path = root.joinpath(*relative.parts)
    if root not in path.resolve().parents:
        raise ValueError(f"Evidence path escapes root: {name}")
    return path


def restore(root, manifest, check_only=False):
    rows = []
    for entry in manifest["files"]:
        source = safe_path(root, entry["compressed_path"])
        destination = safe_path(root, entry["original_path"])
        compressed = source.read_bytes()
        if hashlib.sha256(compressed).hexdigest() != entry["compressed_sha256"]:
            raise ValueError(f"Compressed hash mismatch: {source}")
        expected_size = entry["original_size_bytes"]
        if not isinstance(expected_size, int) or not 0 <= expected_size <= 100 * 1024 * 1024:
            raise ValueError("Evidence member exceeds the bounded restoration size")
        digest = hashlib.sha256()
        size = 0
        with tempfile.TemporaryFile() as temporary:
            with gzip.open(source, "rb") as incoming:
                for block in iter(lambda: incoming.read(1024 * 1024), b""):
                    size += len(block)
                    if size > expected_size:
                        raise ValueError(f"Expanded size exceeds manifest: {source}")
                    digest.update(block)
                    temporary.write(block)
            if size != expected_size or digest.hexdigest() != entry["original_sha256"]:
                raise ValueError(f"Restored size/hash mismatch: {source}")
            status = "verified"
            if not check_only:
                if destination.exists():
                    if destination.is_symlink() or hashlib.sha256(destination.read_bytes()).hexdigest() != digest.hexdigest():
                        raise FileExistsError(f"Refusing to overwrite different evidence: {destination}")
                    status = "already_identical"
                else:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    temporary.seek(0)
                    with destination.open("xb") as outgoing:
                        for block in iter(lambda: temporary.read(1024 * 1024), b""):
                            outgoing.write(block)
                    status = "restored"
            rows.append({"path": entry["original_path"], "bytes": size,
                         "sha256": digest.hexdigest(), "status": status})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = json.loads((root / "checks/COMPRESSED_EVIDENCE.json").read_text())
    if manifest.get("schema") != "review-compressed-evidence-v1":
        raise ValueError("Unexpected compression manifest schema")
    print(json.dumps({"files": restore(root, manifest, args.check_only)}, indent=2))


if __name__ == "__main__":
    main()
