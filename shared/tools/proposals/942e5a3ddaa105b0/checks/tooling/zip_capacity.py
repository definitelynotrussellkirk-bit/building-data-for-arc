#!/usr/bin/env python3
"""Optional read-only ZIP capacity check (Python stdlib, POSIX statvfs).

Usage: python3 zip_capacity.py --archive packet.zip --destination new-directory
Exit 0: reported capacity meets estimates; 1: capacity is unknown; 2: shortage
or invalid input. Run in the same mount namespace as the proposed extraction.
This helper never extracts, removes files, creates directories, or chooses a
destination. It does not change the optional storage study or its admission.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import sys
import zipfile


def archive_metadata(path):
    """Validate central-directory names and return sizes and unique directories."""
    files, directories, declared = {}, set(), set()
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            name = info.orig_filename
            key = name[:-1] if name.endswith("/") else name
            parts = key.split("/")
            if (not key or name.startswith("/") or "\\" in name or "\0" in name
                    or ":" in parts[0] or any(part in {"", ".", ".."} for part in parts)):
                raise ValueError(f"Unsafe or ambiguous ZIP member path: {name!r}")
            mode = stat.S_IFMT(info.external_attr >> 16)
            if mode not in {0, stat.S_IFREG, stat.S_IFDIR}:
                raise ValueError(f"Symlink or special ZIP member refused: {name!r}")
            if mode == stat.S_IFDIR and not info.is_dir():
                raise ValueError(f"Conflicting ZIP directory metadata: {name!r}")
            if key in declared:
                raise ValueError(f"Duplicate ZIP member or file-directory conflict: {key!r}")
            declared.add(key)
            directories.update("/".join(parts[:i]) for i in range(1, len(parts)))
            if info.is_dir():
                directories.add(key)
            else:
                files[key] = info.file_size
    conflicts = files.keys() & directories
    if conflicts:
        raise ValueError(f"ZIP file-directory conflict: {min(conflicts)!r}")
    return list(files.values()), directories


def inspect_capacity(archive, destination):
    """Inspect only this archive's metadata and the destination filesystem."""
    try:
        namespace = os.readlink("/proc/self/ns/mnt")
    except OSError:
        namespace = None
    report = {
        "schema": "zip-capacity-v1",
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "status": "invalid", "exit_code": 2, "shortages": [],
        "environment": {"mount_namespace": namespace, "python": sys.version.split()[0],
                        "platform": sys.platform},
        "limits": [
            "Run this check and extraction in the same mount namespace.",
            "All archive paths are assumed new; existing destination contents and descendant mounts are not inspected.",
            "Byte allocation is an estimate: rounded file blocks plus one block per directory.",
            "Quotas, metadata, concurrent writes, privileges and later setup can change actual capacity.",
            "No space is reserved; exit 0 is not a guarantee of extraction success.",
            "This optional helper never extracts, deletes, creates directories or selects another destination.",
        ],
    }
    try:
        sizes, directories = archive_metadata(archive)
        target = Path(destination).resolve()
        ancestor, missing = target, 0
        while not ancestor.exists():
            if ancestor.is_symlink():
                raise ValueError("Destination has a dangling symlink ancestor")
            ancestor, missing = ancestor.parent, missing + 1
        if not ancestor.is_dir():
            raise ValueError("Destination's existing ancestor must be a directory")
        fs = os.statvfs(ancestor)
        block = fs.f_frsize or fs.f_bsize
        if block <= 0:
            raise ValueError("Filesystem block size is unavailable")
        inode_known = fs.f_files > 0 and fs.f_favail >= 0
        report["archive"] = {
            "path": str(Path(archive).absolute()), "files": len(sizes),
            "directories": len(directories), "uncompressed_bytes": sum(sizes),
        }
        report["destination"] = {"path": str(target), "missing_directories": missing}
        report["filesystem"] = {
            "path": str(ancestor), "device_id": ancestor.stat().st_dev,
            "allocation_unit_bytes": block, "total_bytes": fs.f_blocks * block,
            "free_bytes": fs.f_bfree * block, "available_bytes": fs.f_bavail * block,
            "total_inodes": fs.f_files if fs.f_files > 0 else None,
            "free_inodes": fs.f_ffree if fs.f_files > 0 and fs.f_ffree >= 0 else None,
            "available_inodes": fs.f_favail if inode_known else None,
        }
        directory_count = len(directories) + missing
        required_inodes = len(sizes) + directory_count
        estimated_bytes = sum((size + block - 1) // block * block for size in sizes)
        estimated_bytes += directory_count * block
        report["required"] = {
            "inodes": required_inodes, "estimated_allocated_bytes": estimated_bytes,
        }
        if fs.f_bavail * block < estimated_bytes:
            report["shortages"].append("available_bytes")
        if inode_known and fs.f_favail < required_inodes:
            report["shortages"].append("available_inodes")
        if report["shortages"]:
            report.update(status="insufficient", exit_code=2)
        elif not inode_known:
            report.update(status="unknown", exit_code=1)
            report["unknown"] = ["available_inodes"]
        else:
            report.update(status="sufficient", exit_code=0)
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        report["error"] = str(exc)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args(argv)
    report = inspect_capacity(args.archive, args.destination)
    print(json.dumps(report, indent=2, sort_keys=True))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
