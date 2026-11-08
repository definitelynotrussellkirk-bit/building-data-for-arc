#!/usr/bin/env python3
"""Compress explicitly selected evidence and restore exact bytes; stdlib only."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys

SCHEMA = "arcpuzzles-evidence-gzip-v1"
CHUNK = 1024 * 1024


def relative(value):
    if (not isinstance(value, str) or not value or "\\" in value or "\0" in value
            or value.startswith("/") or any(p in {"", ".", ".."} for p in value.split("/"))):
        raise ValueError(f"unsafe relative path: {value!r}")
    return PurePosixPath(value)


def no_symlinks(path):
    path = Path(path).absolute()
    for part in [*reversed(path.parents), path]:
        if part.is_symlink():
            raise ValueError(f"symlink forbidden: {part}")
    return path


def directory(path):
    path = no_symlinks(path)
    if not path.is_dir():
        raise ValueError(f"directory missing: {path}")
    return path


def regular(path):
    path = no_symlinks(path)
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError(f"regular file required: {path}")
    return path


def fresh(path):
    path = no_symlinks(path)
    directory(path.parent)
    if path.exists():
        raise ValueError(f"output must be a new directory: {path}")
    return path


def fingerprint(path):
    with regular(path).open("rb") as stream:
        digest = hashlib.sha256()
        size = 0
        while chunk := stream.read(CHUNK):
            size += len(chunk)
            digest.update(chunk)
    return size, digest.hexdigest()


def collisions(paths):
    seen = set()
    for name in paths:
        relative(name)
        if name in seen:
            raise ValueError(f"duplicate path: {name}")
        seen.add(name)
    for name in seen:
        if any(str(parent) in seen for parent in PurePosixPath(name).parents if str(parent) != "."):
            raise ValueError(f"file/directory path collision: {name}")


def manifest(bundle):
    bundle = directory(bundle)
    data = json.loads(regular(bundle / "MANIFEST.json").read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError("invalid manifest schema")
    rows = data.get("files")
    if not isinstance(rows, list) or not rows:
        raise ValueError("manifest needs a nonempty files list")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid manifest file row")
        relative(row.get("path"))
        relative(row.get("compressed_path"))
        if row["compressed_path"] != row["path"] + ".gz":
            raise ValueError("compressed path must be original path plus .gz")
        for field in ("raw_size", "compressed_size"):
            if type(row.get(field)) is not int or row[field] < 0:
                raise ValueError(f"invalid {field}")
        for field in ("raw_sha256", "compressed_sha256"):
            if not isinstance(row.get(field), str) or not re.fullmatch("[0-9a-f]{64}", row[field]):
                raise ValueError(f"invalid {field}")
    collisions([row["path"] for row in rows])
    collisions(["MANIFEST.json", *[row["compressed_path"] for row in rows]])
    return bundle, rows


def unpack_stream(bundle, row, target=None):
    path = regular(bundle / row["compressed_path"])
    if fingerprint(path) != (row["compressed_size"], row["compressed_sha256"]):
        raise ValueError(f"compressed size/hash mismatch: {row['path']}")
    size, digest = 0, hashlib.sha256()
    with gzip.open(path, "rb") as stream:
        while chunk := stream.read(min(CHUNK, row["raw_size"] - size + 1)):
            size += len(chunk)
            if size > row["raw_size"]:
                raise ValueError(f"expanded size exceeds manifest: {row['path']}")
            digest.update(chunk)
            if target is not None:
                target.write(chunk)
    if (size, digest.hexdigest()) != (row["raw_size"], row["raw_sha256"]):
        raise ValueError(f"raw size/hash mismatch: {row['path']}")


def verify(bundle):
    bundle, rows = manifest(bundle)
    for row in rows:
        unpack_stream(bundle, row)
    return rows


def compress(root, out, names, remove_originals=False):
    root, out = directory(root), fresh(out)
    collisions(names)
    collisions(["MANIFEST.json", *[name + ".gz" for name in names]])
    sources = [regular(root / str(relative(name))) for name in names]
    # Every source is preflighted before the output exists or any source is removed.
    out.mkdir()
    rows = []
    try:
        for name, source in sorted(zip(names, sources)):
            destination = out / (name + ".gz")
            destination.parent.mkdir(parents=True, exist_ok=True)
            size, digest = 0, hashlib.sha256()
            with source.open("rb") as original, destination.open("xb") as compressed:
                with gzip.GzipFile(fileobj=compressed, mode="wb", filename="", mtime=0,
                                   compresslevel=9) as stream:
                    while chunk := original.read(CHUNK):
                        size += len(chunk)
                        digest.update(chunk)
                        stream.write(chunk)
                compressed.flush()
                os.fsync(compressed.fileno())
            packed_size, packed_hash = fingerprint(destination)
            rows.append({"path": name, "raw_size": size, "raw_sha256": digest.hexdigest(),
                         "compressed_path": name + ".gz", "compressed_size": packed_size,
                         "compressed_sha256": packed_hash})
        with (out / "MANIFEST.json").open("x", encoding="utf-8") as stream:
            json.dump({"schema": SCHEMA, "files": rows}, stream, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        verify(out)
        for row in rows:
            if fingerprint(root / row["path"]) != (row["raw_size"], row["raw_sha256"]):
                raise ValueError(f"source changed during compression: {row['path']}")
    except Exception:
        shutil.rmtree(out)
        raise
    if remove_originals:
        # The complete bundle has been verified before removal starts. A removal error
        # keeps the complete bundle, allowing restoration even after partial removal.
        for row in rows:
            source = regular(root / row["path"])
            if fingerprint(source) != (row["raw_size"], row["raw_sha256"]):
                raise ValueError(f"source changed before removal; bundle retained: {row['path']}")
            source.unlink()
    return rows


def restore(bundle, out):
    bundle, out = directory(bundle), fresh(out)
    rows = verify(bundle)
    out.mkdir()
    try:
        for row in rows:
            path = out / row["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            no_symlinks(path)
            with path.open("xb") as stream:
                unpack_stream(bundle, row, stream)
                stream.flush()
                os.fsync(stream.fileno())
    except Exception:
        shutil.rmtree(out)
        raise
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    pack = commands.add_parser("compress")
    pack.add_argument("--root", type=Path, required=True)
    pack.add_argument("--out", type=Path, required=True)
    pack.add_argument("--remove-originals", action="store_true")
    pack.add_argument("files", nargs="+", help="individual POSIX paths relative to --root")
    check = commands.add_parser("verify")
    check.add_argument("--bundle", type=Path, required=True)
    restore_parser = commands.add_parser("restore")
    restore_parser.add_argument("--bundle", type=Path, required=True)
    restore_parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "compress":
            rows = compress(args.root, args.out, args.files, args.remove_originals)
        elif args.command == "verify":
            rows = verify(args.bundle)
        else:
            rows = restore(args.bundle, args.out)
        print(json.dumps({"status": "verified", "command": args.command, "files": len(rows),
                          "raw_bytes": sum(row["raw_size"] for row in rows),
                          "compressed_bytes": sum(row["compressed_size"] for row in rows)}, sort_keys=True))
        return 0
    except (OSError, ValueError, EOFError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
