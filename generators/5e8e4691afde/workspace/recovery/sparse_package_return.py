#!/usr/bin/env python3
"""Package a sparse ARC review using the packet's unchanged official guards.

The original archive supplies only files never materialized. MATERIALIZED.json
is an explicit extraction inventory, not a cache to regenerate from disk.
No archive member is extracted and no shared source is modified.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import importlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import uuid
import zipfile


INVENTORY_SCHEMA = "arc-review-materialization-v1"
MANIFEST = "WORK/PACKET-MANIFEST.json"
MODULE_ROOT = "WORK/repo/src/arcpuzzles/"
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stream_sha(stream) -> str:
    digest = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(block)
    return digest.hexdigest()


def _json(raw: bytes, label: str) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key in {label}: {key}")
            result[key] = value
        return result
    result = json.loads(raw, object_pairs_hook=unique)
    if not isinstance(result, dict):
        raise ValueError(f"Expected JSON object: {label}")
    return result


def _relative(name: str, label: str) -> str:
    if (not isinstance(name, str) or not name or "\\" in name
            or ":" in name or "\0" in name or name.startswith("/")
            or any(part in {"", ".", ".."} for part in name.split("/"))
            or PurePosixPath(name).as_posix() != name):
        raise ValueError(f"Unsafe {label} path: {name!r}")
    return name


def _read_regular(path: Path) -> bytes:
    mode = path.lstat().st_mode
    if stat.S_ISLNK(mode):
        raise ValueError(f"Symlink file: {path}")
    if not stat.S_ISREG(mode):
        raise ValueError(f"Nonregular file: {path}")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError(f"Nonregular file: {path}")
        return stream.read()


class SparsePacket:
    """Read-only union of verified original members and actual working files."""

    def __init__(self, archive_path: Path, root: Path, inventory_path: Path):
        if root.is_symlink():
            raise ValueError(f"Symlink packet root: {root}")
        self.root = root.resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError(f"Packet root is not a directory: {self.root}")
        self.archive_path = archive_path.resolve(strict=True)
        self.inventory_path = inventory_path.absolute()
        self.inventory_raw = _read_regular(self.inventory_path)
        inventory = _json(self.inventory_raw, "materialization inventory")
        if inventory.get("schema") != INVENTORY_SCHEMA:
            raise ValueError("Unsupported materialization inventory schema")
        digest = inventory.get("archive_sha256")
        if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
            raise ValueError("Invalid inventory archive_sha256")
        entries = inventory.get("entries")
        if not isinstance(entries, list):
            raise ValueError("Inventory entries must be a list")
        self.materialized = {_relative(name, "inventory") for name in entries}
        if len(self.materialized) != len(entries):
            raise ValueError("Repeated materialization inventory path")
        self._stream = self.archive_path.open("rb")
        self.archive = None
        try:
            if _stream_sha(self._stream) != digest:
                raise ValueError("Archive SHA-256 mismatch against materialization inventory")
            self.archive_sha256 = digest
            self._stream.seek(0)
            self.archive = zipfile.ZipFile(self._stream)
            self._verify_archive()
            self._verify_disk()
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.archive is not None:
            self.archive.close()
        self._stream.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _verify_archive(self):
        self.infos = {}
        self.directories = {""}
        seen = set()
        for info in self.archive.infolist():
            name = _relative(info.filename.rstrip("/"), "archive")
            if name.casefold() in seen:
                raise ValueError(f"Archive member collision: {name}")
            seen.add(name.casefold())
            mode = (info.external_attr >> 16) & 0xffff
            kind = stat.S_IFMT(mode)
            if kind not in {0, stat.S_IFREG, stat.S_IFDIR} or mode & 0o111:
                raise ValueError(f"Unsafe archive member type or executable: {name}")
            if info.flag_bits & 1 or info.compress_type not in {
                    zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
                raise ValueError(f"Unsupported archive member: {name}")
            if info.is_dir():
                if kind not in {0, stat.S_IFDIR}:
                    raise ValueError(f"Unsafe archive directory: {name}")
                self.directories.add(name)
            else:
                if kind == stat.S_IFDIR:
                    raise ValueError(f"Unsafe archive file: {name}")
                self.infos[name] = info
            self.directories.update(parent.as_posix()
                                    for parent in PurePosixPath(name).parents
                                    if parent.as_posix() != ".")
        if set(self.infos) & self.directories:
            raise ValueError("Archive file/directory collision")
        if MANIFEST not in self.infos:
            raise ValueError("Original archive has no WORK/PACKET-MANIFEST.json")
        self.manifest_raw = self.archive.read(MANIFEST)
        self.manifest = _json(self.manifest_raw, "original packet manifest")
        canonical = json.dumps(self.manifest, sort_keys=True, ensure_ascii=False,
                               separators=(",", ":")).encode("utf-8")
        if canonical != self.manifest_raw:
            raise ValueError("Original packet manifest is not canonical JSON")
        files = self.manifest.get("files")
        if not isinstance(files, dict):
            raise ValueError("Original packet manifest has no files mapping")
        layout = self.manifest.get("layout")
        if not isinstance(layout, dict) or layout.get("workspace") != "WORK":
            raise ValueError("Packet layout.workspace must be WORK")
        entry_files = layout.get("entry_files")
        if not isinstance(entry_files, dict) or set(entry_files) != {"START-HERE.md", "review.py"}:
            raise ValueError("Packet layout.entry_files must contain exactly START-HERE.md and review.py")
        for name, digest in list(files.items()) + list(entry_files.items()):
            _relative(name, "manifest")
            if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
                raise ValueError(f"Invalid manifest digest: {name}")
        expected = {*entry_files, MANIFEST}
        expected.update("WORK/" + name for name in files)
        if set(self.infos) != expected:
            missing = sorted(expected - set(self.infos))
            extra = sorted(set(self.infos) - expected)
            raise ValueError(f"Archive/manifest file set differs: missing={missing[:5]}, extra={extra[:5]}")
        self.original_sha256 = {}
        for name, info in self.infos.items():
            with self.archive.open(info) as stream:
                digest = _stream_sha(stream)  # Also verifies decompression and CRC.
            expected_digest = files.get(name[5:]) if name.startswith("WORK/") else entry_files[name]
            if expected_digest is not None and expected_digest != digest:
                raise ValueError(f"Manifest hash mismatch: {name}")
            self.original_sha256[name] = digest
        unknown = self.materialized - set(self.infos)
        if unknown:
            raise ValueError(f"Inventory path is not an original archive file: {sorted(unknown)[0]}")

    def _scan_disk(self, prefix: str = "") -> dict[str, os.stat_result]:
        nodes = {}
        start = self.root / prefix
        start_stat = self._local_stat(prefix)
        if start_stat is None:
            return nodes
        if not stat.S_ISDIR(start_stat.st_mode):
            return nodes
        stack = [(start, prefix)]
        while stack:
            directory, relative = stack.pop()
            with os.scandir(directory) as children:
                for child in children:
                    name = relative + "/" + child.name if relative else child.name
                    _relative(name, "working")
                    item = child.stat(follow_symlinks=False)
                    if stat.S_ISLNK(item.st_mode):
                        raise ValueError(f"Symlink working path: {name}")
                    if not (stat.S_ISREG(item.st_mode) or stat.S_ISDIR(item.st_mode)):
                        raise ValueError(f"Nonregular working path: {name}")
                    nodes[name] = item
                    if stat.S_ISDIR(item.st_mode):
                        stack.append((Path(child.path), name))
        return nodes

    def _local_stat(self, name: str):
        current = self.root
        parts = PurePosixPath(name).parts if name else ()
        for index, part in enumerate(parts):
            current = current / part
            try:
                item = current.lstat()
            except FileNotFoundError:
                if name in self.materialized:
                    raise ValueError(f"Materialized file missing: {name}") from None
                return None
            if stat.S_ISLNK(item.st_mode):
                raise ValueError(f"Symlink working path: {current}")
            if index + 1 < len(parts) and not stat.S_ISDIR(item.st_mode):
                raise ValueError(f"Non-directory working ancestor: {current}")
        if not parts:
            item = self.root.lstat()
        if not (stat.S_ISREG(item.st_mode) or stat.S_ISDIR(item.st_mode)):
            raise ValueError(f"Nonregular working path: {current}")
        return item

    def _verify_disk(self):
        nodes = self._scan_disk()
        for name in sorted(self.materialized):
            item = nodes.get(name)
            if item is None:
                raise ValueError(f"Materialized file missing: {name}")
            if not stat.S_ISREG(item.st_mode):
                raise ValueError(f"Materialized path is not a regular file: {name}")
        for name in set(nodes) & set(self.infos):
            if name not in self.materialized:
                raise ValueError(f"Archive file on disk is absent from materialization inventory: {name}")
        # Baseline/default launchers and instructions are immutable. Repository
        # source changes are checked by the original builder's own task guards.
        for name in sorted(self.materialized):
            if name.startswith("WORK/repo/"):
                continue
            raw = _read_regular(self.root / name)
            if name == MANIFEST and raw != self.manifest_raw:
                raise ValueError("Packet manifest differs from original archive")
            if _sha(raw) != self.original_sha256[name]:
                raise ValueError(f"Changed immutable packet file: {name}")

    def require_materialized_baselines(self):
        """Archive defaults must not supply mutable assignment source paths."""
        contract_path = self.root / "WORK/ASSIGNMENT.json"
        contract = _json(_read_regular(contract_path), "assignment")
        baselines = contract.get("baseline_sha256")
        if not isinstance(baselines, dict):
            raise ValueError("Assignment has no baseline_sha256 mapping")
        for path in baselines:
            name = "WORK/" + _relative(path, "assignment baseline")
            if name not in self.materialized:
                raise ValueError(f"Assignment baseline source must be materialized and inventoried: {name}")
        return contract

    def read_archive(self, name: str) -> bytes:
        raw = self.archive.read(name)
        if _sha(raw) != self.original_sha256[name]:
            raise ValueError(f"Original archive member changed during packaging: {name}")
        return raw

    def path(self, name: str = ""):
        return SparsePath(self, name)


class SparsePath:
    """The read-only Path operations exercised by build_full_return.

    No __fspath__ or write methods are supplied: consumers cannot accidentally
    turn a virtual path into an unchecked native filesystem access.
    """

    def __init__(self, packet: SparsePacket, name: str):
        self.packet = packet
        self.name = _relative(name, "overlay") if name else ""

    def __str__(self):
        return str(self.packet.root / self.name)

    def __truediv__(self, other):
        # pathlib accepts a directory operand with a trailing slash; the
        # official builder deliberately constructs its selected home this way.
        part = _relative(str(other).rstrip("/"), "overlay")
        return SparsePath(self.packet, self.name + "/" + part if self.name else part)

    def resolve(self, strict=False):
        if strict and not self.exists():
            raise FileNotFoundError(str(self))
        return self

    def relative_to(self, other):
        if not isinstance(other, SparsePath) or other.packet is not self.packet:
            raise ValueError("Cannot relativize paths from different sparse packets")
        return PurePosixPath(self.name).relative_to(PurePosixPath(other.name))

    @property
    def suffix(self):
        return PurePosixPath(self.name).suffix

    def _stat(self):
        local = self.packet._local_stat(self.name)
        if local is not None:
            if self.name in self.packet.infos and self.name not in self.packet.materialized:
                raise ValueError(f"Archive file on disk is absent from materialization inventory: {self.name}")
            return local
        if self.name in self.packet.infos:
            info = self.packet.infos[self.name]
            mode = (info.external_attr >> 16) & 0xffff
            mode = (mode & 0o777) | stat.S_IFREG
            return os.stat_result((mode, 0, 0, 1, 0, 0, info.file_size, 0, 0, 0))
        if self.name in self.packet.directories:
            return os.stat_result((stat.S_IFDIR | 0o755, 0, 0, 1, 0, 0, 0, 0, 0, 0))
        return None

    def exists(self):
        return self._stat() is not None

    def is_file(self):
        item = self._stat()
        return item is not None and stat.S_ISREG(item.st_mode)

    def is_symlink(self):
        # _local_stat rejects links, including links in ancestor directories.
        self.packet._local_stat(self.name)
        return False

    def stat(self):
        item = self._stat()
        if item is None:
            raise FileNotFoundError(str(self))
        return item

    def read_bytes(self):
        local = self.packet._local_stat(self.name)
        if local is not None:
            if not stat.S_ISREG(local.st_mode):
                raise IsADirectoryError(str(self))
            if self.name in self.packet.infos and self.name not in self.packet.materialized:
                raise ValueError(f"Archive file on disk is absent from materialization inventory: {self.name}")
            return _read_regular(self.packet.root / self.name)
        if self.name not in self.packet.infos:
            raise FileNotFoundError(str(self))
        return self.packet.read_archive(self.name)

    def read_text(self, encoding=None, errors=None):
        return self.read_bytes().decode(encoding or "utf-8", errors or "strict")

    def rglob(self, pattern):
        if pattern != "*":
            raise NotImplementedError("SparsePath only supports the builder's rglob('*')")
        local = self.packet._local_stat(self.name)
        if local is not None and not stat.S_ISDIR(local.st_mode):
            return
        prefix = self.name + "/" if self.name else ""
        names = {name for name in self.packet.infos if name.startswith(prefix)}
        names.update(name for name in self.packet.directories if name.startswith(prefix))
        names.update(self.packet._scan_disk(self.name))
        names.discard(self.name)
        for name in sorted(names):
            yield SparsePath(self.packet, name)


class _OfficialModules(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Load the unchanged original modules under an isolated package name."""

    def __init__(self, packet: SparsePacket):
        self.packet = packet
        self.prefix = "_arc_sparse_official_" + uuid.uuid4().hex

    def _source(self, fullname):
        if fullname == self.prefix:
            stem = MODULE_ROOT.rstrip("/")
        elif fullname.startswith(self.prefix + "."):
            stem = MODULE_ROOT + fullname[len(self.prefix) + 1:].replace(".", "/")
        else:
            return None
        if stem + "/__init__.py" in self.packet.infos:
            return stem + "/__init__.py", True
        if stem + ".py" in self.packet.infos:
            return stem + ".py", False
        return None

    def find_spec(self, fullname, path=None, target=None):
        source = self._source(fullname)
        if source is None:
            return None
        return importlib.util.spec_from_loader(fullname, self, is_package=source[1])

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        name, is_package = self._source(module.__name__)
        raw = self.packet.read_archive(name)
        module.__file__ = str(self.packet.archive_path) + "!/" + name
        if is_package:
            module.__path__ = [module.__file__.rsplit("/", 1)[0]]
        exec(compile(raw, module.__file__, "exec"), module.__dict__)


