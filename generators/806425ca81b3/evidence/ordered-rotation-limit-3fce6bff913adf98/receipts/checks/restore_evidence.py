"""Verify or restore this return's exact-byte gzip evidence.

From the extracted return root:
    python3 checks/restore_evidence.py
    python3 checks/restore_evidence.py --out /path/to/new-directory

The manifest uses the existing review-large-evidence-v1 retention contract.
No returned generator, rival or other reviewer code is imported or executed.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="new output directory; omit to verify only")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    manifest = json.loads((root / "checks/evidence-archives.json").read_text())
    if args.out is not None and args.out.exists():
        raise SystemExit("Refusing to overwrite an existing output directory")
    restored = []
    for entry in manifest["files"]:
        for key in ("original_path", "compressed_path"):
            path = PurePosixPath(entry[key])
            if path.is_absolute() or ".." in path.parts or path.parts[0] != "checks":
                raise SystemExit(f"Unsafe evidence path: {path}")
        packed = (root / entry["compressed_path"]).read_bytes()
        raw = gzip.decompress(packed)
        for label, data in (("compressed", packed), ("original", raw)):
            if len(data) != entry[f"{label}_bytes"]:
                raise SystemExit(f"Size mismatch: {entry['original_path']} ({label})")
            if hashlib.sha256(data).hexdigest() != entry[f"{label}_sha256"]:
                raise SystemExit(f"SHA-256 mismatch: {entry['original_path']} ({label})")
        restored.append((entry["original_path"], raw))
    if args.out is not None:
        args.out.mkdir(parents=True)
        for name, raw in restored:
            dest = args.out / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(raw)
    print(json.dumps({"verified_files": len(restored),
                      "original_bytes": sum(len(raw) for _, raw in restored),
                      "restored_to": str(args.out.resolve()) if args.out else None}))


if __name__ == "__main__":
    main()
