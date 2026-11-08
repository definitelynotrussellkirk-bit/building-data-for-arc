#!/usr/bin/env python3
"""Read immutable packet sources through a manifest-limited sparse overlay.

Only Path.is_file and Path.read_bytes are temporarily adapted. The original
review.py, build_full_return and validate_full_return execute without edits.
No imports, directory enumeration, exists, stat, is_symlink, baseline or solve
paths are virtualized. See ZIP_PACKET_OVERLAY.md for the trust boundary.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import importlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import resource
import runpy
import stat
import struct
import sys
import zipfile
import zlib

sys.dont_write_bytecode = True
_CHUNK = 1024 * 1024
_INDEX = struct.Struct("<QQI")  # central position, next local header, ordinal
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MANIFEST = "WORK/PACKET-MANIFEST.json"
_ORIGINAL_IS_FILE = Path.is_file
_ORIGINAL_READ_BYTES = Path.read_bytes


class IntegrityError(ValueError):
    """The sparse representation cannot safely preserve the packet contract."""


def _safe_name(name):
    if (not isinstance(name, str) or not name or "\\" in name or "\0" in name
            or name.startswith("/") or name.endswith("/")
            or any(part in {"", ".", ".."} for part in name.split("/"))
            or PurePosixPath(name).as_posix() != name):
        raise IntegrityError(f"Unsafe archive-relative path: {name!r}")
    return name


def _sha_stream(stream):
    digest = hashlib.sha256()
    total = 0
    while chunk := stream.read(_CHUNK):
        digest.update(chunk)
        total += len(chunk)
    return digest.hexdigest(), total


def _sha_file(path):
    with open(path, "rb") as stream:
        return _sha_stream(stream)[0]


def _signature(path):
    value = os.lstat(path)
    if not stat.S_ISREG(value.st_mode):
        raise IntegrityError(f"Input is not a regular nonsymlink file: {path}")
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


class CompactReadZip(zipfile.ZipFile):
    """Read-only stdlib ZIP decoding with a compact streamed directory index.

    The original archive has >100,000 entries. Retaining their ZipInfo objects
    costs ~95 MiB before loading its 19 MiB manifest. Store only names and packed
    offsets instead, reconstructing one ZipInfo when stdlib open() needs it.
    Unsupported formats fail closed; no ZIP validation is switched off.
    """
    def __init__(self, path):
        self.entries = {}
        super().__init__(path, "r")

    def _read_record(self):
        fp = self.fp
        raw = fp.read(zipfile.sizeCentralDir)
        if len(raw) != zipfile.sizeCentralDir:
            raise IntegrityError("Truncated ZIP central directory")
        fields = struct.unpack(zipfile.structCentralDir, raw)
        if fields[zipfile._CD_SIGNATURE] != zipfile.stringCentralDir:
            raise IntegrityError("Bad ZIP central-directory signature")
        name_raw = fp.read(fields[zipfile._CD_FILENAME_LENGTH])
        extra = fp.read(fields[zipfile._CD_EXTRA_FIELD_LENGTH])
        comment = fp.read(fields[zipfile._CD_COMMENT_LENGTH])
        if (len(name_raw) != fields[zipfile._CD_FILENAME_LENGTH]
                or len(extra) != fields[zipfile._CD_EXTRA_FIELD_LENGTH]
                or len(comment) != fields[zipfile._CD_COMMENT_LENGTH]):
            raise IntegrityError("Truncated ZIP central-directory entry")
        name = name_raw.decode("utf-8" if fields[zipfile._CD_FLAG_BITS] & 0x800 else "cp437")
        _safe_name(name)
        info = zipfile.ZipInfo(name)
        info.extra, info.comment = extra, comment
        info.header_offset = fields[zipfile._CD_LOCAL_HEADER_OFFSET]
        (info.create_version, info.create_system, info.extract_version, info.reserved,
         info.flag_bits, info.compress_type, clock, date, info.CRC, info.compress_size,
         info.file_size) = fields[1:12]
        info.volume, info.internal_attr, info.external_attr = fields[15:18]
        info._raw_time = clock
        info.date_time = ((date >> 9) + 1980, (date >> 5) & 15, date & 31,
                          clock >> 11, (clock >> 5) & 63, (clock & 31) * 2)
        decode = zipfile.ZipInfo._decodeExtra
        if decode.__code__.co_argcount == 2:
            info._decodeExtra(zlib.crc32(name_raw))
        else:
            info._decodeExtra()
        if info.filename != name or info.orig_filename != name:
            raise IntegrityError("ZIP filename alias is unsupported")
        info.header_offset += self._concat
        kind = stat.S_IFMT(info.external_attr >> 16)
        if kind not in {0, stat.S_IFREG} or info.volume:
            raise IntegrityError(f"Nonregular or multi-disk ZIP member: {name}")
        if (info.flag_bits & (1 | 0x20 | 0x40)
                or info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
                or info.extract_version > zipfile.MAX_EXTRACT_VERSION):
            raise IntegrityError(f"Unsupported ZIP member encoding: {name}")
        if info.file_size > 64 * 1024 * 1024:
            raise IntegrityError(f"ZIP member exceeds this helper's 64 MiB memory bound: {name}")
        return info

    def _RealGetContents(self):
        end = zipfile._EndRecData(self.fp)
        if not end:
            raise IntegrityError("Invalid ZIP end record")
        size, offset = end[zipfile._ECD_SIZE], end[zipfile._ECD_OFFSET]
        count = end[zipfile._ECD_ENTRIES_TOTAL]
        if (end[zipfile._ECD_DISK_NUMBER] or end[zipfile._ECD_DISK_START]
                or count != end[zipfile._ECD_ENTRIES_THIS_DISK]
                or count > 200000 or size > 128 * 1024 * 1024):
            raise IntegrityError("Unsupported ZIP directory size or disk layout")
        self._comment = end[zipfile._ECD_COMMENT]
        self._concat = end[zipfile._ECD_LOCATION] - size - offset
        self.start_dir = offset + self._concat
        if self.start_dir < 0:
            raise IntegrityError("Invalid ZIP central-directory offset")
        self.fp.seek(self.start_dir)
        stop = self.start_dir + size
        previous = None
        ordinal = 0
        while self.fp.tell() < stop:
            central = self.fp.tell()
            info = self._read_record()
            if info.filename in self.entries:
                raise IntegrityError(f"duplicate ZIP member: {info.filename}")
            if info.header_offset < 0 or info.header_offset >= self.start_dir:
                raise IntegrityError("Invalid ZIP local-header offset")
            if previous is not None:
                prior_name, prior_central, prior_local, prior_ordinal = previous
                if info.header_offset <= prior_local:
                    raise IntegrityError("Overlapping or unordered ZIP members are unsupported")
                self.entries[prior_name] = _INDEX.pack(prior_central, info.header_offset, prior_ordinal)
            self.entries[info.filename] = _INDEX.pack(central, self.start_dir, ordinal)
            previous = (info.filename, central, info.header_offset, ordinal)
            ordinal += 1
        if self.fp.tell() != stop or ordinal != count:
            raise IntegrityError("ZIP central-directory count or size mismatch")

    def getinfo(self, name):
        try:
            central, end, _ = _INDEX.unpack(self.entries[name])
        except KeyError:
            raise KeyError(f"No ZIP member {name!r}") from None
        with self._lock:
            self.fp.seek(central)
            info = self._read_record()
        if info.filename != name:
            raise IntegrityError("ZIP central directory changed while open")
        info._end_offset = end
        return info

    def namelist(self):
        return list(self.entries)

    def infolist(self):
        raise IntegrityError("Use the compact index; eager ZipInfo lists are intentionally unsupported")


class PacketOverlay:
    """An immutable original ZIP plus a mandatory materialization/deletion ledger."""
    def __init__(self, packet_root, archive_path, *, expected_archive_sha256,
                 hydration_path=None, progress=False):
        self.root = Path(os.path.abspath(packet_root))
        self.archive_path = Path(os.path.abspath(archive_path))
        self.hydration_path = Path(hydration_path or self.root / ".hydrated-source-paths.json")
        self.expected_archive_sha256 = expected_archive_sha256
        self.progress = progress
        self.archive = None
        self.archive_sha256 = None
        self.manifest_sha256 = None
        self.hydration_sha256 = None
        self.hydrated = set()
        self.inventory = {"manifest_files": 0, "real_regular_files": 0, "streamable_absent_files": 0}
        self.archive_sources_verified = 0
        self.archive_source_bytes_verified = 0
        self.outer_entries_verified = 0
        self.runtime_files_verified = 0
        self.reads = {"real_read_calls": 0, "streamed_read_calls": 0,
                      "real_bytes": 0, "streamed_bytes": 0,
                      "real_unique_files": 0, "streamed_unique_files": 0,
                      "streamed_is_file_calls": 0}
        self._marks = bytearray()
        self._active = False

    def _state(self, name):
        """Inspect all real ancestors without following symlinks or virtualizing."""
        current = self.root
        parts = name.split("/")
        for index, part in enumerate(parts):
            current = current / part
            try:
                mode = os.lstat(current).st_mode
            except FileNotFoundError:
                return "absent"
            except NotADirectoryError:
                return "nonregular"
            if stat.S_ISLNK(mode):
                return "symlink" if index == len(parts) - 1 else "symlink ancestor"
            if index < len(parts) - 1:
                if not stat.S_ISDIR(mode):
                    return "nonregular ancestor"
            elif stat.S_ISREG(mode):
                return "regular"
            else:
                return "nonregular"
        raise IntegrityError("Empty source path")

    def _archived_hash(self, name):
        with self.archive.open(name) as stream:
            return _sha_stream(stream)

    def __enter__(self):
        try:
            self._prepare()
        except BaseException:
            if self.archive is not None:
                self.archive.close()
            raise
        return self

    def __exit__(self, *exc):
        if self._active:
            raise IntegrityError("Overlay context was not restored")
        if self.archive is not None:
            self.archive.close()

    def _prepare(self):
        if self.root.is_symlink() or not self.root.is_dir():
            raise IntegrityError("Packet root must be a real directory")
        if not isinstance(self.expected_archive_sha256, str) or not _SHA.fullmatch(self.expected_archive_sha256):
            raise IntegrityError("A trusted original archive SHA-256 is required")
        self._archive_signature = _signature(self.archive_path)
        self.archive_sha256 = _sha_file(self.archive_path)
        if self.archive_sha256 != self.expected_archive_sha256:
            raise IntegrityError("Original archive SHA-256 mismatch")
        self.archive = CompactReadZip(self.archive_path)
        self._marks = bytearray(len(self.archive.entries))
        if _signature(self.archive_path) != self._archive_signature:
            raise IntegrityError("Original archive changed while opening")
        manifest_path = self.root / _MANIFEST
        self._manifest_signature = _signature(manifest_path)
        self.manifest_sha256 = _sha_file(manifest_path)
        if self._archived_hash(_MANIFEST)[0] != self.manifest_sha256:
            raise IntegrityError("Real manifest differs from the immutable archived manifest")
        with open(manifest_path, encoding="utf-8") as stream:
            manifest = json.load(stream)
        encoder = json.JSONEncoder(sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        canonical_hash = hashlib.sha256()
        for chunk in encoder.iterencode(manifest):
            canonical_hash.update(chunk.encode("utf-8"))
        if canonical_hash.hexdigest() != self.manifest_sha256:
            raise IntegrityError("Packet manifest is not canonical JSON")
        if (manifest.get("layout", {}).get("workspace") != "WORK"
                or set(manifest["layout"]["entry_files"]) != {"review.py", "START-HERE.md"}):
            raise IntegrityError("Unsupported packet manifest layout")
        files = manifest["files"]
        if not isinstance(files, dict):
            raise IntegrityError("Invalid manifest source inventory")
        expected_count = len(files) + 3
        if len(self.archive.entries) != expected_count:
            raise IntegrityError("Archive inventory differs from the manifest")
        for name in self.archive.entries:
            if name in {_MANIFEST, "review.py", "START-HERE.md"}:
                continue
            if not name.startswith("WORK/") or name[5:] not in files:
                raise IntegrityError(f"Archive inventory has an unlisted member: {name}")
        self._hydration_signature = _signature(self.hydration_path)
        self.hydration_sha256 = _sha_file(self.hydration_path)
        with open(self.hydration_path, encoding="utf-8") as stream:
            ledger = json.load(stream)
        if not isinstance(ledger, list) or any(not isinstance(name, str) for name in ledger):
            raise IntegrityError("Hydration ledger must be a JSON array of archive-relative paths")
        if len(set(ledger)) != len(ledger):
            raise IntegrityError("Hydration ledger contains duplicate paths")
        for name in ledger:
            _safe_name(name)
            if name not in self.archive.entries:
                raise IntegrityError(f"Hydration ledger contains a nonarchive path: {name}")
        self.hydrated = set(ledger)
        for name, expected in manifest["layout"]["entry_files"].items():
            if not isinstance(expected, str) or not _SHA.fullmatch(expected):
                raise IntegrityError("Invalid entry SHA-256")
            if (self._state(name) != "regular" or _sha_file(self.root / name) != expected
                    or self._archived_hash(name)[0] != expected):
                raise IntegrityError(f"Original entry file changed: {name}")
            self.outer_entries_verified += 1
        self.inventory["manifest_files"] = len(files)
        for relative, expected in files.items():
            _safe_name(relative)
            if not isinstance(expected, str) or not _SHA.fullmatch(expected):
                raise IntegrityError(f"Invalid source SHA-256: {relative}")
            name = "WORK/" + relative
            actual, size = self._archived_hash(name)
            if actual != expected:
                raise IntegrityError(f"archived source SHA-256 mismatch: {name}")
            self.archive_sources_verified += 1
            self.archive_source_bytes_verified += size
            state = self._state(name)
            if state == "regular":
                if name not in self.hydrated:
                    raise IntegrityError(f"Real source is absent from hydration ledger: {name}")
                self.inventory["real_regular_files"] += 1
            elif state == "absent":
                if name in self.hydrated:
                    raise IntegrityError(f"Previously hydrated source is missing: {name}")
                self.inventory["streamable_absent_files"] += 1
            else:
                raise IntegrityError(f"Real source has {state} substitution: {name}")
            if self.progress and self.archive_sources_verified % 20000 == 0:
                print(f"Archive source SHA checks: {self.archive_sources_verified}/{len(files)}", file=sys.stderr)
        # Do not retain a second parsed 19 MiB manifest beside the original tools.
        del files, manifest, ledger
        self.assert_unchanged_inputs(rehash_archive=False)

    def _source_name(self, path):
        raw = os.fspath(path)
        if ".." in Path(raw).parts:
            return None
        absolute = os.path.abspath(raw)
        prefix = str(self.root) + os.sep
        if not absolute.startswith(prefix):
            return None
        name = absolute[len(prefix):]
        if name.startswith("WORK/") and name != _MANIFEST and name in self.archive.entries:
            return name
        return None

    def _eligible(self, name):
        state = self._state(name)
        if state == "symlink ancestor" or state == "nonregular ancestor":
            raise IntegrityError(f"Real source has {state} substitution: {name}")
        if state != "absent":
            # Even an unrecorded file created while running can never later fall back.
            self.hydrated.add(name)
            return False
        return name not in self.hydrated

    def _mark_read(self, name, streamed, size):
        index = _INDEX.unpack(self.archive.entries[name])[2]
        flag = 2 if streamed else 1
        kind = "streamed" if streamed else "real"
        self.reads[kind + "_read_calls"] += 1
        self.reads[kind + "_bytes"] += size
        if not self._marks[index] & flag:
            self._marks[index] |= flag
            self.reads[kind + "_unique_files"] += 1

    @contextmanager
    def activate(self):
        if self.archive is None or self.archive.fp is None or self._active:
            raise IntegrityError("Overlay must be prepared, open, and not nested")
        if Path.is_file is not _ORIGINAL_IS_FILE or Path.read_bytes is not _ORIGINAL_READ_BYTES:
            raise IntegrityError("Path methods were already patched; refusing to stack overlays")
        def is_file(path):
            name = self._source_name(path)
            if name is not None and self._eligible(name):
                self.reads["streamed_is_file_calls"] += 1
                return True
            return _ORIGINAL_IS_FILE(path)
        def read_bytes(path):
            name = self._source_name(path)
            if name is not None and self._eligible(name):
                raw = self.archive.read(name)
                self._mark_read(name, True, len(raw))
                return raw
            raw = _ORIGINAL_READ_BYTES(path)
            if name is not None:
                self._mark_read(name, False, len(raw))
            return raw
        Path.is_file, Path.read_bytes = is_file, read_bytes
        self._active = True
        try:
            yield self
        finally:
            Path.is_file, Path.read_bytes = _ORIGINAL_IS_FILE, _ORIGINAL_READ_BYTES
            self._active = False

    def assert_unchanged_inputs(self, *, rehash_archive=True):
        if _signature(self.archive_path) != self._archive_signature:
            raise IntegrityError("Original archive changed during operation")
        if rehash_archive and _sha_file(self.archive_path) != self.expected_archive_sha256:
            raise IntegrityError("Original archive SHA-256 changed during operation")
        if _signature(self.root / _MANIFEST) != self._manifest_signature:
            raise IntegrityError("Packet manifest changed during operation")
        if _signature(self.hydration_path) != self._hydration_signature:
            raise IntegrityError("hydration ledger changed during operation")
        if _sha_file(self.root / _MANIFEST) != self.manifest_sha256:
            raise IntegrityError("Packet manifest changed during operation")
        if _sha_file(self.hydration_path) != self.hydration_sha256:
            raise IntegrityError("hydration ledger changed during operation")

    def verify_runtime(self):
        """Authenticate all original Python runtime files before importing them."""
        for name in self.archive.entries:
            if name.startswith("WORK/repo/src/") and name.endswith(".py"):
                if (self._state(name) != "regular"
                        or _sha_file(self.root / name) != self._archived_hash(name)[0]):
                    raise IntegrityError(f"Original runtime must be materialized and unchanged: {name}")
                self.runtime_files_verified += 1

    def receipt(self, command, status, return_code):
        return {"schema": "arcpuzzles-zip-packet-overlay-v1", "command": command,
                "status": status, "return_code": return_code,
                "archive": str(self.archive_path), "archive_sha256": self.archive_sha256,
                "expected_archive_sha256": self.expected_archive_sha256,
                "manifest_sha256": self.manifest_sha256,
                "hydration_ledger_sha256": self.hydration_sha256,
                "archive_sources_verified": self.archive_sources_verified,
                "archive_source_bytes_verified": self.archive_source_bytes_verified,
                "outer_entries_verified": self.outer_entries_verified,
                "runtime_files_verified": self.runtime_files_verified,
                "source_inventory": dict(self.inventory), "reads": dict(self.reads),
                "patched_methods": ["Path.is_file", "Path.read_bytes"],
                "is_symlink_patched": False,
                "fallback_scope": "exact manifest members; absent and never materialized",
                "hydration_ledger_requirement": "complete and monotonic across all materializations",
                "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


def run_verify(overlay):
    namespace = runpy.run_path(str(overlay.root / "review.py"), run_name="original_packet_review")
    with overlay.activate():
        code = namespace["main"](["verify"])
    overlay.assert_unchanged_inputs()
    return code


def run_package(overlay, out=None, *, bundle_evidence=False):
    overlay.verify_runtime()
    runtime = overlay.root / "WORK/repo/src"
    sys.path.insert(0, str(runtime))
    # No existing repository bytecode may replace authenticated source.
    no_cache = overlay.root / "WORK/checks/tooling" / f".disabled-bytecode-{os.getpid()}"
    if no_cache.exists():
        raise IntegrityError("Reserved bytecode-disabled path already exists")
    sys.pycache_prefix = str(no_cache)
    module = importlib.import_module("arcpuzzles.review_full_return")
    if Path(module.__file__).resolve() != runtime / "arcpuzzles/review_full_return.py":
        raise IntegrityError("Return builder resolved outside the authenticated runtime")
    with overlay.activate():
        built = module.build_full_return(overlay.root / "WORK", out, bundle_evidence=bundle_evidence)
    overlay.assert_unchanged_inputs()
    # This mandatory final call runs with the real, restored pathlib methods.
    with open(overlay.root / _MANIFEST, encoding="utf-8") as stream:
        manifest = json.load(stream)
    with zipfile.ZipFile(built["zip"]) as archive:
        checked = module.validate_full_return(archive, manifest)
    return built, checked


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("verify", "package"))
    parser.add_argument("--packet-root", type=Path, required=True, help="outer directory containing review.py and WORK/")
    parser.add_argument("--archive", type=Path, required=True, help="immutable original issued ZIP")
    parser.add_argument("--archive-sha256", required=True, help="trusted SHA-256 of the original issued ZIP")
    parser.add_argument("--hydration-ledger", type=Path)
    parser.add_argument("--receipt", type=Path, required=True, help="new JSON receipt path; never overwritten")
    parser.add_argument("--out", type=Path, help="package output; the original builder chooses its default if omitted")
    parser.add_argument("--bundle-evidence", action="store_true")
    parser.add_argument("--progress", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "verify" and (args.out is not None or args.bundle_evidence):
        parser.error("--out and --bundle-evidence apply only to package")
    packet_root = Path(os.path.abspath(args.packet_root))
    receipt_path = Path(os.path.abspath(args.receipt))
    tooling = packet_root / "WORK/checks/tooling"
    if not (receipt_path.parent == packet_root
            or (args.command == "verify" and tooling in receipt_path.parents)):
        parser.error("--receipt must be at packet root, or under WORK/checks/tooling for verify")
    for ancestor in receipt_path.parents:
        if ancestor.is_symlink():
            parser.error("--receipt must not have a symlink ancestor")
        if ancestor == packet_root:
            break
    if receipt_path.exists() or receipt_path.is_symlink():
        parser.error("--receipt must name a new file")
    overlay = PacketOverlay(args.packet_root, args.archive,
                            expected_archive_sha256=args.archive_sha256,
                            hydration_path=args.hydration_ledger, progress=args.progress)
    code, error, package = 2, None, None
    try:
        with overlay:
            if args.command == "verify":
                code = run_verify(overlay)
            else:
                built, checked = run_package(overlay, args.out, bundle_evidence=args.bundle_evidence)
                package = {"zip": built["zip"], "zip_sha256": built["zip_sha256"],
                           "standard_validate_full_return": "passed_after_overlay_removed",
                           "assignment_id": checked["assignment_id"],
                           "patch_paths": checked["patch_paths"]}
                print(built["zip"])
                code = 0
    except (ValueError, OSError, KeyError, zipfile.BadZipFile, RuntimeError) as exc:
        error = f"{type(exc).__name__}: {exc}"
        print(error, file=sys.stderr)
    receipt = overlay.receipt(args.command, "passed" if code == 0 else "rejected", code)
    if error is not None:
        receipt["error"] = error
    if package is not None:
        receipt["package"] = package
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    with open(receipt_path, "x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(f"Overlay receipt: {receipt_path}", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
