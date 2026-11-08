"""Optional stdlib-only storage snapshot for explicit paths.

Reads os.stat/os.statvfs; never creates, deletes, mounts or changes files.
Capacity exhaustion is reported as data, not a failing preflight gate.
Use PYTHONDONTWRITEBYTECODE=1 when importing this script during a review.
"""
from __future__ import annotations

from datetime import datetime, timezone
import argparse
import json
import os


def inspect_paths(paths, *, stat_fn=None, statvfs_fn=None):
    """Inspect only caller-supplied existing paths and return JSON-compatible data."""
    stat_fn = os.stat if stat_fn is None else stat_fn
    statvfs_fn = os.statvfs if statvfs_fn is None else statvfs_fn
    rows, errors, devices = [], [], {}
    for argument in paths:
        path = os.fspath(argument)
        try:
            node, fs = stat_fn(path), statvfs_fn(path)
        except OSError as exc:
            errors.append({"path": path, "errno": exc.errno, "error": str(exc)})
            continue
        unit = fs.f_frsize or fs.f_bsize
        available_bytes = fs.f_bavail * unit
        reported_inodes = fs.f_files > 0 and fs.f_favail >= 0
        flags = []
        if available_bytes == 0:
            flags.append("no_available_bytes")
        if reported_inodes and fs.f_favail == 0:
            flags.append("no_available_inodes")
            if available_bytes > 0:
                flags.append("inode_exhaustion_with_available_bytes")
        device = {"st_dev": node.st_dev,
                  "major": os.major(node.st_dev) if hasattr(os, "major") else None,
                  "minor": os.minor(node.st_dev) if hasattr(os, "minor") else None,
                  "filesystem_id": getattr(fs, "f_fsid", None)}
        rows.append({"path": path, "absolute_path": os.path.abspath(path),
                     "device": device,
                     "bytes": {"total": fs.f_blocks * unit, "free": fs.f_bfree * unit,
                               "available": available_bytes},
                     "inodes": {"status": "reported" if reported_inodes else "unreported",
                                "total": fs.f_files, "free": fs.f_ffree,
                                "available": fs.f_favail},
                     "flags": flags})
        devices.setdefault(node.st_dev, []).append(path)
    return {"schema": "optional-storage-diagnostic-v1",
            "captured_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "complete" if not errors else "incomplete",
            "paths": rows, "errors": errors,
            "distinct_filesystem_count": len(devices),
            "same_filesystem_groups": [{"st_dev": device, "paths": members}
                                       for device, members in devices.items() if len(members) > 1],
            "same_filesystem_basis": "os.stat st_dev; follows the supplied path's symlink target",
            "note": "Read-only diagnostic. Byte and inode availability are separate. No filesystem changes or required preflight."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="existing paths to inspect; no implicit scan")
    arguments = parser.parse_args(argv)
    report = inspect_paths(arguments.paths)
    print(json.dumps(report, indent=2))
    return 2 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
