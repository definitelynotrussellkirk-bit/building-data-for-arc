#!/usr/bin/env python3
"""Opt-in, stdlib-only adapter for an inode-constrained reviewer checkout.

Use the ordinary package_return.py with a complete extraction. For an explicitly
sparse checkout, first record the issued files actually extracted, before editing,
in WORK/.review/materialized-files.json:
  {"schema":"arcpuzzles-sparse-materialization-v1",
   "packet_manifest_sha256":"<SHA256 of issued PACKET-MANIFEST.json>",
   "paths":["repo/...", ...]}
Missing recorded files and every missing selected baseline are errors. Only never
materialized files may come from the original ZIP. This command does not create
reports, change completion status, draw tickets, or execute a puzzle generator.

Example (from WORK/repo):
  python3 generators/34569d6118b3/workspace/tools/package_sparse_return.py \
    --original-zip /path/to/issued.zip --work-root .. --out /path/to/return.zip

The original ZIP is checked in full against its canonical manifest, which must
equal the local manifest and assignment packet ID. The original builder and all
its arcpuzzles imports execute from those verified bytes. A read-only path view
supplies original bytes plus actual local edits; build_full_return and its full
validator run unchanged. The normal packager and shared source are untouched.
The view intentionally implements only the Path operations used by this issued
builder: a future incompatible builder fails closed instead of guessing.

Run this CLI in its own process. Memory use includes the compressed ZIP and all
uncompressed issued files; no full extraction or third-party package is needed.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import importlib.abc
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import zipfile


SCHEMA = "arcpuzzles-sparse-materialization-v1"
CACHE_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
ROOT_DOCUMENTS = ("ASSIGNMENT.json", "AUDIT_ASSIGNMENT.json", "BLIND_ASSIGNMENT.json",
                  "REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md",
                  "FEEDBACK_TO_CODEX.md", "AUDIT.md", "RESULTS.json")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def safe_name(name: str) -> str:
    if (not isinstance(name, str) or not name or "\\" in name or ":" in name
            or "\0" in name or name.startswith("/")
            or any(p in {"", ".", ".."} for p in name.split("/"))):
        raise ValueError(f"Unsafe packet path: {name!r}")
    return name


def read_issued(path: Path) -> tuple[dict, dict[str, bytes], str]:
    """Check every member before any issued Python is imported."""
    archive_bytes = path.read_bytes()
    files: dict[str, bytes] = {}
    seen: set[str] = set()
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        for item in archive.infolist():
            name = safe_name(item.filename.rstrip("/") if item.is_dir() else item.filename)
            if item.orig_filename != item.filename or name.casefold() in seen:
                raise ValueError(f"Duplicate or truncated ZIP member: {item.orig_filename!r}")
            seen.add(name.casefold())
            mode = item.external_attr >> 16
            kind = stat.S_IFMT(mode)
            if (kind not in {0, stat.S_IFREG, stat.S_IFDIR} or item.flag_bits & 1
                    or item.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
                    or (not item.is_dir() and (mode & 0o111 or kind == stat.S_IFDIR))
                    or (item.is_dir() and kind == stat.S_IFREG)):
                raise ValueError(f"Unsafe ZIP member type: {name}")
            if not item.is_dir():
                files[name] = archive.read(item)  # CRC is verified here.
    folded_files = {name.casefold() for name in files}
    for name in files:
        if any(parent.as_posix().casefold() in folded_files for parent in PurePosixPath(name).parents
               if parent.as_posix() != "."):
            raise ValueError(f"ZIP file/directory collision: {name}")
    raw = files.get("WORK/PACKET-MANIFEST.json")
    if raw is None:
        raise ValueError("Original ZIP has no WORK/PACKET-MANIFEST.json")
    manifest = json.loads(raw)
    if (manifest.get("schema") != "arcpuzzles-full-packet-v2"
            or canonical(manifest) != raw or not isinstance(manifest.get("files"), dict)):
        raise ValueError("Original packet manifest is not canonical or has wrong schema")
    issued = {"PACKET-MANIFEST.json": raw}
    for name, digest in manifest["files"].items():
        safe_name(name)
        value = files.get("WORK/" + name)
        if (not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
                or value is None or sha(value) != digest):
            raise ValueError(f"Original manifest hash mismatch or missing member: {name}")
        issued[name] = value
    extra = {n[5:] for n in files if n.startswith("WORK/")} - set(issued)
    if extra:
        raise ValueError(f"Undeclared original WORK files: {sorted(extra)}")
    return manifest, issued, sha(archive_bytes)


def regular_bytes(root: Path, relative: str) -> tuple[bytes, int]:
    """Read a local regular file without traversing symlink parents."""
    target = root
    for part in PurePosixPath(safe_name(relative)).parts:
        target = target / part
        if target.is_symlink():
            raise ValueError(f"Symlink in local packet: {relative}")
    mode = target.stat().st_mode
    if not stat.S_ISREG(mode):
        raise ValueError(f"Nonregular local packet file: {relative}")
    return target.read_bytes(), mode


class PacketView:
    """Read-only Path protocol over a verified, complete byte snapshot."""

    def __init__(self, files: dict[str, bytes], modes: dict[str, int],
                 name: str = "", directories: set[str] | None = None):
        self.files, self.modes, self.name = files, modes, name
        if directories is None:
            directories = {""}
            for filename in files:
                for parent in PurePosixPath(filename).parents:
                    if str(parent) != ".":
                        directories.add(str(parent))
            if set(files) & directories:
                raise ValueError("Local file/directory collision")
        self.directories = directories

    def __truediv__(self, other: str) -> PacketView:
        # The issued builder appends a trailing slash to its generator home.
        other = safe_name(str(other).rstrip("/"))
        return PacketView(self.files, self.modes,
                          f"{self.name}/{other}" if self.name else other, self.directories)

    def __str__(self) -> str:
        return "/verified-packet/WORK" + ("/" + self.name if self.name else "")

    def resolve(self) -> PacketView:
        return self

    @property
    def suffix(self) -> str:
        return PurePosixPath(self.name).suffix

    def relative_to(self, other: PacketView) -> PurePosixPath:
        if self.files is not other.files:
            raise ValueError("Different virtual packet roots")
        return PurePosixPath(self.name).relative_to(PurePosixPath(other.name))

    def is_file(self) -> bool:
        return self.name in self.files

    def is_symlink(self) -> bool:
        return False  # All original/local symlinks were rejected before construction.

    def exists(self) -> bool:
        return self.is_file() or self.name in self.directories

    def stat(self) -> os.stat_result:
        if not self.exists():
            raise FileNotFoundError(str(self))
        mode = (self.modes.get(self.name, stat.S_IFREG | 0o644)
                if self.is_file() else stat.S_IFDIR | 0o755)
        return os.stat_result((mode, 0, 0, 1, 0, 0,
                               len(self.files[self.name]) if self.is_file() else 0, 0, 0, 0))

    def read_bytes(self) -> bytes:
        if not self.is_file():
            raise FileNotFoundError(str(self))
        return self.files[self.name]

    def read_text(self, encoding: str = "utf-8", errors: str = "strict") -> str:
        with io.TextIOWrapper(io.BytesIO(self.read_bytes()), encoding=encoding, errors=errors) as stream:
            return stream.read()

    def rglob(self, pattern: str):
        if pattern != "*":
            raise ValueError(f"Unsupported issued-builder glob: {pattern!r}")
        prefix = self.name + "/" if self.name else ""
        for name in sorted(set(self.files) | self.directories):
            if name.startswith(prefix) and name != self.name:
                yield PacketView(self.files, self.modes, name, self.directories)


def snapshot(root: Path, manifest: dict, issued: dict[str, bytes]) -> tuple[PacketView, dict]:
    if root.is_symlink():
        raise ValueError("Symlink work root")
    root = root.resolve(strict=True)
    raw, _ = regular_bytes(root, "PACKET-MANIFEST.json")
    if raw != issued["PACKET-MANIFEST.json"]:
        raise ValueError("Local manifest differs from original ZIP")
    contract = json.loads(regular_bytes(root, "ASSIGNMENT.json")[0])
    if contract.get("packet_id") != sha(raw):
        raise ValueError("Assignment packet ID mismatch")
    baseline = contract.get("baseline_sha256")
    if not isinstance(baseline, dict) or not baseline:
        raise ValueError("Missing selected baseline contract")
    inventory = json.loads(regular_bytes(root, ".review/materialized-files.json")[0])
    paths = inventory.get("paths")
    if (inventory.get("schema") != SCHEMA or inventory.get("packet_manifest_sha256") != sha(raw)
            or not isinstance(paths, list) or not all(isinstance(p, str) for p in paths)
            or len(set(paths)) != len(paths) or not set(paths) <= set(manifest["files"])):
        raise ValueError("Invalid materialized-files inventory")
    files, modes = dict(issued), {}

    def overlay(name: str) -> None:
        value, mode = regular_bytes(root, name)
        if (name in manifest["files"] and name not in baseline
                and sha(value) != manifest["files"][name]):
            raise ValueError(f"Changed shared packet source: {name}")
        files[name], modes[name] = value, mode

    for name in sorted(set(paths) | set(baseline)):
        try:
            overlay(name)
        except FileNotFoundError as exc:
            raise ValueError(f"Missing materialized or selected source: {name}") from exc
    for name, digest in baseline.items():
        if manifest["files"].get(name) != digest:
            raise ValueError(f"Selected baseline differs from original manifest: {name}")
        frozen = ".review/baseline/" + safe_name(name)
        try:
            value, mode = regular_bytes(root, frozen)
        except FileNotFoundError as exc:
            raise ValueError(f"Missing frozen baseline: {name}") from exc
        if sha(value) != digest:
            raise ValueError(f"Frozen baseline changed: {name}")
        files[frozen], modes[frozen] = value, mode

    for prefix in ("repo", "checks", "solve", "solve-blind", ".review/solve-private",
                   ".review/solve-private-blind"):
        folder = root / prefix
        if folder.is_symlink():
            raise ValueError(f"Symlink in local packet: {prefix}")
        if not folder.exists():
            continue
        def walk_error(error):
            raise error

        for directory, subdirs, filenames in os.walk(folder, followlinks=False, onerror=walk_error):
            for name in subdirs:
                if (Path(directory) / name).is_symlink():
                    raise ValueError(f"Symlink in local packet: {Path(directory) / name}")
            if prefix == "repo":
                subdirs[:] = [name for name in subdirs if name not in CACHE_PARTS]
            for name in filenames:
                path = Path(directory) / name
                if prefix != "repo" or path.suffix not in {".pyc", ".pyo"}:
                    overlay(path.relative_to(root).as_posix())
    for name in ROOT_DOCUMENTS:
        if (root / name).exists() or (root / name).is_symlink():
            overlay(name)
    return PacketView(files, modes), contract


class IssuedImports(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Execute arcpuzzles modules only from already hash-verified archive bytes."""

    def __init__(self, issued: dict[str, bytes]):
        self.issued = issued

    def find_spec(self, fullname, path=None, target=None):
        if fullname != "arcpuzzles" and not fullname.startswith("arcpuzzles."):
            return None
        stem = "repo/src/" + fullname.replace(".", "/")
        for relative, package in ((stem + "/__init__.py", True), (stem + ".py", False)):
            if relative in self.issued:
                spec = importlib.util.spec_from_loader(fullname, self, is_package=package)
                spec.origin = "/verified-issued/" + relative
                spec.loader_state = relative
                return spec
        raise ImportError(f"Missing verified issued module: {fullname}")

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        relative = module.__spec__.loader_state
        module.__file__ = module.__spec__.origin
        exec(compile(self.issued[relative], module.__file__, "exec"), module.__dict__)


