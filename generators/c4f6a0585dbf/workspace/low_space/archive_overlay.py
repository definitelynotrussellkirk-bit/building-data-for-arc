"""Read omitted immutable packet files from an authenticated original archive.

This is archive-backed validation, not a full extracted-runtime replay.  Only
explicitly recorded sparse-extraction omissions are eligible.  Selected-task and
baseline files must be real.  Use around the unmodified build_full_return call
in one thread, with no concurrent filesystem or pathlib monkeypatch mutations.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import threading
import zipfile


class ArchiveOverlayError(ValueError):
    """The original archive or its sparse-extraction contract is invalid."""


_LOCK = threading.Lock()
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _path(name):
    if (not isinstance(name, str) or not name or "\\" in name or "\0" in name
            or PurePosixPath(name).is_absolute() or PureWindowsPath(name).drive
            or any(p in {"", ".", ".."} for p in name.split("/"))):
        raise ArchiveOverlayError(f"Unsafe archive/manifest path: {name!r}")
    return name


def _object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ArchiveOverlayError(f"Duplicate JSON key: {key!r}")
        out[key] = value
    return out


def _identity(st):
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)


class _ReadOnlyBytes(io.BytesIO):
    def writable(self):
        return False

    def write(self, *args):
        raise io.UnsupportedOperation("write")

    def writelines(self, *args):
        raise io.UnsupportedOperation("write")

    def truncate(self, *args):
        raise io.UnsupportedOperation("truncate")

    def getbuffer(self):
        return memoryview(self.getvalue())


class ArchiveOverlay:
    """Temporarily provide Path reads for declared absent immutable repo files.

    expected_zip_sha256 must come from the independently recorded original ZIP.
    omitted_paths must be recorded at sparse extraction, before review edits.
    The context object is single-use. Path.stat, glob/rglob, builtins.open, and imports stay physical. All write
    modes stay physical, and revoke virtual fallback for that path.  Existing
    objects and symlinked/non-directory ancestors never receive fallback.
    """

    def __init__(self, work_root, archive_path, *, expected_zip_sha256, omitted_paths):
        self.root = Path(work_root).resolve(strict=True)
        self.archive_path = Path(archive_path)
        self.expected_hash = expected_zip_sha256
        self.omissions = list(omitted_paths)
        self._fp = self._zip = None
        self._originals = None
        self._virtual = set()
        self._verified = set()
        self._reads = 0
        self._owner = None
        self._used = False

    def _physical_state(self, rel):
        """Return absent/present/unsafe without ever following a symlink."""
        target = self.root / rel
        current = Path(target.anchor)
        for index, part in enumerate(target.parts[1:]):
            current /= part
            try:
                st = os.lstat(current)
            except FileNotFoundError:
                # A missing ancestor above WORK means the extraction disappeared.
                return "absent" if current.is_relative_to(self.root) and current != self.root else "unsafe"
            except OSError:
                return "unsafe"
            if stat.S_ISLNK(st.st_mode):
                return "unsafe"
            if current == self.root and (st.st_dev, st.st_ino) != self._root_identity:
                return "unsafe"
            if index < len(target.parts) - 2 and not stat.S_ISDIR(st.st_mode):
                return "unsafe"
        return "present"

    def _relative(self, path):
        if threading.get_ident() != self._owner or ".." in path.parts:
            return None
        try:
            rel = path.absolute().relative_to(self.root).as_posix()
        except ValueError:
            return None
        return rel if rel in self._virtual else None

    def _eligible(self, path):
        rel = self._relative(path)
        if rel is not None and self._physical_state(rel) != "absent":
            self._virtual.discard(rel)
            return None
        return rel

    def _unchanged_archive(self):
        if _identity(os.fstat(self._fp.fileno())) != self._archive_identity:
            raise ArchiveOverlayError("Archive changed during overlay validation")

    def _read(self, name):
        self._unchanged_archive()
        try:
            raw = self._zip.read(self._members[name])
        except (OSError, RuntimeError, ValueError, zipfile.BadZipFile, EOFError) as exc:
            raise ArchiveOverlayError(f"Cannot read ZIP member: {name}") from exc
        self._unchanged_archive()
        return raw

    def _open(self, path, mode="r", buffering=-1, encoding=None, errors=None, newline=None):
        old_open = self._originals["open"]
        # Delegate all mutations, invalid modes and noneligible paths unchanged.
        if mode not in {"r", "rt", "tr", "rb", "br"}:
            if isinstance(mode, str) and any(c in mode for c in "wax+"):
                rel = self._relative(path)
                if rel is not None:
                    self._virtual.discard(rel)
            return old_open(path, mode, buffering, encoding, errors, newline)
        rel = self._eligible(path)
        if rel is None:
            return old_open(path, mode, buffering, encoding, errors, newline)
        if not isinstance(buffering, int):
            raise TypeError("buffering must be an integer")
        binary = "b" in mode
        if binary and any(value is not None for value in (encoding, errors, newline)):
            raise ValueError("binary mode does not take encoding, errors, or newline")
        if not binary and buffering == 0:
            raise ValueError("can't have unbuffered text I/O")
        raw = self._read("WORK/" + rel)
        if _sha(raw) != self._files[rel]:
            raise ArchiveOverlayError(f"Manifest SHA-256 mismatch: {rel}")
        self._verified.add(rel)
        self._reads += 1
        stream = _ReadOnlyBytes(raw)
        stream.name, stream.mode = os.fspath(path), "rb"
        return stream if binary else io.TextIOWrapper(stream, encoding=io.text_encoding(encoding),
                                                      errors=errors, newline=newline)

    def _setup(self):
        if not isinstance(self.expected_hash, str) or not _SHA256.fullmatch(self.expected_hash):
            raise ArchiveOverlayError("An independently recorded ZIP SHA-256 is required")
        root_stat = os.lstat(self.root)
        if not stat.S_ISDIR(root_stat.st_mode):
            raise ArchiveOverlayError("WORK root must be an actual directory")
        self._root_identity = (root_stat.st_dev, root_stat.st_ino)
        if not stat.S_ISREG(os.lstat(self.archive_path).st_mode):
            raise ArchiveOverlayError("Original ZIP must be an actual regular file")
        self._fp = self.archive_path.open("rb")
        self._archive_identity = _identity(os.fstat(self._fp.fileno()))
        digest = hashlib.file_digest(self._fp, "sha256").hexdigest()
        self._unchanged_archive()
        if digest != self.expected_hash:
            raise ArchiveOverlayError("Original ZIP SHA-256 mismatch")
        self._fp.seek(0)
        self._zip = zipfile.ZipFile(self._fp)
        self._members = {}
        normalized = {}
        for info in self._zip.infolist():
            name = info.filename
            clean = _path(name[:-1] if info.is_dir() else name)
            mode = stat.S_IFMT(info.external_attr >> 16)
            expected_type = stat.S_IFDIR if info.is_dir() else stat.S_IFREG
            if name != info.orig_filename or clean in normalized:
                raise ArchiveOverlayError(f"Duplicate or ambiguous ZIP member: {name!r}")
            if (mode and mode != expected_type) or info.flag_bits & 1:
                raise ArchiveOverlayError(f"Nonregular or encrypted ZIP member: {name!r}")
            normalized[clean] = info
            self._members[name] = info
        for name in normalized:
            for parent in PurePosixPath(name).parents:
                ancestor = normalized.get(str(parent))
                if ancestor is not None and not ancestor.is_dir():
                    raise ArchiveOverlayError(f"ZIP file used as directory: {parent}")
        manifest_member = "WORK/PACKET-MANIFEST.json"
        if manifest_member not in self._members:
            raise ArchiveOverlayError("Original ZIP has no packet manifest")
        manifest_raw = self._read(manifest_member)
        if self._physical_state("PACKET-MANIFEST.json") != "present":
            raise ArchiveOverlayError("Local packet manifest must be an actual file")
        if (self.root / "PACKET-MANIFEST.json").read_bytes() != manifest_raw:
            raise ArchiveOverlayError("Local packet manifest differs from original archive")
        self._manifest_hash = _sha(manifest_raw)
        manifest = json.loads(manifest_raw, object_pairs_hook=_object)
        self._files = manifest.get("files")
        if manifest.get("schema") != "arcpuzzles-full-packet-v2" or not isinstance(self._files, dict):
            raise ArchiveOverlayError("Invalid full packet manifest")
        for name, digest in self._files.items():
            _path(name)
            if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
                raise ArchiveOverlayError(f"Invalid manifest digest: {name}")
            info = self._members.get("WORK/" + name)
            if info is None or info.is_dir():
                raise ArchiveOverlayError(f"Manifest file missing in ZIP: {name}")
        if self._physical_state("ASSIGNMENT.json") != "present":
            raise ArchiveOverlayError("Assignment must be an actual file")
        contract = json.loads((self.root / "ASSIGNMENT.json").read_bytes(), object_pairs_hook=_object)
        tid, baselines = contract.get("task_id"), contract.get("baseline_sha256")
        if not isinstance(tid, str) or not re.fullmatch(r"[A-Za-z0-9_]+", tid) or not isinstance(baselines, dict):
            raise ArchiveOverlayError("Cannot identify selected task and baselines")
        if len(self.omissions) != len(set(self.omissions)):
            raise ArchiveOverlayError("Duplicate omission path")
        for name in self.omissions:
            _path(name)
            if not name.startswith("repo/") or name not in self._files:
                raise ArchiveOverlayError(f"Omission is not a manifest repository file: {name}")
            if name in baselines or name.startswith(f"repo/generators/{tid}/"):
                raise ArchiveOverlayError(f"Selected or baseline source cannot be virtual: {name}")
            if self._physical_state(name) == "absent":
                self._virtual.add(name)
        self._initial_count = len(self._virtual)

    def __enter__(self):
        if self._used:
            raise RuntimeError("An ArchiveOverlay object is single-use")
        if not _LOCK.acquire(blocking=False):
            raise RuntimeError("An archive overlay is already active")
        self._used = True
        try:
            self._setup()
            self._owner = threading.get_ident()
            self._originals = {name: getattr(Path, name) for name in ("open", "exists", "is_file")}
            overlay = self

            def path_open(path, *args, **kwargs):
                return overlay._open(path, *args, **kwargs)

            def path_exists(path, *args, **kwargs):
                if not args and not kwargs and overlay._eligible(path) is not None:
                    return True
                return overlay._originals["exists"](path, *args, **kwargs)

            def path_is_file(path, *args, **kwargs):
                if not args and not kwargs and overlay._eligible(path) is not None:
                    return True
                return overlay._originals["is_file"](path, *args, **kwargs)

            Path.open, Path.exists, Path.is_file = path_open, path_exists, path_is_file
            return self
        except BaseException:
            try:
                self._close()
            finally:
                _LOCK.release()
            raise

    def _close(self):
        if self._originals is not None:
            for name, method in self._originals.items():
                setattr(Path, name, method)
            self._originals = None
        if self._zip is not None:
            self._zip.close()
        if self._fp is not None:
            self._fp.close()

    def __exit__(self, *exc):
        try:
            self._close()
        finally:
            _LOCK.release()

    def report(self, *, include_paths=False):
        paths = sorted(self._verified)
        result = {"schema": "arcpuzzles-archive-overlay-v1",
                "scope": "archive-backed validation of explicitly omitted immutable sources; not full extracted-runtime replay",
                "archive_sha256": self.expected_hash,
                "manifest_sha256": self._manifest_hash,
                "declared_omissions": len(self.omissions),
                "declared_omission_paths_sha256": _sha(json.dumps(sorted(self.omissions), separators=(",", ":")).encode()),
                "initially_virtual_paths": self._initial_count,
                "verified_virtual_path_count": len(paths),
                "verified_virtual_paths_sha256": _sha(json.dumps(paths, separators=(",", ":")).encode()),
                "virtual_reads": self._reads}
        if include_paths:
            result["verified_virtual_paths"] = paths
        return result
