#!/usr/bin/env python3
"""Optional archive-backed input view for the unchanged stock return builder.

The real selected sources, frozen baselines, assignment and evidence remain
mandatory. Only absent, untouched repository files are supplied from the ZIP.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.abc
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import zipfile

from packet_zip import CHUNK_BYTES, Packet, PacketError, inspect_directory, open_directory, safe_name, unique_object


BUILDER_PATH = "repo/src/arcpuzzles/review_full_return.py"
SUPPORTED_BUILDER_SHA256 = "a021d00ec056acbdf0958955f5d08f110bff934375a6dac397fc3f86089a2f74"


def _regular_file(path, *, stream_hash=False):
    """Read a real regular file without following a symlink at any component."""
    inspect_directory(path.parent)
    parent = open_directory(path.parent)
    try:
        # O_NONBLOCK avoids hanging on a malicious FIFO before fstat can reject it.
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    finally:
        os.close(parent)
    with os.fdopen(descriptor, "rb") as source:
        if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
            raise PacketError(f"expected a regular file: {path}")
        if not stream_hash:
            return source.read()
        digest = hashlib.sha256()
        while chunk := source.read(CHUNK_BYTES):
            digest.update(chunk)
        return digest.hexdigest()


class _ArchiveLoader(importlib.abc.Loader):
    def __init__(self, owner, member, package):
        self.owner, self.member, self.package = owner, member, package

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        output = io.BytesIO()
        self.owner.packet.stream(self.member, output)
        raw = output.getvalue()
        origin = f"{self.owner.packet.archive.filename}!/{self.member}"
        module.__file__ = origin
        if self.package:
            module.__path__ = [origin.rpartition("/")[0]]
        self.owner.loaded_sources[self.member] = hashlib.sha256(raw).hexdigest()
        exec(compile(raw, origin, "exec"), module.__dict__)


class StockModules(importlib.abc.MetaPathFinder):
    """Import exact, hash-checked stock Python sources without disk extraction.

