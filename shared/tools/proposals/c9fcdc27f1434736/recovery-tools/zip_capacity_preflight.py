"""Estimate fresh ZIP extraction capacity without opening member payloads."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path, PurePosixPath
import stat
import zipfile


def inspect_archive(archive_path: Path, *, block_size: int) -> dict:
    """Count unique filesystem entries from the ZIP central directory only."""
    if type(block_size) is not int or block_size <= 0:
        raise ValueError("Allocation block size must be a positive integer")
    files = {}
    directories = set()
    declared = set()
    spelling = {}

    def register(name: str, is_directory: bool) -> None:
        prior = spelling.setdefault(name.casefold(), name)
        if prior != name:
            raise ValueError(f"Case-insensitive path collision: {prior!r}, {name!r}")
        if (is_directory and name in files) or (not is_directory and name in directories):
            raise ValueError(f"File/directory path conflict: {name!r}")
        if is_directory:
            directories.add(name)

    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        for member in members:
            original = member.orig_filename
            is_directory = member.is_dir()
            name = original[:-1] if is_directory else original
            if (not name or "\\" in name or ":" in name
                    or any(ord(character) < 32 or ord(character) == 127 for character in name)
                    or any(part in {"", ".", ".."} for part in name.split("/"))):
                raise ValueError(f"Unsafe ZIP member path: {original!r}")
            mode = stat.S_IFMT(member.external_attr >> 16)
            if mode not in {0, stat.S_IFREG, stat.S_IFDIR}:
                raise ValueError(f"Symlink or special ZIP member: {original!r}")
            if (mode == stat.S_IFDIR and not is_directory
                    or mode == stat.S_IFREG and is_directory
                    or is_directory and member.file_size != 0):
                raise ValueError(f"Inconsistent directory metadata: {original!r}")
            if name.casefold() in declared:
                raise ValueError(f"Duplicate ZIP member path: {original!r}")
            declared.add(name.casefold())
            path = PurePosixPath(name)
            for parent in reversed(path.parents):
                if parent != PurePosixPath("."):
                    register(parent.as_posix(), True)
            register(name, is_directory)
            if not is_directory:
                files[name] = member.file_size
    return {
        "zip_member_count": len(members),
        "file_count": len(files),
        "directory_count": len(directories),
        "entry_count": len(files) + len(directories),
        "expanded_file_bytes": sum(files.values()),
        "block_size": block_size,
        "block_rounded_file_bytes": sum(
            ((size + block_size - 1) // block_size) * block_size for size in files.values()
        ),
    }


def destination_capacity(destination: Path) -> dict:
    """Stat the nearest existing directory, rejecting links and partial trees."""
    if ".." in Path(destination).parts:
        raise ValueError("Destination must not contain '..'; pass its unambiguous absolute path")
    destination = Path(os.path.abspath(destination))
    current = Path(destination.anchor)
    ancestor = current
    missing = 0
    for component in destination.parts[1:]:
        current = current / component
        if missing:
            missing += 1
            continue
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            missing = 1
            continue
        if stat.S_ISLNK(mode):
            raise ValueError(f"Destination contains a symlink: {current}")
        if not stat.S_ISDIR(mode):
            raise ValueError(f"Destination component is not a directory: {current}")
        ancestor = current
    if not missing and next(destination.iterdir(), None) is not None:
        raise ValueError("Destination must be absent or empty; partial extractions need separate review")
    capacity = os.statvfs(ancestor)
    block_size = capacity.f_frsize or capacity.f_bsize
    if block_size <= 0 or capacity.f_bavail < 0:
        raise ValueError("Filesystem does not report a usable block size and free-byte count")
    return {
        "path": str(destination),
        "filesystem_probe_path": str(ancestor),
        "new_directory_count": missing,
        "block_size": block_size,
        "free_bytes": capacity.f_bavail * block_size,
        "free_inodes": capacity.f_favail if capacity.f_files > 0 and capacity.f_favail >= 0 else None,
    }


def preflight(archive_path: Path, destination: Path, *, reserve_bytes: int = 0,
              reserve_inodes: int = 0) -> dict:
    """Return a JSON-compatible report; this function creates no artifacts."""
    report = {
        "schema": "zip-capacity-preflight-v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "archive_path": os.path.abspath(archive_path),
        "destination_path": os.path.abspath(destination),
        "metadata_only": True,
    }
    if any(type(value) is not int or value < 0 for value in (reserve_bytes, reserve_inodes)):
        return {**report, "status": "invalid_arguments", "exit_code": 2,
                "error": "Reserves must be nonnegative integers"}
    try:
        capacity = destination_capacity(destination)
    except (OSError, ValueError, AttributeError) as exc:
        return {**report, "status": "destination_capacity_error", "exit_code": 4,
                "error": str(exc)}
    report["destination"] = capacity
    try:
        inventory = inspect_archive(archive_path, block_size=capacity["block_size"])
    except (OSError, ValueError, zipfile.BadZipFile, NotImplementedError) as exc:
        return {**report, "status": "invalid_archive", "exit_code": 2, "error": str(exc)}
    report["archive"] = inventory
    checks = {}
    requirements = {
        "bytes": (inventory["block_rounded_file_bytes"] + reserve_bytes, capacity["free_bytes"]),
        "inodes": (inventory["entry_count"] + capacity["new_directory_count"] + reserve_inodes,
                   capacity["free_inodes"]),
    }
    for resource, (required, available) in requirements.items():
        checks[resource] = {
            "required": required,
            "available": available,
            "shortfall": max(0, required - available) if available is not None else None,
            "sufficient": available >= required if available is not None else None,
        }
    decisions = [check["sufficient"] for check in checks.values()]
    code = 3 if False in decisions else 4 if None in decisions else 0
    report.update(
        checks=checks,
        reserves={"bytes": reserve_bytes, "inodes": reserve_inodes},
        exit_code=code,
        status={0: "sufficient_for_estimate", 3: "insufficient_capacity", 4: "capacity_unknown"}[code],
        limitations=[
            "Member contents, CRCs and source hashes were not read or verified.",
            "Byte estimate excludes directory data, filesystem metadata, quotas and temporary workspaces.",
            "Capacity is a snapshot; this command does not reserve space or create any files.",
        ],
    )
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="ZIP archive to inspect as metadata only")
    parser.add_argument("destination", type=Path, help="absent or empty extraction directory")
    parser.add_argument("--reserve-bytes", type=int, default=0, help="additional free bytes to retain")
    parser.add_argument("--reserve-inodes", type=int, default=0, help="additional free inodes to retain")
    arguments = parser.parse_args(argv)
    report = preflight(arguments.archive, arguments.destination,
                       reserve_bytes=arguments.reserve_bytes, reserve_inodes=arguments.reserve_inodes)
    print(json.dumps(report, indent=2, sort_keys=True))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
