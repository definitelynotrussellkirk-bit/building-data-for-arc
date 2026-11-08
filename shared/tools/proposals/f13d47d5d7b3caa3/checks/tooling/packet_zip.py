#!/usr/bin/env python3
"""Stream-check an ARC full-review packet or safely extract explicit paths.

This independent utility does not run packet review commands, draw assignments,
rewrite the manifest, or certify an extracted tree. Python standard library only.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import uuid
import zipfile


CHUNK_BYTES = 1024 * 1024
MAX_MANIFEST_BYTES = 32 * 1024 * 1024
PACKET_SCHEMA = "arcpuzzles-full-packet-v2"


class PacketError(Exception):
    """Invalid packet, unsafe destination, or unsuccessful extraction."""


def safe_name(name: str) -> str:
    """Return the canonical path without a directory slash; never normalize it."""
    if not isinstance(name, str) or not name or name.startswith("/"):
        raise PacketError(f"unsafe path: {name!r}")
    canonical = name[:-1] if name.endswith("/") else name
    parts = canonical.split("/")
    if (any(part in ("", ".", "..") or part.endswith((".", " ")) for part in parts)
            or "\\" in name or ":" in name or any(ord(c) < 32 for c in name)):
        raise PacketError(f"unsafe path: {name!r}")
    return canonical


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PacketError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def timestamp(info: zipfile.ZipInfo) -> float:
    # ZIP carries a local wall time, with no timezone or sub-second information.
    try:
        return datetime.datetime(*info.date_time).timestamp()
    except (OverflowError, OSError, ValueError) as error:
        raise PacketError(f"invalid ZIP timestamp: {info.filename}") from error


class Packet:
    def __init__(self, archive: zipfile.ZipFile):
        self.archive = archive
        self.files = {}
        self.directories = {}
        seen = set()
        for info in archive.infolist():
            # ZipInfo.filename may silently truncate an embedded NUL.
            if info.orig_filename != info.filename:
                raise PacketError(f"unsafe original member name: {info.orig_filename!r}")
            name = safe_name(info.filename)
            if info.filename in seen:
                raise PacketError(f"duplicate archive member: {info.filename}")
            seen.add(info.filename)
            if name in self.files or name in self.directories:
                raise PacketError(f"file/directory collision: {name}")
            mode = info.external_attr >> 16
            kind = stat.S_IFMT(mode)
            allowed = (0, stat.S_IFDIR) if info.is_dir() else (0, stat.S_IFREG)
            if kind not in allowed:
                raise PacketError(f"unsupported member type (including symlinks): {info.filename}")
            if mode & 0o7000:
                raise PacketError(f"privileged permission bits are unsupported: {info.filename}")
            if info.flag_bits & 1:
                raise PacketError(f"encrypted member is unsupported: {info.filename}")
            if info.is_dir() and info.file_size:
                raise PacketError(f"directory carries file data: {info.filename}")
            if info.is_dir():
                self.directories[name] = info
            else:
                self.files[name] = info
        for name in (*self.files, *self.directories):
            parts = name.split("/")
            for length in range(1, len(parts)):
                parent = "/".join(parts[:length])
                if parent in self.files:
                    raise PacketError(f"file/directory collision: {parent}")

        candidates = [name for name in ("PACKET-MANIFEST.json", "WORK/PACKET-MANIFEST.json")
                      if name in self.files]
        if len(candidates) != 1:
            raise PacketError("expected exactly one supported PACKET-MANIFEST.json location")
        self.manifest_name = candidates[0]
        manifest_info = self.files[self.manifest_name]
        if manifest_info.file_size > MAX_MANIFEST_BYTES:
            raise PacketError(f"manifest exceeds {MAX_MANIFEST_BYTES} byte limit")
        raw = archive.read(manifest_info)
        self.manifest_sha256 = hashlib.sha256(raw).hexdigest()
        try:
            manifest = json.loads(raw, object_pairs_hook=unique_object)
        except (ValueError, UnicodeError) as error:
            raise PacketError(f"invalid manifest JSON: {error}") from error
        if not isinstance(manifest, dict) or manifest.get("schema") != PACKET_SCHEMA:
            raise PacketError(f"unsupported manifest schema; expected {PACKET_SCHEMA}")
        self.manifest = manifest
        self.manifest_bytes = raw

        self.expected = {}
        if self.manifest_name.startswith("WORK/"):
            layout = manifest.get("layout")
            if not isinstance(layout, dict) or layout.get("workspace") != "WORK":
                raise PacketError("manifest layout does not match WORK/ member paths")
            self.workspace = "WORK"
            self._add_expected(manifest.get("files"), "WORK/")
            self._add_expected(layout.get("entry_files"), "")
        else:
            if "layout" in manifest:
                raise PacketError("flat packet must not declare a workspace layout")
            self.workspace = "."
            self._add_expected(manifest.get("files"), "")
        missing = self.expected.keys() - self.files.keys()
        extra = self.files.keys() - self.expected.keys() - {self.manifest_name}
        if missing:
            raise PacketError(f"manifest-listed file is missing: {sorted(missing)[0]}")
        if extra:
            raise PacketError(f"unlisted archive file: {sorted(extra)[0]}")

    def _add_expected(self, mapping, prefix):
        if not isinstance(mapping, dict):
            raise PacketError("manifest files/entry_files must be SHA-256 mappings")
        for relative, expected in mapping.items():
            name = prefix + safe_name(relative)
            if relative.endswith("/"):
                raise PacketError(f"manifest file path is a directory: {relative}")
            if name == self.manifest_name or name in self.expected:
                raise PacketError(f"manifest path collision: {name}")
            if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
                raise PacketError(f"invalid SHA-256 value for {name}")
            self.expected[name] = expected

    def stream(self, name, output=None):
        info = self.files[name]
        expected = self.manifest_sha256 if name == self.manifest_name else self.expected[name]
        digest = hashlib.sha256()
        count = 0
        with self.archive.open(info) as source:
            while chunk := source.read(CHUNK_BYTES):
                digest.update(chunk)
                count += len(chunk)
                if output is not None:
                    output.write(chunk)
        if count != info.file_size:
            raise PacketError(f"uncompressed size mismatch: {name}")
        if digest.hexdigest() != expected:
            raise PacketError(f"SHA-256 mismatch: {name}")
        return count

    def report(self, operation):
        return {"schema": "arc-packet-zip-report-v1", "operation": operation,
                "manifest_sha256": self.manifest_sha256, "workspace": self.workspace,
                "full_tree_verified": False}

    def verify(self):
        total = sum(self.stream(name) for name in sorted(self.expected))
        return {**self.report("zip-manifest-integrity"),
                "verified_file_count": len(self.expected), "verified_uncompressed_bytes": total,
                "manifest_file_bytes": self.files[self.manifest_name].file_size}

    def select(self, paths):
        selected_files = set()
        selected_dirs = set()
        for path in paths:
            safe_name(path)
            if path.endswith("/"):
                files = {name for name in self.files if name.startswith(path)}
                dirs = {name for name in self.directories
                        if name == path[:-1] or name.startswith(path)}
            else:
                files = {path} if path in self.files else set()
                dirs = set()
            if not files and not dirs:
                raise PacketError(f"path matched no archive members: {path}")
            selected_files.update(files)
            selected_dirs.update(dirs)
        needed_dirs = set(selected_dirs)
        for name in (*selected_files, *selected_dirs):
            parts = name.split("/")
            needed_dirs.update("/".join(parts[:n]) for n in range(1, len(parts)))
        return sorted(selected_files), sorted(needed_dirs, key=lambda value: (value.count("/"), value))

    def selection_report(self, paths, files):
        return {**self.report("selection-plan"), "requested_paths": paths,
                "selected_file_count": len(files),
                "selected_uncompressed_bytes": sum(self.files[name].file_size for name in files),
                "selected_bytes_verified": False}


def inspect_directory(path: Path):
    """Reject existing symlinks, including in every destination ancestor."""
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            status = current.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(status.st_mode):
            raise PacketError(f"destination symlink is forbidden: {current}")
        if not stat.S_ISDIR(status.st_mode):
            raise PacketError(f"destination ancestor is not a directory: {current}")


def open_directory(path: Path, created=None):
    """Open a directory by walking no-follow descriptors from filesystem root."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptor = os.open(path.anchor, flags)
    current = Path(path.anchor)
    try:
        for part in path.parts[1:]:
            current /= part
            if created is not None:
                try:
                    os.mkdir(part, 0o700, dir_fd=descriptor)
                    created.append(current)
                except FileExistsError:
                    pass
            next_descriptor = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def set_metadata(descriptor, info=None):
    if info is None:
        os.fchmod(descriptor, 0o755)
        return
    stamp = timestamp(info)
    os.utime(descriptor, (stamp, stamp))
    os.fchmod(descriptor, stat.S_IMODE(info.external_attr >> 16))


