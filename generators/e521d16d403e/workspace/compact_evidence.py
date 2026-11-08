#!/usr/bin/env python3
"""Lossless, explicit evidence compression under a review packet's checks/ tree.

No threshold or automatic selection is supported. Compress only completed files.
Run ``list`` to inspect candidates, ``compress checks/path.json [...]`` to archive
explicit originals, ``verify`` to check every archive, and ``restore --out NEW``
to recover their original packet-relative paths in a new destination directory.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import stat
import sys
import tempfile


SCHEMA = "arcpuzzles-evidence-gzip-v1"
MANIFEST = "checks/COMPRESSED-EVIDENCE.json"
CHUNK = 64 * 1024
MAX_FILE_BYTES = 256 * 1024 * 1024
MAX_TOTAL_BYTES = 512 * 1024 * 1024
MAX_MANIFEST_BYTES = 2 * 1024 * 1024


def no_symlinks(path: Path) -> None:
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ValueError(f"Symlink refused: {component}")


def checked_path(root: Path, relative: str) -> Path:
    if (not isinstance(relative, str) or "\\" in relative or "\0" in relative or ":" in relative
            or relative.startswith("/") or any(p in {"", ".", ".."} for p in relative.split("/"))):
        raise ValueError(f"Invalid packet-relative path: {relative!r}")
    parts = PurePosixPath(relative).parts
    if len(parts) < 2 or parts[0] != "checks":
        raise ValueError("Evidence paths must be packet-relative beneath checks/")
    path = root.joinpath(*parts)
    no_symlinks(path)
    return path


def protected(relative: str) -> bool:
    name = PurePosixPath(relative).name.lower()
    return ("summary" in name or "manifest" in name or name == "result.json"
            or name.endswith((".gz", ".tmp", ".lock")))


def fingerprint(path: Path, limit: int = MAX_FILE_BYTES + 1024 * 1024) -> tuple[int, str]:
    no_symlinks(path)
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError(f"Not a regular file: {path}")
    total, sha = 0, hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(CHUNK):
            total += len(block)
            if total > limit:
                raise ValueError(f"File exceeds byte limit: {path}")
            sha.update(block)
    return total, sha.hexdigest()


def load_manifest(root: Path, *, required: bool = False) -> dict:
    path = checked_path(root, MANIFEST)
    if not path.exists():
        if required:
            raise FileNotFoundError(path)
        try:
            tool = Path(__file__).absolute().relative_to(root.absolute()).as_posix()
        except ValueError:
            tool = Path(__file__).name
        return {"schema": SCHEMA, "codec": "gzip; level=9, mtime=0, no embedded filename",
                "restoration": {"instructions": "From the packet root, run the command below. OUT must not exist; "
                                "restored files keep their original checks/ paths. Archives are retained.",
                                "command": f"python3 {shlex.quote(tool)} --packet-root . restore --out OUT"},
                "entries": []}
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("Manifest must be a regular file")
    with path.open("rb") as handle:
        raw = handle.read(MAX_MANIFEST_BYTES + 1)
    if len(raw) > MAX_MANIFEST_BYTES:
        raise ValueError("Manifest exceeds byte limit")
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get("schema") != SCHEMA or not isinstance(data.get("entries"), list):
        raise ValueError("Invalid evidence manifest schema")
    seen, total = set(), 0
    for entry in data["entries"]:
        if not isinstance(entry, dict):
            raise ValueError("Invalid manifest entry")
        original = entry.get("original_path")
        checked_path(root, original)
        if protected(original) or original in seen:
            raise ValueError(f"Protected or duplicate original path: {original}")
        seen.add(original)
        if entry.get("compressed_path") != original + ".gz":
            raise ValueError("Compressed path must equal original path + '.gz'")
        checked_path(root, entry["compressed_path"])
        for field, limit in (("original_size", MAX_FILE_BYTES),
                             ("compressed_size", MAX_FILE_BYTES + 1024 * 1024)):
            if type(entry.get(field)) is not int or not 0 <= entry[field] <= limit:
                raise ValueError(f"Invalid or excessive {field}")
        for field in ("original_sha256", "compressed_sha256"):
            if not isinstance(entry.get(field), str) or not re.fullmatch(r"[0-9a-f]{64}", entry[field]):
                raise ValueError(f"Invalid {field}")
        total += entry["original_size"]
    ordered = sorted(seen)
    if any(b.startswith(a + "/") for a, b in zip(ordered, ordered[1:])):
        raise ValueError("Conflicting original file/directory paths")
    if total > MAX_TOTAL_BYTES:
        raise ValueError("Manifest exceeds total restoration byte limit")
    return data


def inflate(archive: Path, entry: dict, output=None) -> None:
    """Stream through gzip EOF/CRC, stopping after the declared size plus one byte."""
    total, sha = 0, hashlib.sha256()
    with gzip.open(archive, "rb") as handle:
        while block := handle.read(min(CHUNK, entry["original_size"] - total + 1)):
            total += len(block)
            if total > entry["original_size"] or total > MAX_FILE_BYTES:
                raise ValueError("Decompressed data exceeds declared byte limit")
            sha.update(block)
            if output is not None:
                output.write(block)
    if (total, sha.hexdigest()) != (entry["original_size"], entry["original_sha256"]):
        raise ValueError("Restored size/SHA-256 mismatch")


def verify_entry(root: Path, entry: dict) -> None:
    archive = checked_path(root, entry["compressed_path"])
    if fingerprint(archive) != (entry["compressed_size"], entry["compressed_sha256"]):
        raise ValueError(f"Compressed size/SHA-256 mismatch: {entry['compressed_path']}")
    inflate(archive, entry)


def write_manifest(root: Path, data: dict) -> None:
    path = checked_path(root, MANIFEST)
    data["entries"].sort(key=lambda entry: entry["original_path"])
    encoded = (json.dumps(data, indent=2, sort_keys=True) + "\n").encode()
    if len(encoded) > MAX_MANIFEST_BYTES:
        raise ValueError("Manifest exceeds byte limit")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        no_symlinks(path)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def compress(root: Path, selected: list[str]) -> dict:
    if not selected or len(selected) != len(set(selected)):
        raise ValueError("Select explicit, distinct evidence paths")
    data = load_manifest(root)
    entries = {entry["original_path"]: entry for entry in data["entries"]}
    plans = []
    # Preflight the entire selection so a bad later path cannot partially select a batch.
    for relative in selected:
        source = checked_path(root, relative)
        archive = checked_path(root, relative + ".gz")
        if protected(relative):
            raise ValueError(f"Protected summary/manifest/archive path: {relative}")
        if relative in entries:
            entry = entries[relative]
            verify_entry(root, entry)
            if source.exists() and fingerprint(source, MAX_FILE_BYTES) != (entry["original_size"], entry["original_sha256"]):
                raise ValueError(f"Original changed since archival: {relative}")
        else:
            if archive.exists():
                raise FileExistsError(f"Untracked archive collision: {archive}")
            size, sha = fingerprint(source, MAX_FILE_BYTES)
            entry = {"original_path": relative, "compressed_path": relative + ".gz",
                     "original_size": size, "original_sha256": sha}
        plans.append((source, archive, entry))
    if sum(e["original_size"] for e in entries.values()) + sum(
            e["original_size"] for _, _, e in plans if e["original_path"] not in entries) > MAX_TOTAL_BYTES:
        raise ValueError("Selection exceeds total restoration byte limit")
    for source, archive, entry in plans:
        if entry["original_path"] not in entries:
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=archive.parent, suffix=".tmp", delete=False) as handle:
                    temporary = Path(handle.name)
                    with gzip.GzipFile(filename="", mode="wb", fileobj=handle, compresslevel=9, mtime=0) as zipped:
                        with source.open("rb") as original:
                            copied = 0
                            while block := original.read(min(CHUNK, entry["original_size"] - copied + 1)):
                                copied += len(block)
                                if copied > entry["original_size"]:
                                    raise ValueError(f"Original grew during compression: {source}")
                                zipped.write(block)
                    handle.flush()
                    os.fsync(handle.fileno())
                if fingerprint(source, MAX_FILE_BYTES) != (entry["original_size"], entry["original_sha256"]):
                    raise ValueError(f"Original changed during compression: {source}")
                inflate(temporary, entry)
                entry["compressed_size"], entry["compressed_sha256"] = fingerprint(temporary)
                no_symlinks(archive)
                # Exclusive publication: a concurrently created archive is never replaced.
                os.link(temporary, archive)
                data["entries"].append(entry)
                write_manifest(root, data)
                entries[entry["original_path"]] = entry
            finally:
                if temporary is not None and temporary.exists():
                    temporary.unlink()
        if source.exists():
            # A verified archive and committed manifest exist before any original removal.
            verify_entry(root, entry)
            if fingerprint(source, MAX_FILE_BYTES) != (entry["original_size"], entry["original_sha256"]):
                raise ValueError(f"Original changed before removal; preserved: {source}")
            source.unlink()
    return {"manifest": MANIFEST, "selected": selected,
            "original_bytes": sum(entry["original_size"] for _, _, entry in plans),
            "compressed_bytes": sum(entry["compressed_size"] for _, _, entry in plans)}


def verify(root: Path) -> dict:
    data = load_manifest(root, required=True)
    for entry in data["entries"]:
        verify_entry(root, entry)
    return {"manifest": MANIFEST, "verified_archives": len(data["entries"]),
            "original_bytes": sum(entry["original_size"] for entry in data["entries"])}


def restore(root: Path, destination: Path) -> dict:
    destination = destination.absolute()
    no_symlinks(destination)
    if destination.exists():
        raise FileExistsError("Restoration destination must not already exist")
    data = load_manifest(root, required=True)
    verify(root)
    destination.mkdir()
    try:
        for entry in data["entries"]:
            output = checked_path(destination, entry["original_path"])
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("xb") as handle:
                inflate(checked_path(root, entry["compressed_path"]), entry, handle)
    except BaseException:
        shutil.rmtree(destination)
        raise
    return {"destination": str(destination), "restored_files": len(data["entries"])}


def list_files(root: Path) -> dict:
    data = load_manifest(root)
    files = []
    checks = checked_path(root, "checks/.listing-root").parent
    for directory, dirs, names in os.walk(checks, followlinks=False):
        for name in [*dirs, *names]:
            no_symlinks(Path(directory) / name)
        for name in names:
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if not stat.S_ISREG(path.stat().st_mode):
                raise ValueError(f"Not a regular file: {path}")
            files.append({"path": relative, "bytes": path.stat().st_size, "eligible": not protected(relative)})
    return {"files": sorted(files, key=lambda row: (-row["bytes"], row["path"])),
            "archived_originals": [entry["original_path"] for entry in data["entries"]]}


def find_packet() -> Path:
    for candidate in Path(__file__).absolute().parents:
        if (candidate / "checks").is_dir():
            no_symlinks(candidate)
            return candidate
    raise FileNotFoundError("Cannot find packet checks/ directory; supply --packet-root")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-root", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list")
    commands.add_parser("verify")
    selection = commands.add_parser("compress")
    selection.add_argument("paths", nargs="+")
    extraction = commands.add_parser("restore")
    extraction.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        root = args.packet_root.absolute() if args.packet_root is not None else find_packet()
        no_symlinks(root)
        if not root.is_dir() or not checked_path(root, "checks/.root-check").parent.is_dir():
            raise ValueError("Packet root must contain a real checks/ directory")
        result = (list_files(root) if args.command == "list" else verify(root) if args.command == "verify"
                  else compress(root, args.paths) if args.command == "compress" else restore(root, args.out))
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, EOFError) as exc:
        print(json.dumps({"error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
