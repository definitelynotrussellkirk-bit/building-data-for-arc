#!/usr/bin/env python3
"""Verify and resume extraction of an issued ARCpuzzles v2 review packet.

Python 3.12+ on POSIX. Standard library only. This program never imports or
executes packet code, draws an assignment, evaluates a rule, or deletes a
reviewer's file. Verification reads source bytes only to calculate digests.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import errno
import fcntl
import hashlib
import json
import lzma
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import time
import uuid
import zipfile
import zlib

SCHEMA = "arcpuzzles-full-packet-v2"
MANIFEST = "WORK/PACKET-MANIFEST.json"
STATE_NAME = ".arc-packet-recovery.json"
LOCK_NAME = ".arc-packet-recovery.lock"
CHUNK = 1024 * 1024
DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
DIGEST = re.compile(r"[0-9a-f]{64}\Z")


class RecoveryError(Exception):
    """A machine-readable rejection or environmental failure."""

    def __init__(self, code, message, **details):
        super().__init__(message)
        self.code = code
        self.details = details


def _invalid(message, **details):
    raise RecoveryError("invalid_archive", message, **details)


def _conflict(message, **details):
    raise RecoveryError("destination_conflict", message, **details)


def _io_error(exc):
    return RecoveryError(
        "io_error", str(exc), errno=exc.errno,
        recovery="Keep the original archive and destination. Resume with the same command after resolving the error.",
    )


def _read_chunk(source):
    try:
        return source.read(CHUNK)
    except OSError as exc:
        # BZIP2 corruption uses a generic OSError without a filesystem errno.
        # Limit this classification to decompression reads, not destination I/O.
        if exc.errno is None and isinstance(source, zipfile.ZipExtFile):
            _invalid("Invalid compressed member: " + str(exc))
        raise


def _hash_stream(source):
    digest = hashlib.sha256()
    count = 0
    while chunk := _read_chunk(source):
        digest.update(chunk)
        count += len(chunk)
    return digest.hexdigest(), count


def _copy_stream(source, destination):
    """Copy one member to its unpublished temporary file and hash its bytes."""
    digest = hashlib.sha256()
    count = 0
    while chunk := _read_chunk(source):
        if destination.write(chunk) != len(chunk):
            raise OSError(errno.EIO, "Short write while extracting a member")
        digest.update(chunk)
        count += len(chunk)
    return digest.hexdigest(), count


def _safe_name(name, directory=False):
    if not isinstance(name, str) or not name:
        _invalid("Empty or non-string archive path")
    clean = name[:-1] if directory and name.endswith("/") else name
    if (
        not clean or "\x00" in name or "\\" in name or ":" in name
        or clean.startswith("/")
        or any(part in ("", ".", "..") for part in clean.split("/"))
        or str(PurePosixPath(clean)) != clean
    ):
        _invalid("Unsafe archive path", path=name)
    return clean


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            _invalid("Duplicate JSON key in packet manifest", key=key)
        value[key] = item
    return value


def _parents(names):
    result = set()
    for name in names:
        parts = name.split("/")
        result.update("/".join(parts[:i]) for i in range(1, len(parts)))
    return result


def _stat_identity(handle):
    value = os.fstat(handle.fileno())
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


@contextmanager
def _checked_archive(archive):
    """Keep one verified archive handle open through any extraction."""
    started = time.monotonic()
    archive = Path(archive).absolute()
    try:
        with archive.open("rb") as raw:
            initial = _stat_identity(raw)
            if not stat.S_ISREG(os.fstat(raw.fileno()).st_mode):
                _invalid("Archive must be a regular file")
            archive_hash, archive_bytes = _hash_stream(raw)
            raw.seek(0)
            with zipfile.ZipFile(raw) as zipped:
                members = {}
                directories = set()
                names_seen = set()
                for info in zipped.infolist():
                    if info.orig_filename != info.filename:
                        _invalid("Archive member name was normalized or truncated")
                    name = _safe_name(info.filename, info.is_dir())
                    if name in names_seen:
                        _invalid("Duplicate archive path", path=name)
                    names_seen.add(name)
                    kind = stat.S_IFMT(info.external_attr >> 16)
                    if info.flag_bits & 1:
                        _invalid("Encrypted archive member", path=name)
                    allowed = (0, stat.S_IFDIR) if info.is_dir() else (0, stat.S_IFREG)
                    if kind not in allowed:
                        _invalid("Symlink or special archive member", path=name)
                    if info.is_dir():
                        if info.file_size:
                            _invalid("Nonempty directory archive member", path=name)
                        directories.add(name)
                    else:
                        members[name] = info
                if MANIFEST not in members:
                    _invalid("Missing packet manifest")
                try:
                    manifest_bytes = zipped.read(members[MANIFEST])
                except OSError as exc:
                    if exc.errno is None:
                        _invalid("Invalid compressed manifest: " + str(exc))
                    raise
                manifest = json.loads(manifest_bytes, object_pairs_hook=_unique_object)
                if not isinstance(manifest, dict):
                    _invalid("Packet manifest must be an object")
                encoder = json.JSONEncoder(
                    sort_keys=True, ensure_ascii=False,
                    separators=(",", ":"), allow_nan=False,
                )
                position = 0
                for fragment in encoder.iterencode(manifest):
                    encoded = fragment.encode("utf-8")
                    if manifest_bytes[position:position + len(encoded)] != encoded:
                        _invalid("Manifest is not canonical or has unsupported schema")
                    position += len(encoded)
                if position != len(manifest_bytes) or manifest.get("schema") != SCHEMA:
                    _invalid("Manifest is not canonical or has unsupported schema")
                layout = manifest.get("layout")
                if not isinstance(layout, dict) or layout.get("workspace") != "WORK":
                    _invalid("Unsupported packet layout")
                entries = layout.get("entry_files")
                files = manifest.get("files")
                if not isinstance(entries, dict) or set(entries) != {"START-HERE.md", "review.py"}:
                    _invalid("Unexpected outer entry-file inventory")
                if not isinstance(files, dict) or not files:
                    _invalid("Missing workspace file inventory")
                expected = {}
                for name, digest in entries.items():
                    expected[_safe_name(name)] = digest
                for name, digest in files.items():
                    path = "WORK/" + _safe_name(name)
                    if path in expected or path == MANIFEST:
                        _invalid("Colliding manifest path", path=path)
                    # Reuse the ZIP index's path strings instead of retaining a second
                    # full set of long task/evidence paths.
                    stored = members.get(path)
                    expected[stored.filename if stored is not None else path] = digest
                for name, digest in expected.items():
                    if not isinstance(digest, str) or not DIGEST.fullmatch(digest):
                        _invalid("Invalid SHA-256 in manifest", path=name)
                manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
                expected[MANIFEST] = manifest_hash
                parent_names = _parents(expected)
                if any(name in expected for name in parent_names):
                    _invalid("Archive file is also a parent directory")
                missing = sorted(name for name in expected if name not in members)
                extra = sorted(name for name in members if name not in expected)
                if missing or extra or directories - parent_names:
                    _invalid(
                        "Archive inventory differs from its issued manifest",
                        missing=missing[:20], missing_count=len(missing),
                        unexpected=extra[:20], unexpected_count=len(extra),
                        unexpected_directories=sorted(directories - parent_names)[:20],
                    )
                workspace_files = len(files)
                outer_entry_files = len(entries)
                implied_directories = len(parent_names)
                # Rich generator metadata is not needed for content verification.
                # Keep digests and the ZIP index, then release the parsed remainder
                # before decompressing member payloads.
                del manifest, manifest_bytes, files, layout, entries, parent_names
                del names_seen, encoder, fragment, encoded
                total_bytes = 0
                for name, info in members.items():
                    with zipped.open(info) as source:
                        digest, size = _hash_stream(source)
                    if size != info.file_size or digest != expected[name]:
                        _invalid("Archive member checksum mismatch", path=name)
                    total_bytes += size
                # Directory entries have no content, but reading them checks their CRCs.
                for info in zipped.infolist():
                    if info.is_dir():
                        with zipped.open(info) as source:
                            if source.read():
                                _invalid("Nonempty directory archive member")
                if _stat_identity(raw) != initial:
                    _invalid("Archive changed during verification")
                report = {
                    "schema": "arc-packet-recovery-receipt-v1",
                    "status": "verified",
                    "archive": str(archive),
                    "archive_name": archive.name,
                    "archive_bytes": archive_bytes,
                    "archive_sha256": archive_hash,
                    "manifest_sha256": manifest_hash,
                    "verified_files": len(members),
                    "workspace_files": workspace_files,
                    "outer_entry_files": outer_entry_files,
                    "zip_directory_entries": len(directories),
                    "uncompressed_bytes": total_bytes,
                    "implied_directories": implied_directories,
                    "minimum_filesystem_entries": len(members) + implied_directories,
                    "file_data_bytes_4k_blocks": sum(
                        ((info.file_size + 4095) // 4096) * 4096 for info in members.values()
                    ),
                    "verification_seconds": round(time.monotonic() - started, 6),
                    "scope": "Archive SHA-256, manifest, inventory, per-file SHA-256 and ZIP CRC only.",
                    "packet_code_executed": False,
                    "assignment_drawn": False,
                }
                yield report, zipped, members, expected
                if _stat_identity(raw) != initial:
                    _invalid("Archive changed while it was in use")
    except RecoveryError:
        raise
    except (zipfile.BadZipFile, zipfile.LargeZipFile, UnicodeError, ValueError, RuntimeError, EOFError, zlib.error, lzma.LZMAError) as exc:
        _invalid(str(exc))
    except OSError as exc:
        raise _io_error(exc) from exc


def verify_archive(archive):
    with _checked_archive(archive) as (report, _, __, ___):
        return dict(report)


def _open_directory(parts, base_fd=None, create=False):
    """Traverse directory descriptors; never follow a destination symlink."""
    current = os.open("/", DIR_FLAGS) if base_fd is None else os.dup(base_fd)
    try:
        for part in parts:
            try:
                following = os.open(part, DIR_FLAGS, dir_fd=current)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(part, mode=0o755, dir_fd=current)
                    os.fsync(current)
                except FileExistsError:
                    pass
                following = os.open(part, DIR_FLAGS, dir_fd=current)
            os.close(current)
            current = following
        return current
    except OSError as exc:
        os.close(current)
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            _conflict("Destination contains a symlink or non-directory component")
        raise


def _open_regular(parent_fd, name):
    try:
        descriptor = os.open(name, READ_FLAGS, dir_fd=parent_fd)
    except FileNotFoundError:
        return None
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            _conflict("Destination file is a symlink or invalid path", path=name)
        raise
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        _conflict("Destination file is not a regular file", path=name)
    return descriptor


@contextmanager
def _atomic_target(parent_fd, final_name, mode=0o644):
    """Publish by a no-overwrite hard link, cleaning only our own temporary."""
    temporary = ".arc-recover-" + uuid.uuid4().hex
    descriptor = os.open(
        temporary, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600, dir_fd=parent_fd,
    )
    try:
        with os.fdopen(descriptor, "w+b") as target:
            yield target
            target.flush()
            os.fchmod(target.fileno(), mode)
            os.fsync(target.fileno())
        try:
            os.link(
                temporary, final_name,
                src_dir_fd=parent_fd, dst_dir_fd=parent_fd, follow_symlinks=False,
            )
        except FileExistsError:
            _conflict("Destination appeared while extracting; it was preserved", path=final_name)
        os.unlink(temporary, dir_fd=parent_fd)
        os.fsync(parent_fd)
    finally:
        try:
            os.unlink(temporary, dir_fd=parent_fd)
        except FileNotFoundError:
            pass


def _state(root_fd):
    descriptor = _open_regular(root_fd, STATE_NAME)
    if descriptor is None:
        return None
    with os.fdopen(descriptor, "rb") as source:
        if os.fstat(source.fileno()).st_size > 16384:
            _conflict("Invalid recovery identity record")
        try:
            value = json.load(source)
        except (ValueError, UnicodeError):
            _conflict("Invalid recovery identity record")
    if not isinstance(value, dict):
        _conflict("Invalid recovery identity record")
    return value


def extract_archive(archive, destination):
    destination = Path(os.path.abspath(destination))
    written = 0
    reused = 0
    try:
        with _checked_archive(archive) as (report, zipped, members, expected):
            root_fd = _open_directory(destination.parts[1:], create=True)
            lock_fd = None
            try:
                try:
                    lock_fd = os.open(
                        LOCK_NAME, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                        0o600, dir_fd=root_fd,
                    )
                except OSError as exc:
                    if exc.errno == errno.ELOOP:
                        _conflict("Recovery lock is a symlink")
                    raise
                if not stat.S_ISREG(os.fstat(lock_fd).st_mode):
                    _conflict("Recovery lock is not a regular file")
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    _conflict("Another recovery process owns this destination")
                identity = {
                    "schema": "arc-packet-recovery-destination-v1",
                    "archive_sha256": report["archive_sha256"],
                    "manifest_sha256": report["manifest_sha256"],
                }
                saved = _state(root_fd)
                if saved is not None and saved != identity:
                    _conflict("Destination belongs to a different archive or identity record")
                present = set()
                # Inspect ALL existing packet files before writing any archive member.
                for name, digest in expected.items():
                    parts = name.split("/")
                    try:
                        parent_fd = _open_directory(parts[:-1], base_fd=root_fd)
                    except FileNotFoundError:
                        continue
                    try:
                        descriptor = _open_regular(parent_fd, parts[-1])
                        if descriptor is None:
                            continue
                        with os.fdopen(descriptor, "rb") as source:
                            actual, _ = _hash_stream(source)
                        if actual != digest:
                            _conflict("Existing file differs; reviewer edits were preserved", path=name)
                        present.add(name)
                    finally:
                        os.close(parent_fd)
                reused = len(present)
                if saved is None:
                    with _atomic_target(root_fd, STATE_NAME, mode=0o600) as target:
                        target.write(json.dumps(identity, sort_keys=True, indent=2).encode() + b"\n")
                for name, info in members.items():
                    if name in present:
                        continue
                    parts = name.split("/")
                    parent_fd = _open_directory(parts[:-1], base_fd=root_fd, create=True)
                    try:
                        permissions = (info.external_attr >> 16) & 0o777
                        permissions = permissions or 0o644
                        with _atomic_target(parent_fd, parts[-1], mode=permissions) as target:
                            with zipped.open(info) as source:
                                actual, size = _copy_stream(source, target)
                            if actual != expected[name] or size != info.file_size:
                                _invalid("Member changed during extraction", path=name)
                        written += 1
                    finally:
                        os.close(parent_fd)
                result = dict(report)
                result.update(
                    status="extracted", destination=str(destination),
                    files_written=written, files_reused=reused,
                    next_commands=[
                        "python3 review.py verify",
                        "python3 review.py start",
                        "python3 review.py duties",
                    ],
                    next_commands_cwd=str(destination),
                    note="Run the original verifier first. Keep this destination; never redraw to recover an interruption.",
                )
            finally:
                if lock_fd is not None:
                    os.close(lock_fd)
                os.close(root_fd)
            return result
    except OSError as exc:
        failure = _io_error(exc)
        failure.details.update(destination=str(destination), files_written=written, files_reused=reused)
        raise failure from exc
    except RecoveryError as exc:
        exc.details.update(destination=str(destination), files_written=written, files_reused=reused)
        raise


def _save_report(path, encoded, archive, destination=None):
    """Optional receipts never overwrite an existing file or packet entry."""
    report_path = Path(os.path.abspath(path))
    # Do not follow report/input symlinks merely to compare names. Atomic
    # no-overwrite publication also protects aliases and existing symlinks.
    archive_path = Path(os.path.abspath(archive))
    if report_path == archive_path:
        _conflict("Report path is the input archive")
    if destination is not None:
        root = Path(os.path.abspath(destination))
        if report_path == root / STATE_NAME or report_path == root / LOCK_NAME:
            _conflict("Report path is recovery state")
        if report_path.is_relative_to(root):
            relative = report_path.relative_to(root)
            if relative.parts and (relative.parts[0] == "WORK" or str(relative) in ("review.py", "START-HERE.md")):
                _conflict("Report path is inside issued packet files")
    parent_fd = _open_directory(report_path.parent.parts[1:])
    try:
        with _atomic_target(parent_fd, report_path.name) as target:
            target.write(encoded)
    finally:
        os.close(parent_fd)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("verify", "extract"):
        command = commands.add_parser(name)
        command.add_argument("archive", type=Path)
        if name == "extract":
            command.add_argument("destination", type=Path)
        command.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    exit_code = 0
    try:
        result = (
            verify_archive(args.archive)
            if args.command == "verify"
            else extract_archive(args.archive, args.destination)
        )
    except RecoveryError as exc:
        exit_code = {"invalid_archive": 1, "io_error": 2, "destination_conflict": 3}[exc.code]
        result = {
            "schema": "arc-packet-recovery-receipt-v1",
            "status": "blocked" if exc.code == "io_error" else "rejected",
            "code": exc.code, "message": str(exc), **exc.details,
            "packet_code_executed": False, "assignment_drawn": False,
        }
    encoded = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if args.report:
        try:
            _save_report(args.report, encoded, args.archive, getattr(args, "destination", None))
        except (RecoveryError, OSError) as exc:
            # The complete primary result still reaches stdout even when storage is full.
            warning = {
                "report_saved": False, "report_path": str(args.report),
                "error": str(exc), "primary_exit_code": exit_code,
            }
            print(json.dumps(warning, sort_keys=True), file=sys.stderr)
            if exit_code == 0:
                exit_code = 2
    sys.stdout.write(encoded.decode("utf-8"))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
