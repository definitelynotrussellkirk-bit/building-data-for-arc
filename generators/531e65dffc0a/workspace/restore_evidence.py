#!/usr/bin/env python3
"""Losslessly archive and restore large JSON evidence using only the stdlib.

No action operates without an explicit packet root. The default action restores
reports; ``verify`` checks archives without writing, and ``pack`` is explicit.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import tempfile


MANIFEST = "checks/COMPRESSED-EVIDENCE.json"
SCHEMA = "compressed-evidence/v1"
CHUNK = 65536


def safe_path(root, relative):
    if (not isinstance(relative, str) or "\\" in relative
            or any(part in ("", ".", "..") for part in relative.split("/"))):
        raise ValueError(f"unsafe evidence path: {relative!r}")
    parts = PurePosixPath(relative).parts
    if not parts or parts[0] != "checks" or PurePosixPath(relative).is_absolute():
        raise ValueError(f"evidence must remain under checks/: {relative!r}")
    current = root
    for i, part in enumerate(parts):
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink refused: {relative}")
        if current.exists() and i < len(parts) - 1 and not current.is_dir():
            raise ValueError(f"non-directory path component: {relative}")
    if current.exists() and not current.is_file():
        raise ValueError(f"expected a regular file: {relative}")
    return current


def file_digest(path):
    digest, size = hashlib.sha256(), 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK), b""):
            digest.update(chunk)
            size += len(chunk)
    return size, digest.hexdigest()


def check_file(path, size, digest):
    if file_digest(path) != (size, digest):
        raise ValueError(f"size/SHA-256 mismatch: {path}")


def read_manifest(root, *, optional=False):
    path = safe_path(root, MANIFEST)
    if not path.exists() and optional:
        return {"schema": SCHEMA, "entries": []}
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or document.get("schema") != SCHEMA:
        raise ValueError("unsupported compressed-evidence manifest")
    entries = document.get("entries")
    if not isinstance(entries, list):
        raise ValueError("manifest entries must be a list")
    originals, archives = set(), set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("invalid manifest entry")
        original, compressed = entry.get("original_path"), entry.get("compressed_path")
        safe_path(root, original)
        safe_path(root, compressed)
        if (not original.endswith(".json") or original == MANIFEST
                or compressed != original + ".gz"):
            raise ValueError("archive path must be the report's .json.gz sibling")
        if original in originals or compressed in archives:
            raise ValueError("duplicate manifest path")
        originals.add(original)
        archives.add(compressed)
        for prefix in ("original", "compressed"):
            size, digest = entry.get(prefix + "_bytes"), entry.get(prefix + "_sha256")
            if type(size) is not int or size < 0:
                raise ValueError("invalid manifest byte count")
            if (not isinstance(digest, str) or len(digest) != 64
                    or any(c not in "0123456789abcdef" for c in digest)):
                raise ValueError("invalid manifest SHA-256")
    return document


def write_manifest(root, document):
    path = safe_path(root, MANIFEST)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".evidence-manifest-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(document, handle, indent=2)
            handle.write("\n")
        safe_path(root, MANIFEST)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def decode_archive(path, entry, destination=None):
    """Read no more than declared size plus one decompressed byte."""
    check_file(path, entry["compressed_bytes"], entry["compressed_sha256"])
    digest, size = hashlib.sha256(), 0
    expected = entry["original_bytes"]
    with gzip.open(path, "rb") as handle:
        while True:
            chunk = handle.read(min(CHUNK, expected - size + 1))
            if not chunk:
                break
            size += len(chunk)
            if size > expected:
                raise ValueError(f"decompressed size exceeds manifest: {path}")
            digest.update(chunk)
            if destination is not None:
                destination.write(chunk)
    if (size, digest.hexdigest()) != (expected, entry["original_sha256"]):
        raise ValueError(f"decompressed size/SHA-256 mismatch: {path}")


def validate_entry(root, entry):
    original = safe_path(root, entry["original_path"])
    compressed = safe_path(root, entry["compressed_path"])
    decode_archive(compressed, entry)
    if original.exists():
        check_file(original, entry["original_bytes"], entry["original_sha256"])
    return original, compressed


def install_without_overwrite(temporary, destination, size, digest):
    # A hard link creates the destination exclusively, without replace races.
    try:
        os.link(temporary, destination)
    except FileExistsError:
        if destination.is_symlink():
            raise ValueError(f"symlink refused: {destination}")
        check_file(destination, size, digest)


def restore(root, document):
    # Verify every entry first, so a corrupt archive blocks all restoration.
    for entry in document["entries"]:
        validate_entry(root, entry)
    restored = 0
    for entry in document["entries"]:
        original = safe_path(root, entry["original_path"])
        if original.exists():
            continue
        original.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=".evidence-restore-", dir=original.parent)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                decode_archive(safe_path(root, entry["compressed_path"]), entry, handle)
            original = safe_path(root, entry["original_path"])
            install_without_overwrite(temporary, original,
                                      entry["original_bytes"], entry["original_sha256"])
            restored += 1
        finally:
            Path(temporary).unlink(missing_ok=True)
    return restored


def pack(root, threshold):
    document = read_manifest(root, optional=True)
    for entry in document["entries"]:
        validate_entry(root, entry)
    known = {entry["original_path"]: entry for entry in document["entries"]}
    checks = root / "checks"
    if checks.is_symlink() or (checks.exists() and not checks.is_dir()):
        raise ValueError("checks must be an ordinary directory")
    checks.mkdir(exist_ok=True)
    packed = 0
    for candidate in sorted(checks.rglob("*.json")):
        relative = candidate.relative_to(root).as_posix()
        if relative == MANIFEST:
            continue
        original = safe_path(root, relative)
        if relative in known:
            entry = known[relative]
            validate_entry(root, entry)
            original.unlink()
            packed += 1
            continue
        if original.stat().st_size < threshold:
            continue
        compressed_relative = relative + ".gz"
        compressed = safe_path(root, compressed_relative)
        descriptor, temporary = tempfile.mkstemp(prefix=".evidence-pack-", dir=original.parent)
        try:
            digest, size = hashlib.sha256(), 0
            with os.fdopen(descriptor, "wb") as target:
                with gzip.GzipFile(filename="", mode="wb", fileobj=target, mtime=0) as archive:
                    with original.open("rb") as source:
                        for chunk in iter(lambda: source.read(CHUNK), b""):
                            digest.update(chunk)
                            size += len(chunk)
                            archive.write(chunk)
            compressed_size, compressed_digest = file_digest(Path(temporary))
            entry = {"original_path": relative, "original_bytes": size,
                     "original_sha256": digest.hexdigest(),
                     "compressed_path": compressed_relative,
                     "compressed_bytes": compressed_size,
                     "compressed_sha256": compressed_digest}
            decode_archive(Path(temporary), entry)
            check_file(safe_path(root, relative), size, digest.hexdigest())
            install_without_overwrite(temporary, safe_path(root, compressed_relative),
                                      compressed_size, compressed_digest)
            document["entries"].append(entry)
            write_manifest(root, document)  # Retain the mapping before removal.
            validate_entry(root, entry)
            safe_path(root, relative).unlink()
            known[relative] = entry
            packed += 1
        finally:
            Path(temporary).unlink(missing_ok=True)
    write_manifest(root, document)
    return document, packed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", default="restore", choices=("restore", "verify", "pack"))
    parser.add_argument("--packet-root", required=True, type=Path)
    parser.add_argument("--threshold-bytes", type=int, default=128 * 1024,
                        help="pack reports at least this large (default 131072)")
    args = parser.parse_args()
    try:
        if args.packet_root.is_symlink() or not args.packet_root.is_dir():
            raise ValueError("packet root must be an existing ordinary directory")
        root = args.packet_root.resolve()
        if args.threshold_bytes < 1:
            raise ValueError("threshold must be positive")
        if args.action == "pack":
            document, changed = pack(root, args.threshold_bytes)
        else:
            document = read_manifest(root)
            if args.action == "restore":
                changed = restore(root, document)
            else:
                for entry in document["entries"]:
                    validate_entry(root, entry)
                changed = 0
        print(json.dumps({"action": args.action, "manifest": MANIFEST,
                          "entries": len(document["entries"]), "files_changed": changed,
                          "original_bytes": sum(e["original_bytes"] for e in document["entries"]),
                          "compressed_bytes": sum(e["compressed_bytes"] for e in document["entries"])}))
        return 0
    except (OSError, ValueError, TypeError, EOFError) as error:
        parser.exit(1, f"evidence error: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
