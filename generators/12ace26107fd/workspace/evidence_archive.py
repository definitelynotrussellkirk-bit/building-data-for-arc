#!/usr/bin/env python3
"""Losslessly pack explicitly selected files under an explicit WORK root.

Usage: python evidence_archive.py --root /path/to/WORK pack checks/report.json
       python evidence_archive.py --root /path/to/WORK verify
       python evidence_archive.py --root /path/to/WORK restore
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile

SCHEMA = "arc-review-evidence-archive-v1"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe(root, name):
    if (not isinstance(name, str) or not name or "\\" in name or "\x00" in name
            or name.startswith("/") or any(p in ("", ".", "..") for p in name.split("/"))):
        raise ValueError(f"unsafe relative path: {name!r}")
    target = root.joinpath(*PurePosixPath(name).parts)
    current = root
    for part in PurePosixPath(name).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink refused: {name}")
    if not target.resolve().is_relative_to(root):
        raise ValueError(f"path escapes root: {name}")
    return target


def decode(root, row):
    packed = safe(root, row["compressed_path"]).read_bytes()
    if len(packed) != row["compressed_bytes"] or sha(packed) != row["compressed_sha256"]:
        raise ValueError(f"compressed size/hash mismatch: {row['compressed_path']}")
    with gzip.GzipFile(fileobj=io.BytesIO(packed)) as stream:
        raw = stream.read(row["original_bytes"] + 1)
    if len(raw) != row["original_bytes"] or sha(raw) != row["original_sha256"]:
        raise ValueError(f"original size/hash mismatch: {row['original_path']}")
    return raw


def validate(root, value, manifest_name):
    if not isinstance(value, dict) or value.get("schema") != SCHEMA or not isinstance(value.get("entries"), list):
        raise ValueError("invalid archive manifest schema/entries")
    originals, compressed = set(), set()
    for row in value["entries"]:
        if not isinstance(row, dict):
            raise ValueError("invalid manifest entry")
        for prefix in ("original", "compressed"):
            safe(root, row.get(prefix + "_path"))
            size, checksum = row.get(prefix + "_bytes"), row.get(prefix + "_sha256")
            if type(size) is not int or size < 0 or not isinstance(checksum, str) or not re.fullmatch("[0-9a-f]{64}", checksum):
                raise ValueError("invalid manifest size/hash")
        original, packed = row["original_path"], row["compressed_path"]
        if original in originals or packed in compressed or not packed.endswith(".gz"):
            raise ValueError("duplicate or invalid archive member")
        originals.add(original); compressed.add(packed)
    paths = originals | compressed | {manifest_name}
    if originals & compressed or manifest_name in originals | compressed:
        raise ValueError("archive paths collide")
    for name in paths:
        if any(parent.as_posix() in paths for parent in PurePosixPath(name).parents):
            raise ValueError(f"file/directory path collision: {name}")


def write_same_or_new(path, raw):
    if path.exists():
        if not path.is_file() or path.read_bytes() != raw:
            raise FileExistsError(f"refusing overwrite conflict: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)


def run(root, action, names, manifest_name, archive_dir):
    manifest_path = safe(root, manifest_name)
    safe(root, archive_dir)
    previous = manifest_path.read_bytes() if manifest_path.exists() else None
    value = json.loads(previous) if previous is not None else {"schema": SCHEMA, "compression": "gzip", "entries": []}
    validate(root, value, manifest_name)
    # Verify every already-retained dependency before changing anything.
    verified = {row["original_path"]: decode(root, row) for row in value["entries"]}
    if action != "pack" and previous is None:
        raise FileNotFoundError(manifest_path)
    if action == "pack":
        if not names:
            raise ValueError("pack requires explicit relative file paths")
        selected = []
        rows = {row["original_path"]: row for row in value["entries"]}
        for name in sorted(set(names)):
            source = safe(root, name)
            if name == manifest_name or name == archive_dir or name.startswith(archive_dir + "/"):
                raise ValueError(f"cannot pack archive metadata/dependencies: {name}")
            if name in rows:
                raw = verified[name]
                if source.exists() and (not source.is_file() or source.read_bytes() != raw):
                    raise FileExistsError(f"recreated original has different bytes: {name}")
                selected.append((source, raw, None, rows[name]))
                continue
            if not source.is_file():
                raise ValueError(f"not a regular file: {name}")
            raw = source.read_bytes()
            encoded = gzip.compress(raw, compresslevel=9, mtime=0)
            row = {"original_path": name, "original_bytes": len(raw), "original_sha256": sha(raw),
                   "compressed_path": archive_dir + "/" + name + ".gz",
                   "compressed_bytes": len(encoded), "compressed_sha256": sha(encoded)}
            destination = safe(root, row["compressed_path"])
            if destination.exists() and (not destination.is_file() or destination.read_bytes() != encoded):
                raise FileExistsError(f"compressed destination conflict: {destination}")
            selected.append((source, raw, encoded, row)); value["entries"].append(row)
        value["entries"].sort(key=lambda row: row["original_path"])
        validate(root, value, manifest_name)
        # Persist and re-read each gzip; all raw files still exist here.
        for source, raw, encoded, row in selected:
            if encoded is not None:
                write_same_or_new(safe(root, row["compressed_path"]), encoded)
            if decode(root, row) != raw:
                raise ValueError("gzip round-trip mismatch")
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        current = manifest_path.read_bytes() if manifest_path.exists() else None
        if current != previous:
            raise FileExistsError("manifest changed during pack; raw files retained")
        manifest_raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
        with tempfile.NamedTemporaryFile(dir=manifest_path.parent, prefix="archive-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(manifest_raw)
        try:
            os.replace(temporary, manifest_path)
        finally:
            temporary.unlink(missing_ok=True)
        # The durable mapping and verified gzip exist before removing raw.
        for source, raw, encoded, row in selected:
            if source.exists():
                safe(root, row["original_path"])
                if source.read_bytes() != raw:
                    raise FileExistsError("original changed during pack; refusing removal")
                source.unlink()
    elif action == "restore":
        # Preflight the complete restore before writing any missing original.
        for row in value["entries"]:
            target = safe(root, row["original_path"])
            if target.exists() and (not target.is_file() or target.read_bytes() != verified[row["original_path"]]):
                raise FileExistsError(f"refusing restore overwrite conflict: {target}")
        for row in value["entries"]:
            write_same_or_new(safe(root, row["original_path"]), verified[row["original_path"]])
    return {"action": action, "files": len(value["entries"]),
            "original_bytes": sum(row["original_bytes"] for row in value["entries"]),
            "compressed_bytes": sum(row["compressed_bytes"] for row in value["entries"]),
            "manifest": manifest_name}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="explicit WORK directory; never inferred")
    parser.add_argument("--manifest", default="checks/ARCHIVE-MANIFEST.json")
    parser.add_argument("--archive-dir", default="checks/archived")
    parser.add_argument("action", choices=("pack", "verify", "restore"))
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args(argv)
    try:
        root = args.root.absolute()
        if not root.is_dir() or any(path.is_symlink() for path in (root, *root.parents)):
            raise ValueError("--root must be an existing directory without symlinks")
        root = root.resolve()
        if args.action != "pack" and args.paths:
            raise ValueError("only pack accepts selected paths")
        print(json.dumps(run(root, args.action, args.paths, args.manifest, args.archive_dir), sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, EOFError) as exc:
        parser.exit(1, f"archive error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