def rollback(files, directories):
    failures = []
    for path, identity in reversed(files):
        try:
            descriptor = open_directory(path.parent)
            try:
                status = os.stat(path.name, dir_fd=descriptor, follow_symlinks=False)
                if (status.st_dev, status.st_ino) == identity:
                    os.unlink(path.name, dir_fd=descriptor)
                else:
                    failures.append(str(path))
            finally:
                os.close(descriptor)
        except OSError:
            failures.append(str(path))
    for path in reversed(directories):
        try:
            descriptor = open_directory(path.parent)
            try:
                os.rmdir(path.name, dir_fd=descriptor)
            finally:
                os.close(descriptor)
        except OSError:
            failures.append(str(path))
    return failures


def extract(packet, destination, paths):
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        raise PacketError("safe extraction requires POSIX no-follow directory descriptors")
    destination = Path(os.path.abspath(destination))
    files, dirs = packet.select(paths)
    inspect_directory(destination)
    for name in dirs:
        inspect_directory(destination / name)
    for name in files:
        path = destination / name
        if os.path.lexists(path):
            raise PacketError(f"destination file already exists: {path}")
        info = packet.files[name]
        if info.create_system != 3:
            raise PacketError(f"POSIX permission metadata is required for extraction: {name}")
        timestamp(info)
    for name in dirs:
        if name in packet.directories:
            info = packet.directories[name]
            if info.create_system != 3:
                raise PacketError(f"POSIX directory metadata is required for extraction: {name}")
            timestamp(info)
    created_dirs = []
    created_files = []
    try:
        for directory in (destination, *(destination / name for name in dirs)):
            descriptor = open_directory(directory, created_dirs)
            os.close(descriptor)
        for name in files:
            target = destination / name
            descriptor = open_directory(target.parent)
            temporary = ".arc-packet-" + uuid.uuid4().hex
            try:
                output_descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                            0o600, dir_fd=descriptor)
                try:
                    with os.fdopen(output_descriptor, "wb") as output:
                        packet.stream(name, output)
                        output.flush()
                        set_metadata(output.fileno(), packet.files[name])
                        status = os.fstat(output.fileno())
                    # An atomic, no-overwrite commit; no second copy of file data.
                    os.link(temporary, target.name, src_dir_fd=descriptor,
                            dst_dir_fd=descriptor, follow_symlinks=False)
                    created_files.append((target, (status.st_dev, status.st_ino)))
                finally:
                    os.unlink(temporary, dir_fd=descriptor)
            finally:
                os.close(descriptor)
        for directory in reversed(created_dirs):
            descriptor = open_directory(directory)
            try:
                try:
                    name = directory.relative_to(destination).as_posix()
                except ValueError:
                    name = ""
                set_metadata(descriptor, packet.directories.get(name))
            finally:
                os.close(descriptor)
    except BaseException as error:
        failed_cleanup = rollback(created_files, created_dirs)
        if failed_cleanup:
            raise PacketError(f"extraction failed ({error}); cleanup incomplete for "
                              f"{len(failed_cleanup)} paths; inspect destination") from error
        raise
    report = packet.selection_report(paths, files)
    report.update(operation="selected-extraction", selected_bytes_verified=True,
                  destination=str(destination), created_directory_count=len(created_dirs))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    verify = commands.add_parser("verify", help="stream-check all manifest-listed ZIP files")
    verify.add_argument("archive", type=Path)
    for name in ("plan", "extract"):
        command = commands.add_parser(name, help="inspect or extract explicit ZIP-relative paths")
        command.add_argument("archive", type=Path)
        if name == "extract":
            command.add_argument("destination", type=Path)
        command.add_argument("--path", action="append", required=True, dest="paths",
                             help="exact file, or directory prefix ending in /; repeatable")
    arguments = parser.parse_args(argv)
    try:
        with zipfile.ZipFile(arguments.archive, "r") as archive:
            packet = Packet(archive)
            if arguments.command == "verify":
                report = packet.verify()
            elif arguments.command == "plan":
                files, _ = packet.select(arguments.paths)
                report = packet.selection_report(arguments.paths, files)
            else:
                report = extract(packet, arguments.destination, arguments.paths)
            report["archive"] = str(arguments.archive.absolute())
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except (PacketError, OSError, ValueError, RuntimeError, NotImplementedError,
            zipfile.BadZipFile, zipfile.LargeZipFile) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("ERROR: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
