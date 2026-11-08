#!/usr/bin/env python3
"""Verify archived evidence or restore it beneath an explicit destination.

Only declared regular members are copied. No tar extraction API is used.
Existing destination files and symlink ancestors are always rejected.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import shutil
import tarfile


def stream_digest(stream):
    digest = hashlib.sha256()
    size = 0
    while chunk := stream.read(1024 * 1024):
        digest.update(chunk)
        size += len(chunk)
    return size, digest.hexdigest()


def file_digest(path):
    with path.open("rb") as stream:
        return stream_digest(stream)


def safe_relative(value):
    if not isinstance(value, str) or "\\" in value or "\0" in value:
        raise ValueError(f"unsafe evidence path: {value!r}")
    path = PurePosixPath(value)
    if (path.is_absolute() or path.as_posix() != value or not path.parts
            or path.parts[0] != "checks" or any(part in ("", ".", "..") or ":" in part for part in path.parts)):
        raise ValueError(f"unsafe evidence path: {value!r}")
    return path


def load_manifest(path):
    manifest = json.loads(path.read_text())
    if manifest.get("schema") != "arc-review-tar-members-v1":
        raise ValueError("unrecognized member manifest")
    originals = set()
    directories = set(manifest["directories"])
    for directory in directories:
        safe_relative(directory)
    archive_names = set()
    for archive in manifest["archives"]:
        name = archive["archive_file"]
        if PurePosixPath(name).name != name or not name.endswith(".tar.gz"):
            raise ValueError(f"unsafe archive filename: {name!r}")
        if name in archive_names:
            raise ValueError(f"duplicate archive: {name}")
        archive_names.add(name)
    for row in manifest["files"]:
        original = row["original_path"]
        safe_relative(original)
        if original in originals or original in directories:
            raise ValueError(f"duplicate or colliding original: {original}")
        if row["archive_file"] not in archive_names:
            raise ValueError(f"undeclared archive for {original}")
        originals.add(original)
    links = set()
    for row in manifest["symlinks"]:
        original = safe_relative(row["original_path"])
        if str(original) in originals | links | directories:
            raise ValueError(f"symlink path collision: {original}")
        target = row["portable_target"]
        if not isinstance(target, str) or PurePosixPath(target).is_absolute() or "\\" in target or "\0" in target:
            raise ValueError(f"unsafe symlink target: {target!r}")
        resolved = posixpath.normpath(posixpath.join(str(original.parent), target))
        safe_relative(resolved)
        if resolved != row["target_path"] or resolved not in originals | directories:
            raise ValueError(f"symlink target is not a declared internal member: {target!r}")
        target_bytes = os.fsencode(row["original_target"])
        if (len(target_bytes) != row["original_target_bytes"]
                or hashlib.sha256(target_bytes).hexdigest() != row["original_target_sha256"]):
            raise ValueError("original symlink-target metadata changed")
        links.add(str(original))
    non_directories = originals | links
    for item in non_directories | directories:
        if any(str(parent) in non_directories for parent in PurePosixPath(item).parents):
            raise ValueError(f"file/link used as a parent directory: {item}")
    return manifest


def verify(manifest_path):
    manifest_path = Path(manifest_path).resolve()
    manifest = load_manifest(manifest_path)
    verified_count = 0
    for archive in manifest["archives"]:
        path = manifest_path.parent / archive["archive_file"]
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"archive is missing or a symlink: {path}")
        if file_digest(path) != (archive["compressed_bytes"], archive["compressed_sha256"]):
            raise ValueError(f"compressed archive hash mismatch: {path}")
        with gzip.open(path, "rb") as stream:
            if stream_digest(stream) != (archive["tar_bytes"], archive["tar_sha256"]):
                raise ValueError(f"decompressed tar hash mismatch: {path}")
        expected = {row["original_path"]: row for row in manifest["files"]
                    if row["archive_file"] == archive["archive_file"]}
        seen = set()
        with tarfile.open(path, "r:gz") as bundle:
            for member in bundle:
                safe_relative(member.name)
                if not member.isfile() or member.name not in expected or member.name in seen:
                    raise ValueError(f"undeclared, duplicate, or nonregular tar member: {member.name}")
                row = expected[member.name]
                if member.size != row["original_bytes"]:
                    raise ValueError(f"member size mismatch: {member.name}")
                stream = bundle.extractfile(member)
                if stream is None:
                    raise ValueError(f"unreadable tar member: {member.name}")
                with stream:
                    actual = stream_digest(stream)
                if actual != (row["original_bytes"], row["original_sha256"]):
                    raise ValueError(f"member hash mismatch: {member.name}")
                seen.add(member.name)
        if seen != set(expected):
            raise ValueError(f"missing tar members in {path}")
        verified_count += len(seen)
    return {"status": "verified", "archives": len(manifest["archives"]),
            "files": verified_count, "original_bytes": sum(row["original_bytes"] for row in manifest["files"]),
            "symlink_metadata_records": len(manifest["symlinks"])}


def destination_path(root, relative):
    parsed = safe_relative(relative)
    path = root.joinpath(*parsed.parts)
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink():
            raise ValueError(f"destination contains a symlink: {part}")
    if not path.resolve(strict=False).is_relative_to(root):
        raise ValueError(f"destination escapes selected root: {path}")
    return path


def restore(manifest_path, destination):
    manifest_path = Path(manifest_path).resolve()
    result = verify(manifest_path)
    manifest = load_manifest(manifest_path)
    root = Path(destination).resolve()
    if root.exists() and not root.is_dir():
        raise ValueError("restore destination must be a directory")
    for row in [*manifest["files"], *manifest["symlinks"]]:
        path = destination_path(root, row["original_path"])
        if path.exists() or path.is_symlink():
            raise FileExistsError(f"refusing to overwrite: {path}")
    for directory in sorted(manifest["directories"], key=lambda value: len(PurePosixPath(value).parts)):
        path = destination_path(root, directory)
        if path.exists() and not path.is_dir():
            raise FileExistsError(f"directory collides with a file: {path}")
    root.mkdir(parents=True, exist_ok=True)
    for directory in sorted(manifest["directories"], key=lambda value: len(PurePosixPath(value).parts)):
        destination_path(root, directory).mkdir(parents=True, exist_ok=True)
    for archive in manifest["archives"]:
        with tarfile.open(manifest_path.parent / archive["archive_file"], "r:gz") as bundle:
            for member in bundle:
                target = destination_path(root, member.name)
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.extractfile(member) as source, target.open("xb") as output:
                    shutil.copyfileobj(source, output)
    for row in manifest["files"]:
        target = destination_path(root, row["original_path"])
        if file_digest(target) != (row["original_bytes"], row["original_sha256"]):
            raise ValueError(f"restored bytes differ: {target}")
    for row in manifest["symlinks"]:
        target = destination_path(root, row["original_path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(row["portable_target"])
    return {**result, "status": "restored-and-verified", "destination": str(root),
            "portable_aliases_restored": len(manifest["symlinks"])}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["verify", "restore"])
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("MANIFEST.json"))
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    if args.action == "restore" and args.destination is None:
        parser.error("restore requires --destination")
    print(json.dumps(verify(args.manifest) if args.action == "verify" else
                     restore(args.manifest, args.destination), indent=2))
