#!/usr/bin/env python3
"""Verify an ARCpuzzles packet in its ZIP without extraction or source imports.

Python 3.10+; standard library only. JSON goes to stdout. Exit 0 means every
listed file matched the canonical manifest, 1 means verification failed, and
2 is reserved for command-line usage errors. Supply a trusted manifest digest
to bind the check to a previously issued packet rather than only its internal
consistency. The program never draws an assignment or changes the archive.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
from typing import BinaryIO, Iterable
import zipfile
import zlib


PACKET_SCHEMA = "arcpuzzles-full-packet-v2"
REPORT_SCHEMA = "arcpuzzles-packet-zip-verification-v1"
CHUNK_BYTES = 1024 * 1024
MAX_MANIFEST_BYTES = 64 * 1024 * 1024
DEFAULT_MAX_EXPANDED_BYTES = 4 * 1024 * 1024 * 1024
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class VerificationError(Exception):
    def __init__(self, code: str, message: str, member: str | None = None):
        super().__init__(message)
        self.code = code
        self.member = member


def safe_path(name: str, code: str) -> None:
    if (not isinstance(name, str) or not name or "\\" in name or "\x00" in name
            or name.startswith("/") or re.match(r"^[A-Za-z]:", name)
            or any(part in {"", ".", ".."} for part in name.split("/"))):
        raise VerificationError(code, "Expected a normalized relative POSIX file path.", str(name))


def digest_stream(stream: BinaryIO) -> tuple[str, int]:
    return digest_chunks(iter(lambda: stream.read(CHUNK_BYTES), b""))


def digest_chunks(chunks: Iterable[bytes]) -> tuple[str, int]:
    digest = hashlib.sha256()
    count = 0
    for block in chunks:
        digest.update(block)
        count += len(block)
    return digest.hexdigest(), count


def checked_member_chunks(archive: zipfile.ZipFile, raw_archive: BinaryIO,
                          info: zipfile.ZipInfo) -> Iterable[bytes]:
    """Read the complete stored/DEFLATE stream, independent of declared output size.

    ZipExtFile truncates output to file_size before the caller sees it. Using
    that reader to verify file_size would therefore miss understated sizes.
    Let it validate local names and overlapping ranges, then decode the actual
    compressed extent with bounded output chunks and our own size/CRC checks.
    """
    if info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
        raise VerificationError("unsupported_compression", "Issued packets use stored or DEFLATE members.", info.filename)
    if info.compress_type == zipfile.ZIP_STORED and info.compress_size != info.file_size:
        raise VerificationError("member_size_mismatch", "Stored member's compressed and expanded sizes differ.", info.filename)
    with archive.open(info):
        pass
    raw_archive.seek(info.header_offset)
    header = raw_archive.read(30)
    if len(header) != 30 or header[:4] != b"PK\x03\x04":
        raise zipfile.BadZipFile("Invalid local member header")
    flags, method = struct.unpack_from("<HH", header, 6)
    if flags != info.flag_bits or method != info.compress_type:
        raise zipfile.BadZipFile("Local and central compression flags/method differ")
    if not flags & 8:  # With a data descriptor, local CRC/sizes may be zero.
        crc, compressed_size, expanded_size = struct.unpack_from("<III", header, 14)
        if (crc != info.CRC or compressed_size not in {info.compress_size, 0xffffffff}
                or expanded_size not in {info.file_size, 0xffffffff}):
            raise zipfile.BadZipFile("Local and central CRC/sizes differ")
    name_length, extra_length = struct.unpack_from("<HH", header, 26)
    raw_archive.seek(info.header_offset + 30 + name_length + extra_length)
    remaining = info.compress_size
    size = 0
    crc = 0
    decoder = zlib.decompressobj(-15) if method == zipfile.ZIP_DEFLATED else None
    while remaining:
        block = raw_archive.read(min(remaining, CHUNK_BYTES))
        if not block:
            raise zipfile.BadZipFile("Truncated compressed member data")
        remaining -= len(block)
        if decoder is not None and decoder.eof:
            raise zipfile.BadZipFile("Trailing bytes after DEFLATE stream")
        pending = block
        while True:
            if decoder is None:
                output = pending
            else:
                output = decoder.decompress(pending, CHUNK_BYTES)
                pending = decoder.unconsumed_tail
                if decoder.unused_data:
                    raise zipfile.BadZipFile("Trailing bytes after DEFLATE stream")
            size += len(output)
            if size > info.file_size:
                raise VerificationError("member_size_mismatch", "Actual expansion exceeds the declared member size.", info.filename)
            crc = zlib.crc32(output, crc)
            if output:
                yield output
            if decoder is None or decoder.eof or (not pending and len(output) < CHUNK_BYTES):
                break
    if decoder is not None and not decoder.eof:
        raise zipfile.BadZipFile("Truncated DEFLATE stream")
    if size != info.file_size:
        raise VerificationError("member_size_mismatch", "Actual expansion differs from the declared member size.", info.filename)
    if crc & 0xffffffff != info.CRC:
        raise zipfile.BadZipFile("Member CRC-32 mismatch")


def checked_inventory(value: object, *, path_code: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise VerificationError("manifest_inventory", "File inventory must be a path-to-SHA256 object.")
    for name, digest in value.items():
        safe_path(name, path_code)
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise VerificationError("manifest_inventory", "Expected a lowercase SHA-256 digest.", name)
    return value


def fingerprint(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns


def verify_packet(path: Path, *, expected_manifest_sha256: str | None = None,
                  max_expanded_bytes: int = DEFAULT_MAX_EXPANDED_BYTES) -> dict:
    """Return a JSON-compatible integrity report; no packet code is imported."""
    report = {"schema": REPORT_SCHEMA, "archive": str(path.resolve()), "status": "failed",
              "expected_manifest_sha256": expected_manifest_sha256, "verified_file_count": 0}
    try:
        if expected_manifest_sha256 is not None and not SHA256.fullmatch(expected_manifest_sha256):
            raise VerificationError("manifest_pin_invalid", "Expected a lowercase SHA-256 manifest pin.")
        if type(max_expanded_bytes) is not int or max_expanded_bytes < 1:
            raise VerificationError("expanded_size_limit", "Expansion budget must be a positive integer.")
        with path.open("rb") as raw_archive:
            original = fingerprint(os.fstat(raw_archive.fileno()))
            report["archive_sha256"], report["archive_bytes"] = digest_stream(raw_archive)
            raw_archive.seek(0)
            with zipfile.ZipFile(raw_archive) as archive:
                members = {}
                expanded = 0
                for info in archive.infolist():
                    safe_path(info.orig_filename, "unsafe_member_path")
                    if info.filename != info.orig_filename:
                        raise VerificationError("unsafe_member_path", "ZIP member name was truncated.", info.orig_filename)
                    kind = stat.S_IFMT(info.external_attr >> 16)
                    if info.is_dir() or kind not in {0, stat.S_IFREG} or info.external_attr & 0x10:
                        raise VerificationError("unsafe_member_type", "Only regular file members are allowed.", info.filename)
                    if info.flag_bits & 1:
                        raise VerificationError("encrypted_member", "Encrypted ZIP members are unsupported.", info.filename)
                    if info.filename in members:
                        raise VerificationError("duplicate_member", "Duplicate ZIP member name.", info.filename)
                    members[info.filename] = info
                    expanded += info.file_size
                report.update(member_count=len(members), expanded_bytes=expanded)
                if expanded > max_expanded_bytes:
                    raise VerificationError("expanded_size_limit", f"Declared expansion {expanded} exceeds budget {max_expanded_bytes}.")
                locations = [name for name in ("PACKET-MANIFEST.json", "WORK/PACKET-MANIFEST.json") if name in members]
                if len(locations) != 1:
                    raise VerificationError("manifest_location", "Expected exactly one root or WORK packet manifest.")
                manifest_name = locations[0]
                report["manifest_member"] = manifest_name
                if members[manifest_name].file_size > MAX_MANIFEST_BYTES:
                    raise VerificationError("manifest_size_limit", "Manifest exceeds the 64 MiB parser limit.", manifest_name)
                raw_manifest = b"".join(checked_member_chunks(archive, raw_archive, members[manifest_name]))
                if len(raw_manifest) > MAX_MANIFEST_BYTES:
                    raise VerificationError("manifest_size_limit", "Manifest exceeds the 64 MiB parser limit.", manifest_name)
                manifest_digest = hashlib.sha256(raw_manifest).hexdigest()
                report["manifest_sha256"] = manifest_digest
                if expected_manifest_sha256 is not None and manifest_digest != expected_manifest_sha256:
                    raise VerificationError("manifest_pin_mismatch", "Manifest does not match the supplied issued digest.", manifest_name)
                try:
                    manifest = json.loads(raw_manifest.decode("utf-8"))
                    canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False,
                                           separators=(",", ":"), allow_nan=False).encode("utf-8")
                except (UnicodeError, ValueError, TypeError) as error:
                    raise VerificationError("invalid_manifest", "Manifest is not a finite UTF-8 JSON object.", manifest_name) from error
                if raw_manifest != canonical:
                    raise VerificationError("noncanonical_manifest", "Manifest bytes are not in issued canonical JSON form.", manifest_name)
                if not isinstance(manifest, dict) or manifest.get("schema") != PACKET_SCHEMA:
                    raise VerificationError("manifest_schema", f"Expected schema {PACKET_SCHEMA}.", manifest_name)
                report["packet_schema"] = manifest["schema"]
                files = checked_inventory(manifest.get("files"), path_code="unsafe_manifest_path")
                prefix = "WORK/" if manifest_name.startswith("WORK/") else ""
                entries = {}
                layout = manifest.get("layout")
                if prefix:
                    if (not isinstance(layout, dict) or layout.get("workspace") != "WORK"
                            or not isinstance(layout.get("entry_files"), dict)
                            or set(layout["entry_files"]) != {"START-HERE.md", "review.py"}):
                        raise VerificationError("manifest_layout", "WORK layout requires exactly both outer entry files.", manifest_name)
                    entries = checked_inventory(layout["entry_files"], path_code="unsafe_manifest_path")
                elif layout is not None:
                    raise VerificationError("manifest_layout", "Flat packets must not declare a WORK layout.", manifest_name)
                expected = {prefix + name: digest for name, digest in files.items()}
                if manifest_name in expected:
                    raise VerificationError("manifest_inventory", "Manifest cannot list itself as a source file.", manifest_name)
                expected.update(entries)
                report.update(manifest_file_count=len(files), outer_file_count=len(entries))
                missing = sorted(set(expected) - members.keys())
                unexpected = sorted(members.keys() - set(expected) - {manifest_name})
                if missing:
                    raise VerificationError("missing_member", f"Missing {len(missing)} manifest-listed member(s); first shown.", missing[0])
                if unexpected:
                    raise VerificationError("unexpected_member", f"Found {len(unexpected)} unlisted member(s); first shown.", unexpected[0])
                for name, expected_digest in sorted(expected.items()):
                    actual_digest, size = digest_chunks(checked_member_chunks(archive, raw_archive, members[name]))
                    if size != members[name].file_size:
                        raise VerificationError("member_size_mismatch", "Actual expansion differs from declared size.", name)
                    if actual_digest != expected_digest:
                        raise VerificationError("hash_mismatch", "Member SHA-256 differs from the issued manifest.", name)
                    report["verified_file_count"] += 1
            if fingerprint(os.fstat(raw_archive.fileno())) != original or fingerprint(path.stat()) != original:
                raise VerificationError("archive_changed", "Archive changed while verification was running.")
        report.update(status="verified", errors=[])
    except VerificationError as error:
        item = {"code": error.code, "message": str(error)}
        if error.member is not None:
            item["member"] = error.member
        report["errors"] = [item]
    except (zipfile.BadZipFile, zipfile.LargeZipFile, EOFError, RuntimeError,
            NotImplementedError, UnicodeError, zlib.error) as error:
        report["errors"] = [{"code": "invalid_zip", "message": str(error)}]
    except OSError as error:
        report["errors"] = [{"code": "io_error", "message": str(error)}]
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--expected-manifest-sha256", help="trusted SHA-256 of the original issued canonical manifest")
    parser.add_argument("--max-expanded-bytes", type=int, default=DEFAULT_MAX_EXPANDED_BYTES,
                        help="maximum total declared expansion (default: 4 GiB; nothing is extracted)")
    args = parser.parse_args(argv)
    report = verify_packet(args.archive, expected_manifest_sha256=args.expected_manifest_sha256,
                           max_expanded_bytes=args.max_expanded_bytes)
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