This context must begin with a clean arcpuzzles module namespace. It does not
patch source, functions or validators, and removes only its own modules on exit.
"""
    def __init__(self, packet):
        self.packet = packet
        self.prefix = "WORK/" if packet.workspace == "WORK" else ""
        self.loaded_sources = {}

    def find_spec(self, fullname, path=None, target=None):
        if fullname != "arcpuzzles" and not fullname.startswith("arcpuzzles."):
            return None
        stem = self.prefix + "repo/src/" + fullname.replace(".", "/")
        for member, package in ((stem + "/__init__.py", True), (stem + ".py", False)):
            if member in self.packet.expected:
                loader = _ArchiveLoader(self, member, package)
                return importlib.util.spec_from_loader(fullname, loader, is_package=package)
        raise ModuleNotFoundError(f"stock package module absent from verified ZIP: {fullname}")

    def __enter__(self):
        builder = self.prefix + BUILDER_PATH
        if self.packet.expected.get(builder) != SUPPORTED_BUILDER_SHA256:
            raise PacketError("unsupported stock builder SHA-256; review this adapter for the new version")
        if any(name == "arcpuzzles" or name.startswith("arcpuzzles.") for name in sys.modules):
            raise PacketError("stock imports require a clean arcpuzzles namespace; run this tool as a separate process")
        sys.meta_path.insert(0, self)
        try:
            return importlib.import_module("arcpuzzles.review_full_return")
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, kind, value, traceback):
        if self in sys.meta_path:
            sys.meta_path.remove(self)
        for name, module in list(sys.modules.items()):
            loader = getattr(module, "__loader__", None)
            if isinstance(loader, _ArchiveLoader) and loader.owner is self:
                del sys.modules[name]


class Projection:
    """A read-only overlay with explicit paths that must remain physical."""
    def __init__(self, packet, root, contract):
        self.packet = packet
        self.root = root
        self.contract = contract
        self.home = f"repo/generators/{contract['task_id']}/"
        self.baseline = set(contract["baseline_sha256"])
        self.prefix = "WORK/" if packet.workspace == "WORK" else ""
        self.virtual_files = {name for name in packet.manifest["files"]
            if name.startswith("repo/") and not name.startswith(self.home)
            and name not in self.baseline
            and name != "repo/shared/data/canonical/puzzles.jsonl"}
        self.virtual_directories = set()
        for name in self.virtual_files:
            parts = name.split("/")
            self.virtual_directories.update("/".join(parts[:n]) for n in range(1, len(parts)))

    def path(self, relative="."):
        return ProjectedPath(self, relative)

    def disk_status(self, relative):
        current = self.root
        parts = PurePosixPath(relative).parts
        if not parts:
            return current.lstat()
        for index, part in enumerate(parts):
            current /= part
            try:
                status = current.lstat()
            except FileNotFoundError:
                return None
            if index < len(parts) - 1:
                if stat.S_ISLNK(status.st_mode):
                    raise PacketError(f"symlink source ancestor: {current}")
                if not stat.S_ISDIR(status.st_mode):
                    raise PacketError(f"non-directory source ancestor: {current}")
        return status

    def audit_present_originals(self, stock):
        checked = 0
        for name, expected in self.packet.manifest["files"].items():
            status = self.disk_status(name)
            if status is None:
                continue
            if stat.S_ISLNK(status.st_mode):
                raise PacketError(f"symlink present original source: {name}")
            if not stat.S_ISREG(status.st_mode):
                raise PacketError(f"present original source is not a regular file: {name}")
            if not stock._allowed(name, self.contract):
                if _regular_file(self.root / name, stream_hash=True) != expected:
                    raise PacketError(f"Changed unauthorized present source: {name}")
                checked += 1
        if self.packet.workspace == "WORK":
            for name, expected in self.packet.manifest["layout"]["entry_files"].items():
                path = self.root.parent / name
                if os.path.lexists(path):
                    if path.is_symlink():
                        raise PacketError(f"symlink original entry file: {name}")
                    if _regular_file(path, stream_hash=True) != expected:
                        raise PacketError(f"Changed original entry file: {name}")
                    checked += 1
        return checked


class ProjectedPath:
    """The small read-only Path interface used by the pinned stock builder."""
    def __init__(self, projection, relative="."):
        self.projection = projection
        self.relative = PurePosixPath(relative)
        if self.relative.as_posix() != ".":
            safe_name(self.relative.as_posix())

    @property
    def key(self):
        return self.relative.as_posix()

    @property
    def local(self):
        return self.projection.root / self.relative

    @property
    def suffix(self):
        return self.relative.suffix

    @property
    def name(self):
        return self.relative.name

    @property
    def parent(self):
        return ProjectedPath(self.projection, self.relative.parent)

    def __truediv__(self, value):
        safe_name(str(value))
        return ProjectedPath(self.projection, self.relative / str(value))

    def __str__(self):
        return str(self.local)

    def resolve(self):
        # The projection root is already absolute and its ancestors were checked.
        return self

    def relative_to(self, other):
        if not isinstance(other, ProjectedPath) or other.projection is not self.projection:
            raise ValueError("relative_to requires paths from the same projection")
        return self.relative.relative_to(other.relative)

    def as_posix(self):
        return self.local.as_posix()

    def is_symlink(self):
        status = self.projection.disk_status(self.key)
        return status is not None and stat.S_ISLNK(status.st_mode)

    def is_file(self):
        status = self.projection.disk_status(self.key)
        if status is not None:
            return stat.S_ISREG(status.st_mode)
        return self.key in self.projection.virtual_files

    def is_dir(self):
        status = self.projection.disk_status(self.key)
        if status is not None:
            return stat.S_ISDIR(status.st_mode)
        return self.key in self.projection.virtual_directories

    def exists(self):
        return (self.projection.disk_status(self.key) is not None
                or self.key in self.projection.virtual_files
                or self.key in self.projection.virtual_directories)

    def stat(self):
        status = self.projection.disk_status(self.key)
        if status is not None:
            return status
        if self.key in self.projection.virtual_files:
            info = self.projection.packet.files[self.projection.prefix + self.key]
            return os.stat_result((info.external_attr >> 16, 0, 0, 1, 0, 0, info.file_size, 0, 0, 0))
        raise FileNotFoundError(str(self))

    def read_bytes(self):
        status = self.projection.disk_status(self.key)
        if status is not None:
            if stat.S_ISLNK(status.st_mode):
                raise PacketError(f"symlink read is forbidden: {self}")
            return _regular_file(self.local)
        if self.key not in self.projection.virtual_files:
            raise FileNotFoundError(str(self))
        output = io.BytesIO()
        self.projection.packet.stream(self.projection.prefix + self.key, output)
        return output.getvalue()

    def read_text(self, encoding=None, errors=None):
        return self.read_bytes().decode(encoding or "utf-8", errors or "strict")

    def rglob(self, pattern):
        if pattern != "*":
            raise PacketError("unsupported stock glob; adapter only permits rglob('*')")
        keys = set()
        status = self.projection.disk_status(self.key)
        if status is not None:
            if stat.S_ISLNK(status.st_mode):
                raise PacketError(f"symlink directory is forbidden: {self}")
            if not stat.S_ISDIR(status.st_mode):
                return
            for directory, directories, files in os.walk(self.local, followlinks=False):
                for name in (*directories, *files):
                    relative = (Path(directory) / name).relative_to(self.projection.root).as_posix()
                    safe_name(relative)
                    keys.add(relative)
        prefix = "" if self.key == "." else self.key + "/"
        keys.update(name for name in self.projection.virtual_files if name.startswith(prefix))
        keys.update(name for name in self.projection.virtual_directories if name.startswith(prefix))
        for name in sorted(keys):
            yield self.projection.path(name)


def build_archive_backed_return(archive_path, packet_root, output, *, bundle_evidence=False):
    root = Path(os.path.abspath(packet_root))
    inspect_directory(root)
    if not root.is_dir():
        raise PacketError("packet workspace must already exist")
    with zipfile.ZipFile(archive_path) as archive:
        packet = Packet(archive)
        # Mandatory on every invocation; no cached or user-asserted substitute.
        archive_integrity = packet.verify()
        if _regular_file(root / "PACKET-MANIFEST.json") != packet.manifest_bytes:
            raise PacketError("on-disk manifest differs byte-for-byte from immutable archive")
        contract = json.loads(_regular_file(root / "ASSIGNMENT.json"), object_pairs_hook=unique_object)
        if not isinstance(contract, dict) or contract.get("task_id") not in packet.manifest.get("main_ids", []):
            raise PacketError("assignment task is outside the original eligible IDs")
        tid = contract["task_id"]
        safe_name(tid)
        if "/" in tid or contract.get("generator") != packet.manifest["generators"][tid]:
            raise PacketError("assignment generator differs from immutable archive")
        baseline = contract.get("baseline_sha256")
        if not isinstance(baseline, dict):
            raise PacketError("assignment baseline must be a hash mapping")
        for name, expected in baseline.items():
            safe_name(name)
            if packet.manifest["files"].get(name) != expected:
                raise PacketError(f"assignment baseline differs from immutable archive: {name}")
        projection = Projection(packet, root, contract)
        imports = StockModules(packet)
        with imports as stock:
            # Sources being executed are hash-checked ZIP bytes, never local edits.
            checked = projection.audit_present_originals(stock)
            fallback_count = sum(projection.disk_status(name) is None for name in projection.virtual_files)
            result = stock.build_full_return(projection.path(), Path(output), bundle_evidence=bundle_evidence)
        return {"schema": "arc-archive-backed-return-v1", "archive_integrity": archive_integrity,
                "projection": {"full_tree_verified": False, "archive_fallback_file_count": fallback_count,
                               "present_original_files_checked": checked,
                               "physical_selected_and_baseline_required": True},
                "stock_builder": {"path": BUILDER_PATH, "sha256": SUPPORTED_BUILDER_SHA256,
                                  "verified_imported_module_count": len(imports.loaded_sources)},
                "return": result}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="immutable original review ZIP")
    parser.add_argument("workspace", type=Path, help="physical workspace containing PACKET-MANIFEST.json")
    parser.add_argument("--output", type=Path, required=True, help="new return ZIP path")
    parser.add_argument("--bundle-evidence", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        report = build_archive_backed_return(arguments.archive, arguments.workspace,
                                             arguments.output, bundle_evidence=arguments.bundle_evidence)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except (PacketError, OSError, ValueError, RuntimeError, ImportError, AttributeError, TypeError,
            zipfile.BadZipFile, zipfile.LargeZipFile) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("ERROR: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
