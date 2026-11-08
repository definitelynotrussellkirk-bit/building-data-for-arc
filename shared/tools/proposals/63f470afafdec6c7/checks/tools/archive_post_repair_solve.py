#!/usr/bin/env python3
"""Preview or archive an entire public WORK/solve tree; no private-state access.

Example (preview):
  python archive_post_repair_solve.py --work /absolute/WORK \
      --archive-name prior-source-v1 --reason "Generator bytes changed"
Add --apply to move solve into checks/prior-solve/prior-source-v1/solve.
Uses only the standard library and POSIX no-follow file descriptors.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys


def _directory_chain(path, *, missing_ok=False):
    """Reject symlinks/non-directories in existing path components."""
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            if missing_ok:
                return
            raise FileNotFoundError(f"Missing directory: {current}") from None
        if stat.S_ISLNK(mode):
            raise ValueError(f"Refusing symlink: {current}")
        if not stat.S_ISDIR(mode):
            raise ValueError(f"Expected a directory: {current}")


def _snapshot(source):
    """Hash every regular file without following links; retain empty directories."""
    files, directories = {}, []
    summary_bytes = None
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW

    def walk(directory_fd, prefix=""):
        nonlocal summary_bytes
        names = sorted(os.listdir(directory_fd))
        for name in names:
            relative = f"{prefix}/{name}" if prefix else name
            if name == ".review":
                raise ValueError(f"Refusing private subtree inside public solve: {relative}")
            info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            if stat.S_ISLNK(info.st_mode):
                raise ValueError(f"Refusing symlink: {relative}")
            if stat.S_ISDIR(info.st_mode):
                child = os.open(name, directory_flags, dir_fd=directory_fd)
                try:
                    directories.append(relative)
                    walk(child, relative)
                finally:
                    os.close(child)
            elif stat.S_ISREG(info.st_mode):
                flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
                fd = os.open(name, flags, dir_fd=directory_fd)
                digest, size = hashlib.sha256(), 0
                capture = bytearray() if relative == "summary.json" and info.st_size <= 1048576 else None
                with os.fdopen(fd, "rb") as handle:
                    initial = os.fstat(handle.fileno())
                    if not stat.S_ISREG(initial.st_mode):
                        raise ValueError(f"Expected regular file: {relative}")
                    for block in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(block)
                        size += len(block)
                        if capture is not None:
                            capture.extend(block)
                    final = os.fstat(handle.fileno())
                    if (initial.st_size, initial.st_mtime_ns) != (final.st_size, final.st_mtime_ns):
                        raise ValueError(f"File changed while hashing: {relative}")
                files[relative] = {"sha256": digest.hexdigest(), "bytes": size}
                if capture is not None:
                    summary_bytes = bytes(capture)
            else:
                raise ValueError(f"Expected regular file or directory: {relative}")
        if sorted(os.listdir(directory_fd)) != names:
            raise ValueError("Public solve tree changed while hashing")

    root_fd = os.open(source, directory_flags)
    try:
        walk(root_fd)
    finally:
        os.close(root_fd)
    return {"files": files, "directories": sorted(directories)}, summary_bytes


def _write_receipt(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def archive_public_solve(work, archive_name, reason, *, apply=False):
    """Return a preview by default; --apply archives the whole tree exactly once."""
    if not isinstance(archive_name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", archive_name):
        raise ValueError("archive_name must be one safe component, starting with an ASCII letter or digit")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("A nonblank reason is required")
    if type(apply) is not bool:
        raise ValueError("apply must be an explicit Boolean")
    work = Path(work)
    if not work.is_absolute() or ".." in work.parts:
        raise ValueError("--work must be an absolute path without '..'")
    if ".review" in work.parts:
        raise ValueError("Private .review paths are outside this helper's scope")
    if not all(hasattr(os, flag) for flag in ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK")):
        raise ValueError("This helper requires POSIX no-follow descriptor support")
    _directory_chain(work)
    source = work / "solve"
    _directory_chain(source)
    parent = work / "checks" / "prior-solve"
    _directory_chain(parent, missing_ok=True)
    container = parent / archive_name
    if os.path.lexists(container):
        raise FileExistsError(f"Archive container already exists: {container}")

    before, summary_bytes = _snapshot(source)
    public_summary = None
    if summary_bytes is not None:
        try:
            public_summary = json.loads(summary_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            public_summary = {"unparsed": True, "reason": str(exc)}
    elif "summary.json" in before["files"]:
        public_summary = {"unparsed": True, "reason": "Public summary exceeds the 1 MiB receipt display limit"}
    receipt = {
        "schema": "arcpuzzles-public-solve-archive-v1",
        "mode": "preview", "verified": False,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "work": str(work), "source": "solve",
        "destination": f"checks/prior-solve/{archive_name}/solve",
        "reason": reason.strip(), "before": before, "after": None,
        "file_count": len(before["files"]),
        "directory_count_including_root": len(before["directories"]) + 1,
        "total_bytes": sum(item["bytes"] for item in before["files"].values()),
        "public_summary": public_summary,
        "current_solution_sha256": before["files"].get("solution.py", {}).get("sha256"),
        "attempt_source_hashes": {p: item["sha256"] for p, item in before["files"].items()
                                  if p.startswith("attempts/") and p.endswith(".py")},
    }
    if not apply:
        return receipt

    parent.mkdir(parents=True, exist_ok=True)
    _directory_chain(parent)
    container.mkdir(mode=0o700)  # Exclusive reservation; never reuse an archive.
    destination = container / "solve"
    try:
        os.rename(source, destination)
    except BaseException:
        try:
            container.rmdir()  # Remove only our still-empty reservation.
        except OSError:
            pass
        raise
    receipt["mode"] = "applied"
    try:
        receipt["after"], _ = _snapshot(destination)
        receipt["verified"] = receipt["before"] == receipt["after"]
    except (OSError, ValueError) as exc:
        receipt["verification_error"] = str(exc)
    _write_receipt(container / "ARCHIVE.json", receipt)
    if not receipt["verified"]:
        raise ValueError(f"Archive verification failed; moved public files and receipt retained at {container}")
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", required=True)
    parser.add_argument("--archive-name", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--apply", action="store_true", help="Move the whole public solve tree; default is preview")
    args = parser.parse_args(argv)
    try:
        receipt = archive_public_solve(args.work, args.archive_name, args.reason, apply=args.apply)
    except (OSError, ValueError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
