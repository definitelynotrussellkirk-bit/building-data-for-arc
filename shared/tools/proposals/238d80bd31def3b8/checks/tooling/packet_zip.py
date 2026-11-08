#!/usr/bin/env python3
"""Verify or selectively extract an ARCpuzzles full packet using only stdlib.

Payloads are streamed; only the central directory and bounded JSON manifest are
held in memory. No puzzle selection, seed generation, or review state is used.
"""

import argparse
from contextlib import contextmanager
import hashlib
import json
import lzma
import os
from pathlib import Path
import secrets
import stat
import sys
import zipfile
import zlib


CHUNK = 1024 * 1024
MANIFEST = "WORK/PACKET-MANIFEST.json"
MAX_MANIFEST = 64 * 1024 * 1024


class PacketError(Exception):
    """An archive or destination violates the recovery contract."""


def _safe_name(name, directory=False):
    if not isinstance(name, str):
        raise PacketError("unsafe path: expected text")
    normalized = name[:-1] if directory and name.endswith("/") else name
    if (not normalized or "\\" in normalized or ":" in normalized
            or any(ord(c) < 32 or ord(c) == 127 for c in normalized)
            or any(part in ("", ".", "..") for part in normalized.split("/"))):
        raise PacketError("unsafe path: " + repr(name))
    return normalized


def _sha(value):
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdefABCDEF" for c in value):
        raise PacketError("invalid SHA-256 value")
    return value.lower()


def _digest(stream, sink=None):
    sha = hashlib.sha256()
    size = 0
    while True:
        data = stream.read(CHUNK)
        if not data:
            return sha.hexdigest(), size
        sha.update(data)
        size += len(data)
        if sink is not None:
            sink.write(data)


