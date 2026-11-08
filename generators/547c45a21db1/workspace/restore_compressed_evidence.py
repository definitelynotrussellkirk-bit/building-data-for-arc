"""Restore losslessly compressed review evidence with hash verification."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def contained(root, name):
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe evidence path: {name}")
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"evidence path escapes root: {name}")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--manifest", default="checks/compressed-evidence.json")
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = json.loads(contained(root, args.manifest).read_text())
    for entry in manifest["files"]:
        compressed = contained(root, entry["compressed_path"]).read_bytes()
        if digest(compressed) != entry["compressed_sha256"]:
            raise ValueError(f"compressed hash mismatch: {entry['compressed_path']}")
        raw = gzip.decompress(compressed)
        if len(raw) != entry["original_bytes"] or digest(raw) != entry["original_sha256"]:
            raise ValueError(f"original hash/size mismatch: {entry['original_path']}")
        target = contained(root, entry["original_path"])
        if target.exists():
            if not target.is_file() or target.read_bytes() != raw:
                raise ValueError(f"refusing to replace different evidence: {target}")
            action = "already verified"
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(raw)
            action = "restored"
        print(json.dumps({"path": entry["original_path"], "sha256": digest(raw), "action": action}))


if __name__ == "__main__":
    main()
