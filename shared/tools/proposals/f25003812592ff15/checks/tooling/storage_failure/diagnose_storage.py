#!/usr/bin/env python3
"""Read-only statvfs evidence for an ENOSPC investigation; JSON to stdout."""
import argparse
from datetime import datetime, timezone
import json
import os


def classify_enospc(available_bytes, available_inodes):
    """Identify observed exhaustion; unknown counters never imply exhaustion."""
    bytes_exhausted = available_bytes == 0
    inodes_exhausted = available_inodes == 0
    if bytes_exhausted and inodes_exhausted:
        return "both"
    if bytes_exhausted:
        return "bytes"
    if inodes_exhausted:
        return "inodes"
    if available_bytes is None or available_inodes is None:
        return "unknown"
    return "neither"


def _nonnegative_count(value):
    return value if type(value) is int and value >= 0 else None


def diagnose_path(path):
    """Read one path's filesystem counters without scanning or modifying it."""
    report = {"path": os.fspath(path), "status": "ok"}
    statvfs = getattr(os, "statvfs", None)
    if not callable(statvfs):
        return {**report, "status": "unavailable", "enospc_explanation": "unknown",
                "error": {"type": "Unavailable", "message": "os.statvfs is unavailable"}}
    try:
        stats = statvfs(path)
    except OSError as error:
        return {**report, "status": "error", "enospc_explanation": "unknown",
                "error": {"type": type(error).__name__, "errno": error.errno,
                          "message": str(error)}}

    block_size = _nonnegative_count(getattr(stats, "f_bsize", None))
    fragment_size = _nonnegative_count(getattr(stats, "f_frsize", None))
    # POSIX block counts use fragment size. A zero/absent fragment size falls
    # back to the filesystem's reported block size, never an invented default.
    byte_unit = fragment_size or block_size or None
    free_blocks = _nonnegative_count(getattr(stats, "f_bfree", None))
    available_blocks = _nonnegative_count(getattr(stats, "f_bavail", None))
    free_bytes = byte_unit * free_blocks if byte_unit is not None and free_blocks is not None else None
    available_bytes = byte_unit * available_blocks if byte_unit is not None and available_blocks is not None else None

    total_inodes = _nonnegative_count(getattr(stats, "f_files", None))
    inodes_meaningful = total_inodes is not None and total_inodes > 0
    free_inodes = _nonnegative_count(getattr(stats, "f_ffree", None)) if inodes_meaningful else None
    available_inodes = _nonnegative_count(getattr(stats, "f_favail", None)) if inodes_meaningful else None
    return {**report, "block_size_bytes": block_size,
            "fragment_size_bytes": fragment_size, "byte_count_unit": byte_unit,
            "free_bytes": free_bytes, "available_bytes": available_bytes,
            "reported_total_inodes": total_inodes,
            "inode_counts_meaningful": inodes_meaningful,
            "free_inodes": free_inodes, "available_inodes": available_inodes,
            "evidence_complete": available_bytes is not None and available_inodes is not None,
            "enospc_explanation": classify_enospc(available_bytes, available_inodes)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Existing files or directories to inspect")
    args = parser.parse_args(argv)
    reports = [diagnose_path(path) for path in args.paths]
    payload = {"schema": "storage-enospc-diagnosis-v1",
               "sampled_at_utc": datetime.now(timezone.utc).isoformat(),
               "interpretation": "Snapshot of available capacity; not a write test or preflight gate.",
               "paths": reports}
    print(json.dumps(payload, indent=2))
    return 0 if all(report["status"] == "ok" for report in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
