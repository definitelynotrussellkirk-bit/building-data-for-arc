#!/usr/bin/env python3
"""Package a compact workspace with the unchanged official ARCpuzzles builder.

Only physically absent, manifest-listed, immutable repo files can be read from
the original ZIP. Selected sources, all contract baseline paths, assignments,
reports, evidence, and output remain real files. No global Path monkeypatch is
used. The official builder still hashes every source it checks.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path, PosixPath, PurePosixPath
import stat
import sys
import zipfile

sys.dont_write_bytecode = True
CHUNK = 1024 * 1024


def canonical_json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def stream_sha(stream):
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(CHUNK), b""):
        digest.update(chunk)
    return digest.hexdigest()


def no_symlinks(path, stop=None):
    """Check real paths, including ancestors; never consult the archive view."""
    path = Path(str(path))
    for part in (path, *path.parents):
        if part == stop:
            break
        if part.is_symlink():
            raise ValueError(f"Symlink path or ancestor: {part}")


def safe_member(name):
    if (not isinstance(name, str) or not name or "\\" in name or ":" in name
            or "\0" in name or PurePosixPath(name).is_absolute()
            or ".." in PurePosixPath(name).parts
            or str(PurePosixPath(name)) != name.rstrip("/")):
        raise ValueError(f"Unsafe archive member: {name!r}")


class ArchiveBackedWorkspace:
    """Context-owned read view; callers must finish using root before closing."""

    def __init__(self, work, source_zip):
        self.work = Path(work).absolute()
        self.source_zip = Path(source_zip).absolute()
        no_symlinks(self.work)
        no_symlinks(self.source_zip)
        self.work = self.work.resolve()
        self.source_zip = self.source_zip.resolve()
        self.fallback_reads = set()
        self.archive = None
        self.stream = self.source_zip.open("rb")
        self.source_stat = os.fstat(self.stream.fileno())
        try:
            self.source_sha256 = stream_sha(self.stream)
            self.stream.seek(0)
            self.archive = zipfile.ZipFile(self.stream)
            self._verify_archive()
            contract_path = self.work / "ASSIGNMENT.json"
            no_symlinks(contract_path, self.work)
            self.contract_bytes = contract_path.read_bytes()
            self.contract = json.loads(self.contract_bytes)
            if (self.contract.get("schema") != "arcpuzzles-full-assignment-v2"
                    or self.contract.get("packet_id") != self.packet_id):
                raise ValueError("Assignment packet identity differs from original archive")
            task = self.contract["task_id"]
            if self.contract.get("generator") != self.manifest["generators"].get(task):
                raise ValueError("Assignment generator differs from original manifest")
            protected = set(self.contract["baseline_sha256"])
            for name, digest in self.contract["baseline_sha256"].items():
                if self.manifest["files"].get(name) != digest:
                    raise ValueError(f"Assignment baseline differs from manifest: {name}")
            protected.add("repo/shared/data/canonical/puzzles.jsonl")
            home = f"repo/generators/{task}/"
            self.immutable = {
                name: digest for name, digest in self.manifest["files"].items()
                if name.startswith("repo/") and name not in protected and not name.startswith(home)
            }
            self.root = self._path_class()(str(self.work))
            self.assert_stable()
        except BaseException:
            self.close()
            raise

    def _verify_archive(self):
        files, seen = {}, set()
        for info in self.archive.infolist():
            safe_member(info.filename)
            key = info.filename.rstrip("/")
            if key in seen:
                raise ValueError(f"Duplicate archive member: {info.filename}")
            seen.add(key)
            kind = stat.S_IFMT(info.external_attr >> 16)
            if kind not in {0, stat.S_IFREG, stat.S_IFDIR} or info.flag_bits & 1:
                raise ValueError(f"Unsafe archive member type: {info.filename}")
            if not info.is_dir():
                if kind == stat.S_IFDIR:
                    raise ValueError(f"Nonregular archive member: {info.filename}")
                files[info.filename] = info
        self.manifest_bytes = self.archive.read("WORK/PACKET-MANIFEST.json")
        self.manifest = json.loads(self.manifest_bytes)
        if (canonical_json(self.manifest) != self.manifest_bytes
                or self.manifest.get("schema") != "arcpuzzles-full-packet-v2"
                or self.manifest.get("layout", {}).get("workspace") != "WORK"):
            raise ValueError("Original manifest is not a canonical WORK-layout packet")
        no_symlinks(self.work / "PACKET-MANIFEST.json", self.work)
        if (self.work / "PACKET-MANIFEST.json").read_bytes() != self.manifest_bytes:
            raise ValueError("Working manifest differs from original archive")
        entries = self.manifest["layout"]["entry_files"]
        if set(entries) != {"START-HERE.md", "review.py"}:
            raise ValueError("Invalid original outer entry inventory")
        self.packet_id = hashlib.sha256(self.manifest_bytes).hexdigest()
        expected = {"WORK/" + name: digest for name, digest in self.manifest["files"].items()}
        expected.update(entries)
        expected["WORK/PACKET-MANIFEST.json"] = self.packet_id
        for name in expected:
            safe_member(name)
        if set(files) != set(expected):
            raise ValueError("Original archive inventory differs from packet manifest")
        for name, digest in expected.items():
            with self.archive.open(files[name]) as stream:
                if stream_sha(stream) != digest:
                    raise ValueError(f"Original manifest mismatch: {name}")
        for name, digest in entries.items():
            path = self.work.parent / name
            no_symlinks(path)
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError(f"Changed or missing outer entry: {name}")
        self.verified_members = len(expected)
        self.verified_bytes = sum(info.file_size for info in files.values())

    def _relative(self, path):
        try:
            return Path(str(path)).relative_to(self.work).as_posix()
        except ValueError:
            return None

    def _fallback(self, path):
        relative = self._relative(path)
        if relative not in self.immutable:
            return None
        real = Path(str(path))
        no_symlinks(real, self.work)
        try:
            real.lstat()
        except FileNotFoundError:
            return relative
        return None  # Existing files, directories, and other objects stay real.

    def _path_class(self):
        view = self

        class ArchiveBackedPath(PosixPath):
            def is_file(self, **kwargs):
                if view._fallback(self) is not None:
                    return True
                return super().is_file(**kwargs)

            def read_bytes(self):
                no_symlinks(Path(str(self)), view.work)
                relative = view._fallback(self)
                if relative is None:
                    return Path(str(self)).read_bytes()
                raw = view.archive.read("WORK/" + relative)
                if hashlib.sha256(raw).hexdigest() != view.immutable[relative]:
                    raise ValueError(f"Original manifest mismatch: {relative}")
                view.fallback_reads.add(relative)
                return raw

            def open(self, mode="r", *args, **kwargs):
                if view._relative(self) in view.immutable and any(c in mode for c in "wax+"):
                    raise PermissionError(f"Immutable archive source view is read-only: {self}")
                return super().open(mode, *args, **kwargs)

        return ArchiveBackedPath

    def source_report(self):
        return {
            "schema": "arcpuzzles-archive-source-verification-v1",
            "status": "all_original_members_verified",
            "source_zip_sha256": self.source_sha256, "packet_id": self.packet_id,
            "workspace_files": len(self.manifest["files"]),
            "outer_entry_files": len(self.manifest["layout"]["entry_files"]),
            "verified_members_including_manifest": self.verified_members,
            "verified_expanded_bytes": self.verified_bytes,
            "verification": "Every original ZIP member streamed through SHA-256; no extraction required.",
            "fallback_policy": "Only absent immutable manifest repo files; selected tree and baseline paths stay real.",
        }

    def assert_stable(self):
        no_symlinks(self.source_zip)
        current = self.source_zip.stat()
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        opened = os.fstat(self.stream.fileno())
        if any(getattr(item, field) != getattr(self.source_stat, field)
               for item in (current, opened) for field in fields):
            raise ValueError("Original archive changed during packaging")
        if (self.work / "PACKET-MANIFEST.json").read_bytes() != self.manifest_bytes:
            raise ValueError("Working manifest changed during packaging")
        if (self.work / "ASSIGNMENT.json").read_bytes() != self.contract_bytes:
            raise ValueError("Assignment changed during packaging")

    def close(self):
        if self.archive is not None:
            self.archive.close()
        self.stream.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def official_builder(view):
    """Verify actual generic Python sources before importing the official code."""
    for relative, digest in view.manifest["files"].items():
        if relative.startswith("repo/src/arcpuzzles/") and relative.endswith(".py"):
            path = view.work / relative
            no_symlinks(path, view.work)
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError(f"Changed or missing official Python source: {relative}")
    sys.path.insert(0, str(view.work / "repo/src"))
    module = importlib.import_module("arcpuzzles.review_full_return")
    for name, loaded in tuple(sys.modules.items()):
        if name == "arcpuzzles" or name.startswith("arcpuzzles."):
            origin = getattr(loaded, "__file__", None)
            if origin and not Path(origin).resolve().is_relative_to(view.work / "repo/src/arcpuzzles"):
                raise ValueError(f"Official import came from a different workspace: {name}")
    return module.build_full_return


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--verification-report", type=Path,
                        help="New JSON source-verification report written BEFORE packaging; may be under checks/.")
    parser.add_argument("--bundle-evidence", action="store_true")
    args = parser.parse_args(argv)
    no_symlinks(args.out.absolute())
    if args.out.exists():
        raise FileExistsError(args.out)
    with ArchiveBackedWorkspace(args.work, args.source_zip) as view:
        target = None
        if args.verification_report is not None:
            candidate = args.verification_report.absolute()
            no_symlinks(candidate)
            target = candidate.resolve()
            if not target.is_relative_to(view.work / "checks"):
                raise ValueError("Source verification report must be a new file under WORK/checks/")
        builder = official_builder(view)
        report = view.source_report()
        report.update(
            wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            official_builder_sha256=view.manifest["files"]["repo/src/arcpuzzles/review_full_return.py"],
            official_builder_modified=False,
            packaging_status="not_yet_run_when_this_source_receipt_was_written",
        )
        if target is not None:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(report, sort_keys=True, indent=2) + "\n")
        result = builder(view.root, args.out, bundle_evidence=args.bundle_evidence)
        view.assert_stable()
        fallbacks = {path: view.immutable[path] for path in sorted(view.fallback_reads)}
        summary = {key: result[key] for key in ("zip", "zip_sha256", "packet_id", "assignment_id", "task_id")}
        summary.update(
            status="official_return_built_and_validated", source_verification=report,
            archive_backed_source_count=len(fallbacks),
            archive_backed_path_hash_inventory_sha256=hashlib.sha256(canonical_json(fallbacks)).hexdigest(),
        )
        print(json.dumps(summary, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as error:
        print(f"Archive-backed packaging failed: {error}", file=sys.stderr)
        raise SystemExit(2)
