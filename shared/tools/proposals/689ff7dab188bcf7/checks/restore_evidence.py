"""Verify and optionally restore the losslessly compressed large review reports.

Run from anywhere: python3 checks/restore_evidence.py [--restore]
The default verifies compressed and original hashes without writing.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(root: Path, name: str) -> Path:
    relative = PurePosixPath(name)
    if (not name or relative.is_absolute() or ".." in relative.parts
            or "\\" in name or str(relative) != name):
        raise ValueError(f"Unsafe evidence path: {name!r}")
    target = root / name
    for path in (target, *target.parents):
        if path.is_symlink():
            raise ValueError(f"Symlink evidence path: {path}")
        if path == root:
            break
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).absolute().parent.parent
    manifest = json.loads((root / "checks/COMPRESSED-EVIDENCE.json").read_text())
    results = []
    for row in manifest["files"]:
        stored = safe_path(root, row["stored_path"])
        compressed = stored.read_bytes()
        if sha(compressed) != row["stored_sha256"] or len(compressed) != row["stored_bytes"]:
            raise ValueError(f"Compressed evidence changed: {stored}")
        with gzip.open(stored, "rb") as stream:
            original = stream.read(row["original_bytes"] + 1)
        if sha(original) != row["original_sha256"] or len(original) != row["original_bytes"]:
            raise ValueError(f"Original evidence mismatch: {stored}")
        target = safe_path(root, row["original_path"])
        status = "verified"
        if args.restore:
            if target.exists():
                if target.read_bytes() != original:
                    raise FileExistsError(f"Refusing to replace different evidence: {target}")
                status = "already_exact"
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as stream:
                    stream.write(original)
                status = "restored"
        results.append({"path": row["original_path"], "sha256": row["original_sha256"], "status": status})
    print(json.dumps({"schema": "compressed-review-evidence-verification-v1", "passed": True,
                      "files": results}, indent=2))


if __name__ == "__main__":
    main()
