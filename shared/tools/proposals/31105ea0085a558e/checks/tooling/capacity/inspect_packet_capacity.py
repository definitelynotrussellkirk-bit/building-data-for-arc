#!/usr/bin/env python3
"""Read ZIP metadata and destination capacity; never read payloads or extract.

Exit 0: lower bounds fit, 1: known shortfall, 2: invalid input, 3: availability
unknown. A fitting lower bound does not prove an extraction will succeed.
"""
import argparse
import json
import ntpath
import os
from pathlib import Path
import stat
import zipfile


def inventory(infos, allocation_unit):
    """Validate central-directory entries and count a fresh POSIX extraction."""
    if allocation_unit <= 0:
        raise ValueError("Filesystem allocation unit must be positive")
    seen, files, directories = set(), set(), set()
    explicit_directories = uncompressed = allocated = 0
    for info in infos:
        raw = info.orig_filename
        is_directory = raw.endswith("/")
        name = raw[:-1] if is_directory else raw
        parts = name.split("/")
        if (not name or "\0" in raw or "\\" in raw or raw.startswith("/")
                or ntpath.splitdrive(raw)[0] or any(p in ("", ".", "..") for p in parts)):
            raise ValueError(f"Unsafe or noncanonical member path: {raw!r}")
        if raw in seen:
            raise ValueError(f"Duplicate member: {raw!r}")
        seen.add(raw)
        kind = stat.S_IFMT(info.external_attr >> 16)
        if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
            raise ValueError(f"Symlink or special-file member: {raw!r}")
        if ((kind == stat.S_IFDIR or info.external_attr & 0x10) and not is_directory
                or is_directory and kind == stat.S_IFREG):
            raise ValueError(f"Inconsistent directory metadata: {raw!r}")
        if info.file_size < 0 or is_directory and info.file_size:
            raise ValueError(f"Invalid member size: {raw!r}")
        for depth in range(1, len(parts)):
            directories.add("/".join(parts[:depth]))
        if is_directory:
            directories.add(name)
            explicit_directories += 1
        else:
            files.add(name)
            uncompressed += info.file_size
            allocated += ((info.file_size + allocation_unit - 1) // allocation_unit) * allocation_unit
    conflicts = files & directories
    if conflicts:
        raise ValueError(f"File/directory path conflict: {min(conflicts)!r}")
    return {"members": len(seen), "files": len(files), "directories": len(directories),
            "explicit_directories": explicit_directories,
            "minimum_inodes": len(files) + len(directories),
            "uncompressed_bytes": uncompressed,
            "dense_file_allocation_lower_bound_bytes": allocated}


def inspect_packet(source, destination):
    """Inspect a ZIP and stat the nearest existing destination ancestor."""
    source, destination = Path(source).resolve(), Path(destination).resolve()
    probe, missing = destination, 0
    while not probe.exists():
        missing += 1
        probe = probe.parent
    if not probe.is_dir():
        raise ValueError(f"Destination ancestor is not a directory: {probe}")
    filesystem = os.statvfs(probe)
    unit = filesystem.f_frsize or filesystem.f_bsize
    with zipfile.ZipFile(source) as archive:
        counts = inventory(archive.infolist(), unit)
    available_bytes = (filesystem.f_bavail * unit if filesystem.f_blocks > 0
                       and 0 <= filesystem.f_bavail <= filesystem.f_blocks else None)
    total_inodes, free_inodes = filesystem.f_files, filesystem.f_favail
    available_inodes = (free_inodes if 0 < total_inodes < (1 << 64) - 1
                        and 0 <= free_inodes <= total_inodes else None)
    required_inodes = counts["minimum_inodes"] + missing
    inode_headroom = None if available_inodes is None else available_inodes - required_inodes
    byte_headroom = (None if available_bytes is None else available_bytes
                     - counts["dense_file_allocation_lower_bound_bytes"])
    if any(value is not None and value < 0 for value in (inode_headroom, byte_headroom)):
        status = "insufficient"
    elif inode_headroom is None or byte_headroom is None:
        status = "unknown"
    else:
        status = "lower_bounds_fit"
    return {
        "schema": "packet-capacity-v1", "metadata_only": True,
        "zip": str(source), "destination": str(destination), "filesystem_probe": str(probe),
        "inventory": counts, "allocation_unit_bytes": unit,
        "new_destination_directories": missing, "required_inodes": required_inodes,
        "byte_availability": "unknown" if available_bytes is None else "known",
        "available_bytes": available_bytes,
        "inode_availability": "unknown" if available_inodes is None else "known",
        "available_inodes": available_inodes,
        "inode_headroom_after_inventory": inode_headroom,
        "byte_headroom_after_file_data_lower_bound": byte_headroom,
        "capacity_status": status,
        "assumptions": [
            "Fresh extraction on the probed filesystem; existing destination contents are not inspected.",
            "File-data lower bound assumes ordinary dense allocation, rounded per file to statvfs units; "
            "compression, sparse files, deduplication, and filesystem-specific allocation are not modeled.",
            "Directory storage, filesystem metadata, baseline/runtime copies and concurrent usage need extra space.",
            "Lexical POSIX paths only; filesystem name equivalence, permissions, quotas, payload CRC and "
            "local-header consistency are not verified. Unknown availability is JSON null, never infinity.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip", type=Path, help="original ZIP; member payloads remain unread")
    parser.add_argument("destination", type=Path, help="existing or proposed extraction directory")
    args = parser.parse_args(argv)
    try:
        report = inspect_packet(args.zip, args.destination)
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as error:
        print(json.dumps({"schema": "packet-capacity-v1", "capacity_status": "invalid_input",
                          "error": str(error)}, sort_keys=True, allow_nan=False))
        return 2
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return {"lower_bounds_fit": 0, "insufficient": 1, "unknown": 3}[report["capacity_status"]]


if __name__ == "__main__":
    raise SystemExit(main())
