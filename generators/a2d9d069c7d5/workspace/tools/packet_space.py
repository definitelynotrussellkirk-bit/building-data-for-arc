#!/usr/bin/env python3
"""Read-only ZIP capacity preflight and optional packet-byte verification.

Estimate a fresh tree in an existing destination; quotas, existing paths and
runtime behavior are not checked. Hashes establish internal packet consistency.
Exit: 0 fits, 1 insufficient capacity, 2 usage/I/O, 3 unsafe ZIP, 4 hash/inventory.
"""
import argparse
import hashlib
import json
import math
import os
import re
import stat
import zipfile

MANIFEST = "WORK/PACKET-MANIFEST.json"


def safe_name(name):
    clean = name.removesuffix("/")
    if (not clean or "\\" in name or "\0" in name or ":" in name
            or any(part in ("", ".", "..") for part in clean.split("/"))):
        raise ValueError(f"Unsafe member path: {name!r}")
    return clean


def assess(archive, filesystem, margin=0.1):
    """Count members and budget blocks/inodes without extracting anything."""
    if not math.isfinite(margin) or margin < 0:
        raise ValueError("margin must be finite and nonnegative")
    files, directories, seen = {}, set(), set()
    for info in archive.infolist():
        name = safe_name(info.orig_filename)
        mode = stat.S_IFMT(info.external_attr >> 16)
        if name in seen:
            raise ValueError(f"Duplicate member path: {name!r}")
        if mode not in (0, stat.S_IFREG, stat.S_IFDIR):
            raise ValueError(f"Unsupported member type (including symlink): {name!r}")
        if (mode == stat.S_IFDIR and not info.is_dir()
                or mode == stat.S_IFREG and info.is_dir()):
            raise ValueError(f"Conflicting member type: {name!r}")
        seen.add(name)
        parts = name.split("/")
        directories.update("/".join(parts[:i]) for i in
                           range(1, len(parts) + int(info.is_dir())))
        if not info.is_dir():
            files[name] = info
    if files.keys() & directories:
        raise ValueError("A member file is also used as a directory")
    block = filesystem.f_frsize
    declared = sum(info.file_size for info in files.values())
    allocated = sum((info.file_size + block - 1) // block * block
                    for info in files.values()) + len(directories) * block
    needed_bytes = math.ceil(allocated * (1 + margin))
    needed_inodes = math.ceil((len(files) + len(directories)) * (1 + margin))
    available = filesystem.f_bavail * block
    return {"declared_bytes": declared, "file_count": len(files),
            "directory_count": len(directories), "block_bytes": block,
            "allocated_bytes_estimate": allocated, "margin": margin,
            "required_bytes": needed_bytes, "required_inodes": needed_inodes,
            "available_bytes": available, "free_inodes": filesystem.f_ffree,
            "available_inodes": filesystem.f_favail, "member_layout_safe": True,
            "full_extraction_fits": (needed_bytes <= available
                                     and needed_inodes <= filesystem.f_favail)}, files


def unique_object(pairs):
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError("Duplicate JSON key in packet manifest")
    return result


def verify(archive, files):
    """Stream SHA-256 checks for every declared WORK and outer member."""
    with archive.open(MANIFEST) as source:
        manifest = json.load(source, object_pairs_hook=unique_object)
    layout = manifest.get("layout", {})
    work, outer = manifest.get("files"), layout.get("entry_files")
    if layout.get("workspace") != "WORK" or not isinstance(work, dict) or not isinstance(outer, dict):
        raise ValueError("Expected WORK-layout manifest with files and entry_files maps")
    expected = {}
    for prefix, mapping in (("WORK/", work), ("", outer)):
        for name, digest in mapping.items():
            safe_name(name)
            target = prefix + name
            if name.endswith("/") or target in expected or target == MANIFEST:
                raise ValueError(f"Conflicting manifest path: {target!r}")
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError(f"Invalid SHA-256 for {target!r}")
            expected[target] = digest
    if set(expected) != files.keys() - {MANIFEST}:
        raise ValueError("Manifest inventory differs from ZIP files")
    canonical = manifest.get("canonical_sha256")
    if canonical is not None and canonical != work.get("repo/shared/data/canonical/puzzles.jsonl"):
        raise ValueError("Canonical-data digest differs from the manifest file map")
    for name, expected_digest in expected.items():
        digest = hashlib.sha256()
        with archive.open(files[name]) as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected_digest:
            raise ValueError(f"SHA-256 mismatch: {name}")
    return {"archive_bytes_verified": True, "verified_files": len(expected),
            "outer_entries_verified": len(outer),
            "verification_scope": "manifest-listed ZIP member bytes"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", help="ZIP to inspect; never extracted")
    parser.add_argument("destination", help="existing destination directory")
    parser.add_argument("--margin", type=float, default=0.1, help="fractional byte/inode headroom (default .1)")
    parser.add_argument("--verify", action="store_true", help="stream packet manifest hash checks")
    parser.add_argument("--json", action="store_true", help="emit a single JSON report")
    args = parser.parse_args()
    if not math.isfinite(args.margin) or args.margin < 0:
        parser.error("--margin must be finite and nonnegative")
    report = {"archive": args.archive, "destination": args.destination,
              "archive_bytes_verified": False, "capacity_scope": "fresh-tree estimate"}
    code = 2
    try:
        if not os.path.isdir(args.destination):
            raise OSError("destination must be an existing directory")
        code = 3
        with zipfile.ZipFile(args.archive) as archive:
            capacity, files = assess(archive, os.statvfs(args.destination), args.margin)
            report.update(capacity)
            if args.verify:
                code = 4
                report.update(verify(archive, files))
            code = 0 if report["full_extraction_fits"] else 1
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RuntimeError,
            NotImplementedError, zipfile.BadZipFile) as error:
        report["error"] = str(error)
        if isinstance(error, OSError):
            code = 2
    report["exit_status"] = code
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else
          "\n".join(f"{key}: {value}" for key, value in report.items()))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
