#!/usr/bin/env python3
"""Losslessly compact evidence while retaining a verified external original.

Example, run from the packet root:
    python3 compact_evidence.py compact WORK/checks/report.json \
        --root . --manifest evidence-manifest.json \
        --retain-original /external/retained-evidence
    python3 compact_evidence.py restore evidence-manifest.json --root restored

On compact, FILE and MANIFEST are relative to --root unless absolute. The
manifest must be in an ancestor directory of FILE. The retained directory
must be outside --root; the original relative path is preserved beneath it.
On restore, MANIFEST is relative to the current directory unless absolute.
Compressed paths are relative to the manifest directory; original paths are
relative to the restoration root. Moving the packet does not break this map.

Outputs are published atomically without overwriting existing paths. Errors
before input removal keep the input and completed recovery copies. The input
is removed only after both recovery copies and the manifest verify. A later
directory-sync error can therefore leave the input absent, with all verified
recovery artifacts available for restoration. Temporary unfinished writes are removed.
Only the Python standard library is required.
"""

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile


SCHEMA = "lossless-evidence-compaction-v1"
CHUNK_SIZE = 1024 * 1024


class EvidenceError(Exception):
    """An unsafe path, collision, or integrity failure."""


def _relative_parts(value, label):
    if not isinstance(value, str) or not value:
        raise EvidenceError(f"{label} must be a nonempty relative path")
    parts = value.split("/")
    if (any(part in ("", ".", "..") for part in parts)
            or "\\" in value or ":" in value
            or any(ord(character) < 32 for character in value)):
        raise EvidenceError(f"{label} is not a safe relative path: {value!r}")
    return parts


def _safe_join(root, relative, label):
    path = root
    for part in _relative_parts(relative, label):
        path = path / part
        if path.is_symlink():
            raise EvidenceError(f"{label} contains a symlink: {relative!r}")
    if not path.resolve().is_relative_to(root):
        raise EvidenceError(f"{label} escapes its root")
    return path


def _root_path(root, value, label):
    path = Path(value)
    if path.is_absolute():
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError as error:
            raise EvidenceError(f"{label} must be inside --root") from error
    else:
        relative = os.fspath(value)
    return _safe_join(root, relative, label), relative


def _require_file(path, label):
    if not path.is_file() or path.is_symlink():
        raise EvidenceError(f"{label} is missing or is not a regular file: {path}")


def _require_new(path):
    if path.exists() or path.is_symlink():
        raise EvidenceError(f"refusing to overwrite existing path: {path}")


def _stream_digest(source, destination=None, limit=None):
    digest = hashlib.sha256()
    size = 0
    while True:
        block = source.read(CHUNK_SIZE)
        if not block:
            break
        size += len(block)
        if limit is not None and size > limit:
            raise EvidenceError("decompressed data exceeds the declared size")
        digest.update(block)
        if destination is not None:
            destination.write(block)
    return size, digest.hexdigest()


def _file_digest(path):
    with path.open("rb") as source:
        return _stream_digest(source)


def _expect(actual, expected, label):
    if actual != expected:
        raise EvidenceError(f"{label} byte count or SHA-256 does not match")


