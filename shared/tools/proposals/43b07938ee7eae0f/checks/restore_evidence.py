"""Restore losslessly compressed review evidence, verifying bytes and paths.

Run from the returned packet root: python3 checks/restore_evidence.py
Use --root to select an extracted return containing checks/compressed-evidence.json.
Existing files are accepted only when their exact recorded hash already matches.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def scoped(root, name):
    path = PurePosixPath(name)
    if (not name.startswith("checks/") or path.is_absolute() or ".." in path.parts
            or "\\" in name or path.as_posix() != name):
        raise ValueError(f"unsafe evidence path: {name!r}")
    target = root.joinpath(*path.parts)
    for current in (target, *target.parents):
        if current == root:
            break
        if current.is_symlink():
            raise ValueError(f"symlink evidence path: {name!r}")
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = json.loads((root / "checks/compressed-evidence.json").read_text())
    if manifest.get("schema") != "arcpuzzles-lossless-evidence-v1":
        raise ValueError("unsupported compression manifest")
    for row in manifest["files"]:
        original = scoped(root, row["original_path"])
        compressed = scoped(root, row["compressed_path"])
        size = row["original_bytes"]
        if type(size) is not int or not 0 <= size <= 100 * 1024 * 1024:
            raise ValueError("invalid or excessive recorded byte size")
        if digest(compressed.read_bytes()) != row["compressed_sha256"]:
            raise ValueError(f"compressed hash mismatch: {compressed}")
        with gzip.open(compressed, "rb") as handle:
            raw = handle.read(size + 1)
        if len(raw) != size or digest(raw) != row["original_sha256"]:
            raise ValueError(f"restored byte/hash mismatch: {original}")
        if original.exists():
            if not original.is_file() or digest(original.read_bytes()) != row["original_sha256"]:
                raise FileExistsError(f"refusing to overwrite differing evidence: {original}")
        else:
            original.parent.mkdir(parents=True, exist_ok=True)
            with original.open("xb") as handle:
                handle.write(raw)
        print(f"verified {row['original_path']} ({size} bytes)")
    print(f"Restored or verified {len(manifest['files'])} evidence files.")


if __name__ == "__main__":
    main()
