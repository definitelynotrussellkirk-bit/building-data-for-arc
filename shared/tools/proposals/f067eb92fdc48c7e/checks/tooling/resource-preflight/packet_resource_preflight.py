#!/usr/bin/env python3
"""Read-only ZIP capacity preflight; never extracts, deletes, or selects a destination."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import stat
import sys
import zipfile


def rounded(size: int, unit: int) -> int:
    return ((size + unit - 1) // unit) * unit


def archive_inventory(archive: zipfile.ZipFile, allocation_unit: int = 4096) -> dict:
    if allocation_unit < 1:
        raise ValueError("allocation_unit must be positive")
    files, directories, errors = {}, set(), []
    names = Counter()
    for entry in archive.infolist():
        original = getattr(entry, "orig_filename", entry.filename)
        names[original] += 1
        name = original.rstrip("/")
        parts = name.split("/")
        unsafe = (not name or original.startswith("/") or "\\" in original
                  or any(part in {"", ".", ".."} for part in parts)
                  or ":" in parts[0] or any(ord(c) < 32 for c in original))
        mode = entry.external_attr >> 16
        kind = stat.S_IFMT(mode)
        if unsafe:
            errors.append({"kind": "unsafe_path", "member": original})
            continue
        if kind not in {0, stat.S_IFREG, stat.S_IFDIR}:
            errors.append({"kind": "unsupported_member_type", "member": original})
            continue
        is_directory = entry.is_dir() or kind == stat.S_IFDIR
        directories.update("/".join(parts[:n]) for n in range(1, len(parts)))
        if is_directory:
            directories.add(name)
        else:
            files[name] = entry.file_size
    errors.extend({"kind": "duplicate_member", "member": name, "count": count}
                  for name, count in sorted(names.items()) if count > 1)
    errors.extend({"kind": "file_directory_conflict", "member": name}
                  for name in sorted(set(files) & directories))
    # A directory allocation unit is an estimate. Filesystem metadata and large
    # directory indexes can require additional capacity; callers can reserve it.
    return {"archive_entries": len(archive.infolist()),
            "distinct_files": len(files), "distinct_directories": len(directories),
            "payload_bytes": sum(files.values()),
            "rounded_file_bytes": sum(rounded(size, allocation_unit) for size in files.values()),
            "estimated_directory_bytes": len(directories) * allocation_unit,
            "estimated_inodes": len(files) + len(directories),
            "allocation_unit": allocation_unit, "errors": errors}


def capacity_report(inventory: dict, available_bytes: int, available_inodes: int | None,
                    *, extra_bytes: int = 0, extra_inodes: int = 0,
                    copies: list[dict] | None = None) -> dict:
    if min(available_bytes, extra_bytes, extra_inodes) < 0:
        raise ValueError("capacity and reserve values must be nonnegative")
    budgets = []
    for item in copies or []:
        count, byte_size = item["count"], item["bytes_per_copy"]
        file_count, directory_count = item["files_per_copy"], item["directories_per_copy"]
        if min(count, byte_size, file_count, directory_count) < 0:
            raise ValueError("copy estimates must be nonnegative")
        # Byte estimates should include file allocation rounding. Directory
        # allocation is added here explicitly to preserve separate accounting.
        budgets.append({**item, "estimated_bytes": count * (
            byte_size + directory_count * inventory["allocation_unit"]),
            "estimated_inodes": count * (file_count + directory_count)})
    required_bytes = (inventory["rounded_file_bytes"] + inventory["estimated_directory_bytes"]
                      + extra_bytes + sum(row["estimated_bytes"] for row in budgets))
    required_inodes = (inventory["estimated_inodes"] + extra_inodes
                       + sum(row["estimated_inodes"] for row in budgets))
    byte_ok = required_bytes <= available_bytes
    inode_ok = None if available_inodes is None else required_inodes <= available_inodes
    return {"required_bytes_estimate": required_bytes, "available_bytes": available_bytes,
            "bytes_sufficient": byte_ok, "byte_headroom": available_bytes - required_bytes,
            "required_inodes_estimate": required_inodes, "available_inodes": available_inodes,
            "inodes_sufficient": inode_ok,
            "inode_headroom": None if available_inodes is None else available_inodes - required_inodes,
            "extra_bytes": extra_bytes, "extra_inodes": extra_inodes, "copy_estimates": budgets,
            "capacity_sufficient": byte_ok and inode_ok is not False,
            "inode_check_known": inode_ok is not None}


def existing_ancestor(destination: Path) -> Path:
    path = destination.absolute()
    while not path.exists():
        path = path.parent
    if not path.is_dir():
        raise ValueError(f"Existing destination ancestor is not a directory: {path}")
    return path.resolve()


def mount_context(path: Path) -> dict:
    result = {}
    try:
        result["mount_namespace"] = os.readlink("/proc/self/ns/mnt")
        chosen = None
        for line in Path("/proc/self/mountinfo").read_text().splitlines():
            before, after = line.split(" - ", 1)
            fields, details = before.split(), after.split()
            mountpoint = fields[4]
            for encoded, decoded in (("\\040", " "), ("\\011", "\t"),
                                     ("\\012", "\n"), ("\\134", "\\")):
                mountpoint = mountpoint.replace(encoded, decoded)
            mount = Path(mountpoint)
            if path == mount or mount in path.parents:
                if chosen is None or len(mountpoint) > len(chosen[0]):
                    chosen = (mountpoint, details[0])
        if chosen:
            result.update(mountpoint=chosen[0], filesystem_type=chosen[1])
    except (OSError, ValueError, IndexError):
        pass
    result["lifecycle_note"] = (
        "Capacity applies to the current process mount namespace. Some execution environments "
        "give each command transient mounts, including /dev tmpfs. Verify destination persistence "
        "or retain the execution session and copy final artifacts to a persistent destination. "
        "This tool does not select or recommend a destination.")
    if result.get("filesystem_type") == "tmpfs":
        result["memory_note"] = (
            "tmpfs capacity shares memory limits with processes and other tmpfs mounts. "
            "Available filesystem bytes alone do not establish available memory.")
        for name in ("memory.max", "memory.current", "memory.swap.max"):
            try:
                result[name] = Path("/sys/fs/cgroup", name).read_text().strip()
            except OSError:
                pass
    return result


def nonnegative(value: str) -> int:
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("destination", type=Path, help="chosen extraction directory; never created")
    parser.add_argument("--json", action="store_true", help="print complete machine-readable report")
    parser.add_argument("--extra-bytes", type=nonnegative, default=0)
    parser.add_argument("--extra-inodes", type=nonnegative, default=0)
    for label in ("runtime", "replay"):
        parser.add_argument(f"--{label}-copies", type=nonnegative, default=0)
        parser.add_argument(f"--{label}-bytes", type=nonnegative, default=0,
                            help="allocated file bytes per copy, excluding directory allocation")
        parser.add_argument(f"--{label}-files", type=nonnegative, default=0)
        parser.add_argument(f"--{label}-directories", type=nonnegative, default=0)
    args = parser.parse_args(argv)
    try:
        probe = existing_ancestor(args.destination)
        capacity = os.statvfs(probe)
        unit = capacity.f_frsize or capacity.f_bsize or 4096
        with zipfile.ZipFile(args.archive) as archive:
            inventory = archive_inventory(archive, unit)
        copies = [{"kind": label, "count": getattr(args, f"{label}_copies"),
                   "bytes_per_copy": getattr(args, f"{label}_bytes"),
                   "files_per_copy": getattr(args, f"{label}_files"),
                   "directories_per_copy": getattr(args, f"{label}_directories")}
                  for label in ("runtime", "replay")]
        budget = capacity_report(inventory, capacity.f_bavail * unit,
            capacity.f_favail if capacity.f_files else None,
            extra_bytes=args.extra_bytes, extra_inodes=args.extra_inodes, copies=copies)
        report = {"schema": "zip-resource-preflight-v1", "archive": str(args.archive.absolute()),
                  "destination": str(args.destination.absolute()), "capacity_probe_path": str(probe),
                  "device_id": capacity.f_fsid, "inventory": inventory, "capacity": budget,
                  "mount_context": mount_context(probe),
                  "limits": ["Directory allocation and copy sizes are estimates; reserve metadata and evidence headroom.",
                             "ZIP contents and CRCs are not inspected or validated by this metadata-only preflight.",
                             "Runtime/replay defaults are zero; supply estimates for the intended workflow."]}
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"Archive: {report['archive']}")
            print(f"Destination capacity measured at: {probe}")
            print(f"Files: {inventory['distinct_files']:,}; directories: {inventory['distinct_directories']:,}")
            print(f"Bytes required/available: {budget['required_bytes_estimate']:,} / {budget['available_bytes']:,}; sufficient: {budget['bytes_sufficient']}")
            print(f"Inodes required/available: {budget['required_inodes_estimate']:,} / {budget['available_inodes']}; sufficient: {budget['inodes_sufficient']}")
            for error in inventory['errors']:
                print(f"Archive error: {error}")
            print(report['mount_context']['lifecycle_note'])
            for limit in report['limits']:
                print(limit)
        if inventory['errors']:
            return 2
        return 0 if budget['capacity_sufficient'] else 1
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"Preflight failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
