"""Manifest-bound packing of check evidence for returns that exceed the ZIP member limit.

All `checks/` files go into one deterministic tar.gz with a per-file path/size/SHA-256
manifest. The bundle's expanded bytes count against the same expanded-size limit as
ordinary members, and validation reads it as data: only regular files under checks/,
listed exactly once, with matching sizes and hashes. Nothing in it is executed.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import tarfile

ARCHIVE = "EVIDENCE-BUNDLE.tar.gz"
MANIFEST = "EVIDENCE-BUNDLE.json"
SCHEMA = "arcpuzzles-evidence-bundle-v1"
MAX_BUNDLED_FILES = 4096
PREFIX = "checks/"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _safe_path(name: str) -> bool:
    path = PurePosixPath(name)
    return (name.startswith(PREFIX) and not path.is_absolute() and ".." not in path.parts
            and "\\" not in name and "\0" not in name and path.as_posix() == name and len(path.parts) >= 2
            and len(name.encode("utf-8")) <= 4096)


def pack(files: dict[str, bytes]) -> dict[str, bytes]:
    """Return {ARCHIVE: bytes, MANIFEST: bytes} for the given checks/ files."""
    if not files:
        raise ValueError("No check evidence to bundle")
    if len(files) > MAX_BUNDLED_FILES:
        raise ValueError(f"Evidence bundle holds at most {MAX_BUNDLED_FILES} files; got {len(files)}")
    for name in files:
        if not _safe_path(name):
            raise ValueError(f"Only checks/ evidence can be bundled: {name}")
    tar_bytes = io.BytesIO()
    with tarfile.open(fileobj=tar_bytes, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for name in sorted(files):
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = len(files[name]), 0o644, 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            archive.addfile(info, io.BytesIO(files[name]))
    compressed = io.BytesIO()
    with gzip.GzipFile(fileobj=compressed, mode="wb", mtime=0) as handle:
        handle.write(tar_bytes.getvalue())
    archive_bytes = compressed.getvalue()
    manifest = {"schema": SCHEMA, "archive": ARCHIVE, "archive_sha256": _sha(archive_bytes),
                "count": len(files), "expanded_bytes": sum(len(raw) for raw in files.values()),
                "files": [{"path": name, "bytes": len(files[name]), "sha256": _sha(files[name])}
                          for name in sorted(files)]}
    return {ARCHIVE: archive_bytes, MANIFEST: (json.dumps(manifest, sort_keys=True, indent=1) + "\n").encode()}


def read_manifest(raw: bytes) -> dict:
    manifest = json.loads(raw)
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if (not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA or manifest.get("archive") != ARCHIVE
            or not isinstance(files, list) or not files or len(files) > MAX_BUNDLED_FILES
            or manifest.get("count") != len(files)):
        raise ValueError("Invalid evidence bundle manifest")
    seen = set()
    for row in files:
        if (not isinstance(row, dict) or not isinstance(row.get("path"), str) or not _safe_path(row["path"])
                or row["path"].casefold() in seen or type(row.get("bytes")) is not int or row["bytes"] < 0
                or not isinstance(row.get("sha256"), str) or len(row["sha256"]) != 64):
            raise ValueError("Invalid or repeated evidence bundle entry")
        seen.add(row["path"].casefold())
    for name in seen:
        if any(parent.as_posix().casefold() in seen for parent in PurePosixPath(name).parents):
            raise ValueError("Evidence bundle has conflicting file and directory paths")
    if type(manifest.get("expanded_bytes")) is not int or manifest["expanded_bytes"] != sum(row["bytes"] for row in files):
        raise ValueError("Evidence bundle expanded size differs from its entries")
    return manifest



def check_budget(manifest: dict, entries=()) -> None:
    """Bound nested file bytes, including all ordinary outer ZIP members, before reading tar data."""
    from .review_return import check_zip_budget
    check_zip_budget([*entries, (ARCHIVE, manifest["expanded_bytes"])])


class _BoundedTarReader:
    """Stop gzip expansion even when malformed tar/PAX headers request a huge read."""
    def __init__(self, source, limit: int):
        self.source, self.remaining = source, limit

    def read(self, size=-1):
        wanted = self.remaining + 1 if size < 0 else min(size, self.remaining + 1)
        raw = self.source.read(wanted)
        if len(raw) > self.remaining:
            raise ValueError("Evidence tar decompression exceeds its bounded storage budget")
        self.remaining -= len(raw)
        return raw


def _open_directory(parent_fd: int, name: str) -> int:
    try:
        os.mkdir(name, mode=0o755, dir_fd=parent_fd)
    except FileExistsError:
        pass
    try:
        return os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
    except OSError as exc:
        raise ValueError(f"Symlink or non-directory in evidence extraction path: {name}") from exc


def _write_verified(root: Path, files: dict[str, bytes]) -> None:
    # Directory descriptors anchor every component; no resolved-path cache can be
    # retargeted through a symlink between validation and the write.
    root = Path(os.path.abspath(root))
    root_fd = os.open(root.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for name in root.parts[1:]:
            child_fd = _open_directory(root_fd, name)
            os.close(root_fd)
            root_fd = child_fd
        for name, raw in files.items():
            parent_fd = os.dup(root_fd)
            try:
                parts = PurePosixPath(name).parts
                for component in parts[:-1]:
                    child_fd = _open_directory(parent_fd, component)
                    os.close(parent_fd)
                    parent_fd = child_fd
                try:
                    fd = os.open(parts[-1], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                 0o644, dir_fd=parent_fd)
                except OSError as exc:
                    raise ValueError(f"Refusing to overwrite or follow bundled evidence path: {name}") from exc
                with os.fdopen(fd, "wb") as handle:
                    handle.write(raw)
            finally:
                os.close(parent_fd)
    finally:
        os.close(root_fd)

def verify(archive_bytes: bytes, manifest: dict, *, extract_to: Path | None = None,
           retain: set[str] | None = None) -> dict[str, bytes] | None:
    """Check every member against the manifest; optionally extract the verified bytes."""
    manifest = read_manifest(json.dumps(manifest).encode())
    check_budget(manifest)
    if _sha(archive_bytes) != manifest["archive_sha256"]:
        raise ValueError("Evidence bundle archive hash differs from its manifest")
    expected = {row["path"]: row for row in manifest["files"]}
    seen: set[str] = set()
    out: dict[str, bytes] = {}
    budget = manifest["expanded_bytes"]
    # Includes file data, bounded PAX/name headers, member padding and end padding.
    storage_limit = manifest["expanded_bytes"] + sum(2560 + len(row["path"].encode("utf-8"))
                                                    for row in manifest["files"]) + 10240
    with gzip.GzipFile(fileobj=io.BytesIO(archive_bytes), mode="rb") as compressed, \
            tarfile.open(fileobj=_BoundedTarReader(compressed, storage_limit), mode="r|") as archive:
        for info in archive:
            row = expected.get(info.name)
            if row is None or info.name in seen:
                raise ValueError(f"Unlisted or repeated evidence bundle member: {info.name!r}")
            if not info.isreg() or info.size != row["bytes"]:
                raise ValueError(f"Evidence bundle member is not the listed regular file: {info.name}")
            budget -= info.size
            if budget < 0:
                raise ValueError("Evidence bundle expands beyond its declared size")
            handle = archive.extractfile(info)
            raw = handle.read(info.size + 1) if handle else b""
            if len(raw) != row["bytes"] or _sha(raw) != row["sha256"]:
                raise ValueError(f"Evidence bundle member hash differs: {info.name}")
            seen.add(info.name)
            if extract_to is not None or retain is not None and info.name in retain:
                out[info.name] = raw
    if seen != set(expected):
        raise ValueError(f"Evidence bundle is missing listed files: {sorted(set(expected) - seen)[:5]}")
    if extract_to is not None:
        _write_verified(extract_to, out)
        return out
    if retain is not None:
        if not retain <= seen:
            raise ValueError("Selected evidence member missing from bundle")
        return out
    return None


def extract_from_return(zip_path: Path, out: Path) -> dict:
    """Verify a return's bundle against its manifest, then write the files under out/."""
    import zipfile
    from .review_return import scan_zip
    with zipfile.ZipFile(zip_path) as archive:
        infos = scan_zip(archive)
        names = {info.filename for info in infos}
        if not {ARCHIVE, MANIFEST} <= names:
            raise ValueError("Return has no evidence bundle")
        manifest = read_manifest(archive.read(MANIFEST))
        check_budget(manifest, [(info.filename, info.file_size) for info in infos if info.filename != ARCHIVE])
        if out.is_symlink():
            raise ValueError(f"Symlink evidence extraction directory: {out}")
        if out.exists() and any(out.iterdir()):
            raise FileExistsError(f"Extraction directory must be new or empty: {out}")
        verify(archive.read(ARCHIVE), manifest, extract_to=out)
    return {"out": str(out), "count": manifest["count"], "expanded_bytes": manifest["expanded_bytes"],
            "archive_sha256": manifest["archive_sha256"]}