@contextmanager
def issued_imports(issued: dict[str, bytes]):
    existing = {name for name in sys.modules if name == "arcpuzzles" or name.startswith("arcpuzzles.")}
    if existing:
        raise RuntimeError("Use a fresh process: arcpuzzles modules are already imported")
    importer = IssuedImports(issued)
    sys.meta_path.insert(0, importer)
    try:
        yield
    finally:
        sys.meta_path.remove(importer)
        for name in list(sys.modules):
            if name == "arcpuzzles" or name.startswith("arcpuzzles."):
                del sys.modules[name]


def package(original_zip: Path, work_root: Path, out: Path,
            *, bundle_evidence: bool = False) -> dict:
    """Invoke the issued builder; failures never become successful receipts."""
    out = out.absolute()
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    manifest, issued, archive_sha = read_issued(original_zip)
    view, contract = snapshot(work_root, manifest, issued)
    with issued_imports(issued):
        from arcpuzzles.review_full_return import build_full_return, validate_full_return
        result = build_full_return(view, out, bundle_evidence=bundle_evidence)
        # Independently reopen the actual on-disk ZIP with the same issued validator.
        try:
            with zipfile.ZipFile(out) as archive:
                validate_full_return(archive, manifest)
        except Exception:
            out.unlink()
            raise
    result["sparse_packaging"] = {
        "original_zip_sha256": archive_sha,
        "packet_manifest_sha256": contract["packet_id"],
        "verified_original_files": len(manifest["files"]),
        "builder_sha256": manifest["files"]["repo/src/arcpuzzles/review_full_return.py"],
        "method": "verified-original-bytes-plus-local-overlay; unchanged-issued-builder-and-validator",
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--original-zip", required=True, type=Path)
    parser.add_argument("--work-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--bundle-evidence", action="store_true")
    args = parser.parse_args()
    result = package(args.original_zip, args.work_root, args.out,
                     bundle_evidence=args.bundle_evidence)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