def _sync_directory(path):
    if os.name != "nt":
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _atomic_new(path, write):
    """Publish one complete file with an exclusive, atomic hard-link operation."""
    _require_new(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as destination:
            write(destination)
            destination.flush()
            os.fsync(destination.fileno())
        # os.replace would overwrite a path created after the preflight check.
        os.link(temporary, path)
        _sync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def _record(relative, digest):
    return {"path": relative, "size_bytes": digest[0], "sha256": digest[1]}


def _validate_record(record, label):
    if not isinstance(record, dict):
        raise EvidenceError(f"manifest {label} must be an object")
    relative = record.get("path")
    _relative_parts(relative, f"manifest {label}.path")
    size = record.get("size_bytes")
    digest = record.get("sha256")
    if type(size) is not int or size < 0:
        raise EvidenceError(f"manifest {label}.size_bytes must be nonnegative")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise EvidenceError(f"manifest {label}.sha256 must be a SHA-256 hex digest")
    return relative, (size, digest)


def compact(file, *, root, manifest, retain_original):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise EvidenceError("--root must be a directory")
    original, original_relative = _root_path(root, file, "FILE")
    manifest_path, _ = _root_path(root, manifest, "MANIFEST")
    compressed, _ = _root_path(root, original_relative + ".gz", "compressed path")
    _require_file(original, "FILE")
    try:
        compressed_relative = compressed.relative_to(manifest_path.parent).as_posix()
    except ValueError as error:
        raise EvidenceError("MANIFEST must be in an ancestor directory of FILE") from error

    retained_root = Path(retain_original).resolve()
    if retained_root.is_relative_to(root):
        raise EvidenceError("--retain-original must be outside --root")
    retained = _safe_join(retained_root, original_relative, "retained path")
    if retained.is_relative_to(root):
        raise EvidenceError("retained original must be outside --root")
    if len({original, compressed, manifest_path, retained}) != 4:
        raise EvidenceError("input, manifest, compressed, and retained paths must differ")
    for output in (compressed, manifest_path, retained):
        _require_new(output)

    original_digest = _file_digest(original)

    def copy_original(destination):
        with original.open("rb") as source:
            _expect(_stream_digest(source, destination), original_digest, "retained copy")

    _atomic_new(retained, copy_original)
    _expect(_file_digest(retained), original_digest, "retained copy")

    def compress_original(destination):
        with retained.open("rb") as source:
            with gzip.GzipFile(filename="", mode="wb", fileobj=destination,
                               compresslevel=9, mtime=0) as archive:
                _expect(_stream_digest(source, archive), original_digest, "compression input")

    _atomic_new(compressed, compress_original)
    compressed_digest = _file_digest(compressed)
    with gzip.open(compressed, "rb") as source:
        _expect(_stream_digest(source, limit=original_digest[0]),
                original_digest, "decompressed copy")

    document = {
        "schema": SCHEMA,
        "compression": "gzip",
        "original": _record(original_relative, original_digest),
        "compressed": _record(compressed_relative, compressed_digest),
        "retained_copy": {"path": original_relative},
        "path_bases": {
            "original": "restoration --root directory",
            "compressed": "manifest directory",
            "retained_copy": "compaction --retain-original directory",
        },
        "restore_command": "python3 compact_evidence.py restore MANIFEST --root DEST",
    }
    encoded = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _atomic_new(manifest_path, lambda destination: destination.write(encoded))

    # Every published recovery artifact is checked before unlinking the input.
    _expect(_file_digest(manifest_path),
            (len(encoded), hashlib.sha256(encoded).hexdigest()), "manifest")
    _expect(_file_digest(retained), original_digest, "retained copy")
    _expect(_file_digest(compressed), compressed_digest, "compressed copy")
    _expect(_file_digest(original), original_digest, "original before removal")
    original.unlink()
    _sync_directory(original.parent)
    return document


def restore(manifest, *, root):
    manifest_path = Path(manifest).absolute()
    _require_file(manifest_path, "MANIFEST")
    manifest_path = manifest_path.resolve(strict=True)
    if manifest_path.stat().st_size > CHUNK_SIZE:
        raise EvidenceError("manifest is larger than the 1 MiB limit")
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (not isinstance(document, dict) or document.get("schema") != SCHEMA
            or document.get("compression") != "gzip"):
        raise EvidenceError("unsupported evidence manifest schema or compression")
    original_relative, original_digest = _validate_record(document.get("original"), "original")
    compressed_relative, compressed_digest = _validate_record(document.get("compressed"), "compressed")
    retained = document.get("retained_copy")
    if not isinstance(retained, dict):
        raise EvidenceError("manifest retained_copy must be an object")
    _relative_parts(retained.get("path"), "manifest retained_copy.path")
    compressed = _safe_join(manifest_path.parent, compressed_relative, "compressed path")
    _require_file(compressed, "compressed evidence")

    restoration_root = Path(root).resolve()
    if restoration_root.exists() and not restoration_root.is_dir():
        raise EvidenceError("restoration --root must be a directory")
    destination = _safe_join(restoration_root, original_relative, "restoration path")
    _require_new(destination)
    _expect(_file_digest(compressed), compressed_digest, "compressed copy")

    def decompress(destination_stream):
        with gzip.open(compressed, "rb") as source:
            _expect(_stream_digest(source, destination_stream, limit=original_digest[0]),
                    original_digest, "restored original")

    _atomic_new(destination, decompress)
    _expect(_file_digest(destination), original_digest, "restored original")
    return _record(original_relative, original_digest)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    compact_parser = commands.add_parser("compact", help="retain and gzip one evidence file")
    compact_parser.add_argument("file", help="file relative to --root, or an absolute path inside it")
    compact_parser.add_argument("--root", default=".", help="packet root (default: current directory)")
    compact_parser.add_argument("--manifest", required=True, help="new manifest path inside --root")
    compact_parser.add_argument("--retain-original", required=True, help="external directory for the original")
    restore_parser = commands.add_parser("restore", help="restore original bytes from a manifest")
    restore_parser.add_argument("manifest")
    restore_parser.add_argument("--root", required=True, help="destination root for original relative paths")
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "compact":
            result = compact(arguments.file, root=arguments.root, manifest=arguments.manifest,
                             retain_original=arguments.retain_original)
        else:
            result = restore(arguments.manifest, root=arguments.root)
    except (EvidenceError, OSError, ValueError, EOFError) as error:
        print(f"evidence compaction error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
