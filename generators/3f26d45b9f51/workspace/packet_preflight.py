"""Read-only ARC packet integrity and NEW-extraction capacity preflight.

Exit 0: verified and capacity estimate sufficient; 2: unsafe/corrupt packet;
3: verified but capacity insufficient/read-only; 4: destination/I/O failure.
Manifest hashes establish internal consistency, not publisher authenticity.
No extraction, writes, assignment selection, or runtime verification occurs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import zipfile
import zlib

MAX_ENTRY_BYTES = 128 * 1024 * 1024
MAX_TOTAL_BYTES = 512 * 1024 * 1024
MAX_MANIFEST_BYTES = 16 * 1024 * 1024
MAX_ENTRIES = 100000
CHUNK = 1024 * 1024

class PacketError(ValueError):
    """The archive is unsafe, inconsistent, corrupt, or beyond bounded limits."""

def safe_path(name, directory=False):
    if not isinstance(name, str) or not name or len(name) > 4096:
        raise PacketError("invalid path length")
    if "\\" in name or "\x00" in name or name.startswith("/") or re.match(r"^[A-Za-z]:", name):
        raise PacketError("unsafe path: " + repr(name))
    path = name[:-1] if directory and name.endswith("/") else name
    if any(part in ("", ".", "..") for part in path.split("/")):
        raise PacketError("noncanonical path: " + repr(name))
    return path

def unique_json(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PacketError("duplicate JSON key: " + key)
        result[key] = value
    return result

def verify_packet(source, *, max_entry_bytes=MAX_ENTRY_BYTES, max_total_bytes=MAX_TOTAL_BYTES):
    """Stream every payload, validate inventory, return bounded summary metadata."""
    try:
        with zipfile.ZipFile(source) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ENTRIES:
                raise PacketError("entry count limit exceeded")
            files, directories, names = {}, set(), set()
            declared = 0
            for info in entries:
                name = safe_path(info.filename, info.is_dir())
                if info.orig_filename != info.filename or name in names:
                    raise PacketError("duplicate or NUL-truncated archive path: " + name)
                names.add(name)
                mode = stat.S_IFMT(info.external_attr >> 16)
                if mode not in (0, stat.S_IFREG, stat.S_IFDIR):
                    raise PacketError("nonregular archive member: " + name)
                if mode == stat.S_IFDIR and not info.is_dir() or mode == stat.S_IFREG and info.is_dir():
                    raise PacketError("file type/path disagreement: " + name)
                if info.flag_bits & 1:
                    raise PacketError("encrypted archive member")
                if info.file_size > max_entry_bytes or info.file_size < 0:
                    raise PacketError("entry expansion limit exceeded: " + name)
                declared += info.file_size
                if declared > max_total_bytes:
                    raise PacketError("total expansion limit exceeded")
                parts = name.split("/")
                directories.update("/".join(parts[:i]) for i in range(1, len(parts)))
                if info.is_dir():
                    if info.file_size:
                        raise PacketError("nonempty directory member")
                    directories.add(name)
                else:
                    files[name] = info
            if directories.intersection(files):
                raise PacketError("file/directory path collision")
            manifest_name = "WORK/PACKET-MANIFEST.json"
            if manifest_name not in files:
                raise PacketError("missing packet manifest")
            digests, manifest_parts, actual = {}, [], 0
            for name, info in files.items():
                digest, size = hashlib.sha256(), 0
                with archive.open(info) as member:
                    while True:
                        chunk = member.read(CHUNK)
                        if not chunk:
                            break
                        size += len(chunk)
                        actual += len(chunk)
                        if size > max_entry_bytes or actual > max_total_bytes:
                            raise PacketError("actual expansion limit exceeded")
                        digest.update(chunk)
                        if name == manifest_name:
                            if size > MAX_MANIFEST_BYTES:
                                raise PacketError("manifest size limit exceeded")
                            manifest_parts.append(chunk)
                if size != info.file_size:
                    raise PacketError("declared/actual size mismatch: " + name)
                digests[name] = digest.hexdigest()
            manifest = json.loads(b"".join(manifest_parts), object_pairs_hook=unique_json)
            if not isinstance(manifest, dict):
                raise PacketError("manifest must be an object")
            inventory = manifest.get("files")
            layout = manifest.get("layout")
            if not isinstance(inventory, dict) or not isinstance(layout, dict):
                raise PacketError("missing manifest inventory/layout")
            if layout.get("workspace", "WORK") != "WORK":
                raise PacketError("unsupported workspace layout")
            outer = layout.get("entry_files")
            if not isinstance(outer, dict):
                raise PacketError("missing outer entry hashes")
            expected = {}
            for mapping, prefix in ((inventory, "WORK/"), (outer, "")):
                for name, digest in mapping.items():
                    safe_path(name)
                    full = prefix + name
                    if full == manifest_name or full in expected:
                        raise PacketError("overlapping manifest inventory")
                    if not isinstance(digest, str) or not re.fullmatch("[0-9a-f]{64}", digest):
                        raise PacketError("invalid SHA-256: " + name)
                    expected[full] = digest
            if set(files) != set(expected) | {manifest_name}:
                raise PacketError("manifest/archive inventory mismatch")
            for name, digest in expected.items():
                if digests[name] != digest:
                    raise PacketError("SHA-256 mismatch: " + name)
            return {"integrity": "verified", "files": len(files), "directories": len(directories),
                    "required_inodes": len(files) + len(directories), "expanded_bytes": actual,
                    "declared_expanded_bytes": declared, "manifest_files_verified": len(inventory),
                    "outer_entry_sha256": {name: digests[name] for name in outer},
                    "manifest_sha256": digests[manifest_name],
                    "file_sizes": [info.file_size for info in files.values()],
                    "limits": {"entry_bytes": max_entry_bytes, "total_bytes": max_total_bytes,
                               "manifest_bytes": MAX_MANIFEST_BYTES, "entries": MAX_ENTRIES}}
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, UnicodeError, json.JSONDecodeError, EOFError, zlib.error) as exc:
        raise PacketError(str(exc)) from exc

def capacity_report(report, *, free_bytes, free_inodes, block_size, readonly=False):
    """Conservative data-block estimate; metadata/journal/reserves can need more."""
    block_size = max(1, block_size)
    allocated = sum(((size + block_size - 1) // block_size) * block_size for size in report["file_sizes"])
    allocated += report["directories"] * block_size
    reasons = []
    if allocated > free_bytes:
        reasons.append("insufficient_bytes")
    if report["required_inodes"] > free_inodes:
        reasons.append("insufficient_inodes")
    if readonly:
        reasons.append("read_only_filesystem")
    return {"sufficient": not reasons, "reasons": reasons, "free_bytes": free_bytes,
            "free_inodes": free_inodes, "required_allocated_bytes": allocated,
            "required_inodes": report["required_inodes"], "block_size": block_size,
            "read_only": readonly, "scope": "new extraction; no reuse; excludes runtime/Git and filesystem metadata overhead"}

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet")
    parser.add_argument("destination", help="existing directory on target filesystem")
    args = parser.parse_args(argv)
    try:
        destination = Path(args.destination)
        if not destination.is_dir():
            raise OSError("destination must be an existing directory")
        report = verify_packet(args.packet)
        digest = hashlib.sha256()
        with open(args.packet, "rb") as packet:
            for chunk in iter(lambda: packet.read(CHUNK), b""):
                digest.update(chunk)
        report["packet_sha256"] = digest.hexdigest()
        fs = os.statvfs(destination)
        report["destination"] = str(destination.resolve())
        report["capacity"] = capacity_report(report, free_bytes=fs.f_bavail * fs.f_frsize,
            free_inodes=fs.f_favail, block_size=fs.f_frsize,
            readonly=bool(fs.f_flag & getattr(os, "ST_RDONLY", 1)))
        report.pop("file_sizes")
        report["status"] = "ok" if report["capacity"]["sufficient"] else "insufficient_capacity"
        code = 0 if report["capacity"]["sufficient"] else 3
    except PacketError as exc:
        report, code = {"status": "invalid_packet", "error": str(exc)}, 2
    except OSError as exc:
        report, code = {"status": "io_error", "error": str(exc)}, 4
    print(json.dumps(report, sort_keys=True))
    return code

if __name__ == "__main__":
    raise SystemExit(main())
