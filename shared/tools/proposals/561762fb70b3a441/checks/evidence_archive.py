#!/usr/bin/env python3
"""Lossless deterministic gzip packing and verified evidence restoration."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

SCHEMA = "arc-review-evidence-archive-v1"
CHUNK = 1024 * 1024


def safe_path(root, relative):
    if (not isinstance(relative, str) or not relative or "\\" in relative
            or relative.startswith("/") or any(p in ("", ".", "..") for p in relative.split("/"))):
        raise ValueError(f"unsafe relative path: {relative!r}")
    path = root
    for part in relative.split("/"):
        path = path / part
        if path.is_symlink():
            raise ValueError(f"symlink refused: {relative}")
    return path


def digest(path):
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"expected regular file: {path}")
    size, h = 0, hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK), b""):
            size += len(chunk)
            h.update(chunk)
    return size, h.hexdigest()


def sync_directory(directory):
    fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def save_manifest(path, manifest):
    missing = []
    ancestor = path.parent
    while not ancestor.exists():
        missing.append(ancestor)
        ancestor = ancestor.parent
    path.parent.mkdir(parents=True, exist_ok=True)
    for directory in reversed(missing):
        sync_directory(directory.parent)
    fd, temporary = tempfile.mkstemp(prefix=".evidence-index-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(manifest, out, indent=2, sort_keys=True)
            out.write("\n")
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, path)
        sync_directory(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_manifest(root, relative, *, allow_missing=False):
    path = safe_path(root, relative)
    if not path.exists() and allow_missing:
        return path, {"schema": SCHEMA, "entries": []}
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema") != SCHEMA or not isinstance(manifest.get("entries"), list):
        raise ValueError("invalid evidence manifest")
    seen = set()
    for entry in manifest["entries"]:
        if not isinstance(entry, dict):
            raise ValueError("invalid evidence entry")
        original, compressed = entry.get("original_path"), entry.get("compressed_path")
        safe_path(root, original)
        safe_path(root, compressed)
        if (original in seen or compressed in seen or compressed != original + ".gz"
                or relative in (original, compressed)):
            raise ValueError("duplicate, conflicting, or nonstandard archive path")
        seen.update((original, compressed))
        for field in ("original_bytes", "compressed_bytes"):
            if type(entry.get(field)) is not int or entry[field] < 0:
                raise ValueError(f"invalid {field}")
        for field in ("original_sha256", "compressed_sha256"):
            if not isinstance(entry.get(field), str) or not re.fullmatch("[0-9a-f]{64}", entry[field]):
                raise ValueError(f"invalid {field}")
    return path, manifest


def verify_entry(root, entry):
    archive = safe_path(root, entry["compressed_path"])
    if digest(archive) != (entry["compressed_bytes"], entry["compressed_sha256"]):
        raise ValueError(f"compressed hash/size mismatch: {entry['compressed_path']}")
    size, h = 0, hashlib.sha256()
    with gzip.open(archive, "rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK), b""):
            size += len(chunk)
            h.update(chunk)
    if (size, h.hexdigest()) != (entry["original_bytes"], entry["original_sha256"]):
        raise ValueError(f"restored hash/size mismatch: {entry['original_path']}")
    original = safe_path(root, entry["original_path"])
    if original.exists() and digest(original) != (size, h.hexdigest()):
        raise ValueError(f"differing existing original refused: {entry['original_path']}")


def pack(root, manifest_relative, paths):
    manifest_path, manifest = load_manifest(root, manifest_relative, allow_missing=True)
    for old in manifest["entries"]:
        verify_entry(root, old)
    known = {e["original_path"]: e for e in manifest["entries"]}
    for relative in paths:
        source = safe_path(root, relative)
        target = safe_path(root, relative + ".gz")
        if manifest_relative in (relative, relative + ".gz"):
            raise ValueError("cannot archive the manifest itself")
        if relative in known:
            verify_entry(root, known[relative])
            if source.exists():
                save_manifest(manifest_path, manifest)
                source.unlink()
                sync_directory(source.parent)
            continue
        if any(relative == e["compressed_path"] or relative + ".gz" == e["original_path"]
               for e in manifest["entries"]):
            raise ValueError(f"archive path conflicts with a tracked entry: {relative}")
        if target.exists():
            raise ValueError(f"untracked existing gzip refused: {relative}.gz")
        original_size, original_hash = digest(source)
        fd, temporary = tempfile.mkstemp(prefix=".evidence-gzip-", dir=source.parent)
        try:
            with os.fdopen(fd, "wb") as out:
                with source.open("rb") as inp, gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=0) as gz:
                    shutil.copyfileobj(inp, gz, CHUNK)
                out.flush()
                os.fsync(out.fileno())
            # link creates a destination atomically and refuses existing files.
            os.link(temporary, target)
            sync_directory(target.parent)
            compressed_size, compressed_hash = digest(target)
            entry = {"original_path": relative, "compressed_path": relative + ".gz",
                     "original_bytes": original_size, "compressed_bytes": compressed_size,
                     "original_sha256": original_hash, "compressed_sha256": compressed_hash}
            verify_entry(root, entry)
            manifest["entries"].append(entry)
            save_manifest(manifest_path, manifest)  # durable before original removal
            known[relative] = entry
            if digest(source) != (original_size, original_hash):
                raise ValueError(f"source changed while packing: {relative}")
            source.unlink()
            sync_directory(source.parent)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return len(paths), len(manifest["entries"])


def restore(root, entries):
    # Preflight every entry before writing any restored file.
    for entry in entries:
        verify_entry(root, entry)
    created = 0
    for entry in entries:
        output = safe_path(root, entry["original_path"])
        if output.exists():
            continue  # exact existing bytes were verified above
        output.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".evidence-restore-", dir=output.parent)
        try:
            with os.fdopen(fd, "wb") as out, gzip.open(safe_path(root, entry["compressed_path"]), "rb") as inp:
                shutil.copyfileobj(inp, out, CHUNK)
                out.flush()
                os.fsync(out.fileno())
            if digest(Path(temporary)) != (entry["original_bytes"], entry["original_sha256"]):
                raise ValueError(f"restoration verification failed: {entry['original_path']}")
            os.link(temporary, output)  # never clobber a concurrent/differing file
            sync_directory(output.parent)
            created += 1
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return created


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("pack", "verify", "restore"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--root", required=True, type=Path)
        cmd.add_argument("--manifest", default="checks/EVIDENCE_INDEX.json")
        if name == "pack":
            cmd.add_argument("paths", nargs="+")
    args = parser.parse_args()
    try:
        if args.root.is_symlink() or not args.root.is_dir():
            raise ValueError("root must be an existing directory, not a symlink")
        root = args.root.resolve()
        if args.command == "pack":
            processed, count = pack(root, args.manifest, args.paths)
            result = {"command": "pack", "processed": processed, "entries": count}
        else:
            _, manifest = load_manifest(root, args.manifest)
            entries = manifest["entries"]
            if args.command == "verify":
                for entry in entries:
                    verify_entry(root, entry)
                result = {"command": "verify", "verified": len(entries)}
            else:
                result = {"command": "restore", "restored": restore(root, entries), "entries": len(entries)}
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, KeyError, EOFError) as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