def _unique_object(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise PacketError("duplicate JSON key: " + repr(name))
        result[name] = value
    return result


class Packet:
    """Validated metadata on one open ZIP; payload verification is explicit."""

    def __init__(self, archive, z, archive_hash, archive_size):
        self.archive = os.path.abspath(archive)
        self.z = z
        self.archive_hash = archive_hash
        self.archive_sha256 = archive_hash
        self.archive_size = archive_size
        self.entries = {}
        logical_names = set()
        for item in z.infolist():
            name = _safe_name(item.orig_filename, item.is_dir())
            if item.orig_filename != item.filename:
                raise PacketError("unsafe path: ZIP filename was truncated")
            if name in logical_names:
                raise PacketError("duplicate archive path: " + name)
            logical_names.add(name)
            kind = stat.S_IFMT(item.external_attr >> 16)
            allowed = (0, stat.S_IFDIR) if item.is_dir() else (0, stat.S_IFREG)
            if kind not in allowed:
                raise PacketError("archive symlink or special file: " + name)
            if item.flag_bits & 1:
                raise PacketError("encrypted archive entry: " + name)
            self.entries[item.filename] = item
        self.file_names = {name for name, item in self.entries.items() if not item.is_dir()}
        for name in logical_names:
            parts = name.split("/")
            if any("/".join(parts[:i]) in self.file_names for i in range(1, len(parts))):
                raise PacketError("file/directory collision: " + name)
        if MANIFEST not in self.file_names:
            raise PacketError("missing manifest: " + MANIFEST)
        if self.entries[MANIFEST].file_size > MAX_MANIFEST:
            raise PacketError("manifest exceeds 64 MiB limit")
        with z.open(self.entries[MANIFEST]) as source:
            raw = source.read(MAX_MANIFEST + 1)
        if len(raw) > MAX_MANIFEST:
            raise PacketError("manifest exceeds 64 MiB limit")
        self.manifest_hash = hashlib.sha256(raw).hexdigest()
        manifest = json.loads(raw, object_pairs_hook=_unique_object)
        self.manifest_raw = raw
        self.manifest = manifest
        if not isinstance(manifest, dict) or manifest.get("schema") != "arcpuzzles-full-packet-v2":
            raise PacketError("unsupported packet manifest schema")
        layout = manifest.get("layout")
        if not isinstance(layout, dict) or not isinstance(layout.get("entry_files"), dict) or not isinstance(manifest.get("files"), dict):
            raise PacketError("manifest requires files and layout.entry_files mappings")
        workspace = _safe_name(layout.get("workspace"))
        if MANIFEST != workspace + "/PACKET-MANIFEST.json":
            raise PacketError("manifest workspace does not match its archive location")
        self.hashes = {}
        for mapping, prefix in ((manifest["files"], workspace + "/"), (layout["entry_files"], "")):
            for relative, expected in mapping.items():
                name = prefix + _safe_name(relative)
                if name == MANIFEST or name in self.hashes:
                    raise PacketError("duplicate manifest file path: " + name)
                self.hashes[name] = _sha(expected)
        missing = set(self.hashes) - self.file_names
        extra = self.file_names - set(self.hashes) - {MANIFEST}
        if missing:
            raise PacketError("missing manifest entries in archive: " + repr(sorted(missing)[:4]))
        if extra:
            raise PacketError("unlisted archive files: " + repr(sorted(extra)[:4]))
        self.hashes[MANIFEST] = self.manifest_hash

    def select(self, files, prefixes):
        if not files and not prefixes:
            raise PacketError("extract requires at least one --file or --prefix")
        selected = set()
        for name in files:
            name = _safe_name(name)
            if name not in self.file_names:
                raise PacketError("requested file is missing: " + name)
            selected.add(name)
        for prefix in prefixes:
            prefix = _safe_name(prefix, directory=True) + "/"
            matches = {name for name in self.file_names if name.startswith(prefix)}
            if not matches:
                raise PacketError("requested prefix is missing: " + prefix)
            selected.update(matches)
        return sorted(selected)

    def copy_verified(self, name, sink=None):
        with self.z.open(self.entries[name]) as source:
            actual, size = _digest(source, sink)
        if actual != self.hashes[name] or size != self.entries[name].file_size:
            raise PacketError("hash mismatch: " + name)

    def verify(self, names):
        for name in names:
            self.copy_verified(name)

    def receipt(self, names, scope):
        selection = hashlib.sha256()
        for name in sorted(names):
            selection.update((name + "\0" + self.hashes[name] + "\n").encode("utf-8"))
        return {
            "schema": "arcpuzzles-packet-zip-receipt-v1", "status": "ok",
            "archive": self.archive, "archive_sha256": self.archive_hash,
            "archive_bytes": self.archive_size, "archive_entries": len(self.entries),
            "archive_files": len(self.file_names), "manifest": MANIFEST,
            "manifest_sha256": self.manifest_hash,
            "manifest_payload_files": len(self.hashes) - 1,
            "verification_scope": scope, "verified_files": len(names),
            "verified_bytes": sum(self.entries[name].file_size for name in names),
            "selection_sha256": selection.hexdigest(),
        }


@contextmanager
def open_packet(archive, expected_archive_sha256=None):
    """Open one source handle; detect source modification during the operation."""
    with open(archive, "rb") as raw:
        before = os.fstat(raw.fileno())
        archive_hash, size = _digest(raw)
        if expected_archive_sha256 is not None and archive_hash != _sha(expected_archive_sha256):
            raise PacketError("archive hash mismatch")
        raw.seek(0)
        with zipfile.ZipFile(raw) as z:
            yield Packet(archive, z, archive_hash, size)
        after = os.fstat(raw.fileno())
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        if any(getattr(before, key) != getattr(after, key) for key in fields):
            raise PacketError("archive changed during operation")


def _walk_dir(fd, parts, create=False):
    """Open each component relative to a pinned directory, without symlinks."""
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise PacketError("safe extraction requires POSIX O_NOFOLLOW and directory descriptors")
    current = os.dup(fd)
    try:
        for part in parts:
            if create:
                try:
                    os.mkdir(part, 0o755, dir_fd=current)
                except FileExistsError:
                    pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
            os.close(current)
            current = child
        return current
    except BaseException:
        os.close(current)
        raise


def _root_fd(path, create=False):
    root = os.open("/", os.O_RDONLY)
    try:
        return _walk_dir(root, Path(os.path.abspath(path)).parts[1:], create)
    finally:
        os.close(root)


def _matching_file(parent, leaf, expected):
    try:
        fd = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    except FileNotFoundError:
        return False
    with os.fdopen(fd, "rb") as source:
        if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
            raise PacketError("destination is not a regular file: " + leaf)
        actual, _ = _digest(source)
    if actual != expected:
        raise PacketError("existing file differs; refusing overwrite: " + leaf)
    return True


def _preflight(root, names, hashes):
    try:
        root_fd = _root_fd(root)
    except FileNotFoundError:
        return
    try:
        for name in names:
            parts = name.split("/")
            try:
                parent = _walk_dir(root_fd, parts[:-1])
            except FileNotFoundError:
                continue
            try:
                _matching_file(parent, parts[-1], hashes[name])
            finally:
                os.close(parent)
    finally:
        os.close(root_fd)


def _publish(parent, leaf, expected, writer):
    """Stage one file and publish with a no-overwrite hard link."""
    if _matching_file(parent, leaf, expected):
        return False
    temporary = ".packet-" + secrets.token_hex(16)
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644, dir_fd=parent)
    try:
        with os.fdopen(fd, "wb") as target:
            writer(target)
        try:
            os.link(temporary, leaf, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
            return True
        except FileExistsError:
            if _matching_file(parent, leaf, expected):
                return False
            raise PacketError("destination appeared during extraction: " + leaf)
    finally:
        os.unlink(temporary, dir_fd=parent)


def verify_archive(archive, expected_archive_sha256=None):
    with open_packet(archive, expected_archive_sha256) as packet:
        names = sorted(packet.file_names)
        packet.verify(names)
        receipt = packet.receipt(names, "all")
        receipt["operation"] = "verify"
    return receipt


def extract_archive(archive, destination, *, files=(), prefixes=(), expected_archive_sha256=None):
    with open_packet(archive, expected_archive_sha256) as packet:
        names = packet.select(files, prefixes)
        packet.verify(names)
        _preflight(destination, names, packet.hashes)
        root = _root_fd(destination, create=True)
        created = 0
        try:
            for name in names:
                parts = name.split("/")
                parent = _walk_dir(root, parts[:-1], create=True)
                try:
                    created += _publish(parent, parts[-1], packet.hashes[name], lambda sink: packet.copy_verified(name, sink))
                finally:
                    os.close(parent)
        finally:
            os.close(root)
        receipt = packet.receipt(names, "selected")
        receipt.update({
            "operation": "extract", "destination": os.path.abspath(destination),
            "requested_files": sorted(set(files)),
            "requested_prefixes": sorted({_safe_name(p, directory=True) + "/" for p in prefixes}),
            "created_files": created, "reused_files": len(names) - created,
        })
    return receipt


def write_receipt(path, receipt):
    data = (json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    path = Path(os.path.abspath(path))
    parent = _root_fd(path.parent, create=True)
    try:
        _publish(parent, path.name, hashlib.sha256(data).hexdigest(), lambda sink: sink.write(data))
    finally:
        os.close(parent)


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise PacketError(message)


def main(argv=None):
    parser = _Parser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("verify", "extract"):
        item = sub.add_parser(command)
        item.add_argument("archive")
        item.add_argument("--expected-archive-sha256")
        item.add_argument("--receipt", help="create compact JSON; preserve any differing existing file")
        if command == "extract":
            item.add_argument("destination")
            item.add_argument("--file", action="append", default=[], help="exact archive path; repeatable")
            item.add_argument("--prefix", action="append", default=[], help="archive directory prefix; repeatable")
    try:
        args = parser.parse_args(argv)
        if args.command == "verify":
            receipt = verify_archive(args.archive, args.expected_archive_sha256)
        else:
            receipt = extract_archive(args.archive, args.destination, files=args.file, prefixes=args.prefix,
                                      expected_archive_sha256=args.expected_archive_sha256)
        if args.receipt:
            write_receipt(args.receipt, receipt)
        print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
        return 0
    except (PacketError, OSError, ValueError, zipfile.BadZipFile, zipfile.LargeZipFile,
            RuntimeError, NotImplementedError, EOFError, zlib.error, lzma.LZMAError) as error:
        print(json.dumps({"status": "error", "error": str(error)}, separators=(",", ":")), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