@contextmanager
def _official_modules(packet):
    loader = _OfficialModules(packet)
    sys.meta_path.insert(0, loader)
    try:
        module = importlib.import_module(loader.prefix + ".review_full_return")
        draw = importlib.import_module(loader.prefix + ".review_full_draw")
        draw.load_manifest(packet.path("WORK"))  # Official schema/canonical check.
        yield module
    finally:
        sys.meta_path.remove(loader)
        for name in list(sys.modules):
            if name == loader.prefix or name.startswith(loader.prefix + "."):
                del sys.modules[name]


def build_sparse_return(archive: Path, root: Path, inventory: Path, out: Path,
                        *, bundle_evidence: bool = False) -> dict:
    """Run both original full-return functions without changing their guards."""
    out = out.absolute()
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    root = root.absolute()
    if out.resolve().is_relative_to((root / "WORK/repo").resolve()):
        raise ValueError("Return output must be outside WORK/repo")
    with SparsePacket(archive, root, inventory) as packet:
        packet.require_materialized_baselines()
        with _official_modules(packet) as official:
            result = official.build_full_return(packet.path("WORK"), out,
                                                bundle_evidence=bundle_evidence)
            try:
                with zipfile.ZipFile(out) as returned:
                    checked = official.validate_full_return(returned, packet.manifest)
                if _read_regular(packet.inventory_path) != packet.inventory_raw:
                    raise ValueError("Materialization inventory changed during packaging")
                packet._verify_disk()
            except BaseException:
                out.unlink()
                raise
            # The original return and its original validation must agree.
            if any(result.get(key) != value for key, value in checked.items()):
                out.unlink()
                raise ValueError("Original builder/validator result disagreement")
            return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True,
                        help="Original full packet ZIP, never a reviewer return")
    parser.add_argument("--root", type=Path, required=True,
                        help="Sparse extraction directory containing WORK/")
    parser.add_argument("--inventory", type=Path,
                        help="Extraction inventory (default: ROOT/MATERIALIZED.json)")
    parser.add_argument("--out", type=Path, required=True,
                        help="New return ZIP path outside WORK/repo")
    parser.add_argument("--bundle-evidence", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = build_sparse_return(args.archive, args.root,
            args.inventory or args.root / "MATERIALIZED.json", args.out,
            bundle_evidence=args.bundle_evidence)
    except (ValueError, OSError, zipfile.BadZipFile, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
