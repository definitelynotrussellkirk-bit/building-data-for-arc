"""Restore the losslessly compressed JSON evidence in this review return.

First unpack EVIDENCE-BUNDLE.tar.gz using the packet's verified bundle reader.
Then run this script with --packet-root pointing to the directory containing
checks/COMPRESSED-EVIDENCE.json. Existing identical files are left alone;
different files are never overwritten. Both stored and original hashes are
checked before writing. This is a local archive restoration helper.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked_path(root, name):
    relative = PurePosixPath(name)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != "checks":
        raise ValueError(f"Evidence path must stay under checks/: {name}")
    path = root.joinpath(*relative.parts)
    if any(part.is_symlink() for part in [path, *path.parents] if part != root.parent):
        raise ValueError(f"Refusing a symlink in evidence path: {name}")
    return path


def restore(root):
    root = root.resolve()
    manifest = json.loads((root / "checks/COMPRESSED-EVIDENCE.json").read_bytes())
    if manifest.get("schema") != "arcpuzzles-review-compressed-evidence-v1":
        raise ValueError("Unrecognized compression manifest")
    restored = []
    for row in manifest["files"]:
        source = checked_path(root, row["compressed_path"])
        target = checked_path(root, row["original_path"])
        stored = source.read_bytes()
        if sha(stored) != row["compressed_sha256"]:
            raise ValueError(f"Compressed hash mismatch: {source}")
        raw = gzip.decompress(stored)
        if len(raw) != row["original_bytes"] or sha(raw) != row["original_sha256"]:
            raise ValueError(f"Original size/hash mismatch: {target}")
        if target.exists():
            if target.read_bytes() != raw:
                raise ValueError(f"Refusing to overwrite different evidence: {target}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as handle:
                handle.write(raw)
        restored.append(row["original_path"])
    return {"status": "restored_and_verified", "files": len(restored), "paths": restored}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(restore(args.packet_root), indent=2))


if __name__ == "__main__":
    main()
