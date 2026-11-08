#!/usr/bin/env python3
"""Extract a review ZIP with SHA-verified hardlinks for immutable sources.

Standard library only. File bodies use a 1 MiB buffer; zipfile metadata and the
JSON manifest remain O(member count). Hardlinks share storage, so named editable
tasks and shared/data are always copied. With no --editable-task, all generator
trees are protected. Use detach before editing any additional task.

This tool never executes extracted code, changes the source ZIP, rewrites the
manifest, prints puzzle contents, or skips an original member. An interrupted
extraction leaves a partial destination; use a fresh empty destination to retry.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
import zipfile

CHUNK = 1024 * 1024
MANIFEST = "WORK/PACKET-MANIFEST.json"
TASK = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")


def safe_name(name: str) -> str:
    if (not isinstance(name, str) or not name or "\\" in name or "\0" in name
            or name.startswith("/") or ":" in name):
        raise ValueError("Unsafe archive path")
    parts = name.rstrip("/").split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("Unsafe archive path")
    return "/".join(parts)


def task_prefix(task: str) -> str:
    if not isinstance(task, str) or not TASK.fullmatch(task):
        raise ValueError("Invalid task ID")
    return f"WORK/repo/generators/{task}/"


def digest_stream(stream, writer=None) -> str:
    checksum = hashlib.sha256()
    while block := stream.read(CHUNK):
        checksum.update(block)
        if writer is not None:
            writer.write(block)
    return checksum.hexdigest()


def regular_path(root: Path, name: str) -> Path:
    path = root
    for part in PurePosixPath(safe_name(name)).parts:
        path /= part
        if path.is_symlink():
            raise ValueError(f"Symlink is forbidden: {name}")
    if not path.is_file():
        raise ValueError(f"Missing regular file: {name}")
    return path


def inventory(manifest: dict) -> dict[str, str]:
    if manifest.get("layout", {}).get("workspace") != "WORK":
        raise ValueError("Expected a WORK-layout review packet")
    entries = manifest["layout"].get("entry_files")
    files = manifest.get("files")
    if not isinstance(files, dict) or not isinstance(entries, dict):
        raise ValueError("Invalid packet file inventory")
    if set(entries) != {"START-HERE.md", "review.py"}:
        raise ValueError("Invalid outer entry inventory")
    expected = {}
    for relative, digest in files.items():
        name = "WORK/" + safe_name(relative)
        if name == MANIFEST:
            raise ValueError("Manifest cannot hash itself")
        expected[name] = digest
    expected.update(entries)
    if any(not isinstance(value, str) or not SHA.fullmatch(value)
           for value in expected.values()):
        raise ValueError("Invalid SHA-256 in packet inventory")
    return expected


def read_inventory(raw: bytes) -> dict[str, str]:
    return inventory(json.loads(raw))


def member_mode(info: zipfile.ZipInfo) -> int:
    kind = stat.S_IFMT(info.external_attr >> 16)
    if info.is_dir():
        if kind not in {0, stat.S_IFDIR}:
            raise ValueError("Non-directory ZIP entry has a directory name")
        if info.file_size != 0:
            raise ValueError("Directory ZIP entries must have empty payloads")
    elif kind not in {0, stat.S_IFREG}:
        raise ValueError("Symlinks and special ZIP entries are forbidden")
    return ((info.external_attr >> 16) & 0o777) or 0o644


def extract(archive: Path, destination: Path, *, editable_tasks=()) -> dict:
    archive, destination = Path(archive), Path(destination)
    if destination.is_symlink() or (destination.exists()
            and (not destination.is_dir() or any(destination.iterdir()))):
        raise FileExistsError("Extraction destination must be absent or empty")
    protected = ["WORK/repo/shared/data/"]
    protected.extend(task_prefix(task) for task in editable_tasks)
    if not editable_tasks:
        protected.append("WORK/repo/generators/")
    with zipfile.ZipFile(archive) as zipped:
        infos = zipped.infolist()
        seen = set()
        for info in infos:
            name = safe_name(info.filename)
            key = os.path.normcase(name)
            if key in seen:
                raise ValueError(f"Duplicate archive member: {name}")
            seen.add(key)
            member_mode(info)
        raw = zipped.read(MANIFEST)
        manifest_sha = hashlib.sha256(raw).hexdigest()
        expected = read_inventory(raw)
        for task in editable_tasks:
            prefix = task_prefix(task)
            if not any(name.startswith(prefix) for name in expected):
                raise ValueError(f"Editable task is absent from the packet: {task}")
        del raw
        actual = {info.filename for info in infos if not info.is_dir()}
        if actual != set(expected) | {MANIFEST}:
            raise ValueError("Archive inventory has missing or unexpected members")
        del actual, seen
        destination.mkdir(parents=True, exist_ok=True)
        destination = destination.resolve()
        linked = {}
        report = {"members": 0, "hardlinks": 0, "bytes_saved": 0,
                  "copy_fallbacks": 0, "manifest_sha256": manifest_sha,
                  "protected_prefixes": protected}
        # Local-header order avoids unnecessary seeks across the archive.
        for info in sorted(infos, key=lambda item: item.header_offset):
            name = safe_name(info.filename)
            target = destination.joinpath(*PurePosixPath(name).parts)
            if info.is_dir():
                with zipped.open(info) as stream:
                    digest_stream(stream)  # Validate local header, compression and CRC.
                target.mkdir(parents=True, exist_ok=True)
                report["members"] += 1
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            mode = member_mode(info)
            wanted = manifest_sha if name == MANIFEST else expected[name]
            eligible = (name.startswith("WORK/repo/")
                        and not any(name.startswith(prefix) for prefix in protected))
            key = (wanted, mode, info.date_time)
            previous = linked.get(key) if eligible else None
            owned = False
            try:
                # Even duplicate members are read fully, checking ZIP CRC and SHA.
                context = nullcontext()
                if previous is None:
                    context = target.open("xb")
                    owned = True
                with context as writer:
                    with zipped.open(info) as stream:
                        observed = digest_stream(stream, writer)
                if observed != wanted:
                    raise ValueError(f"Manifest hash mismatch: {name}")
                if previous is not None:
                    try:
                        os.link(previous, target)
                        owned = True
                    except OSError as exc:
                        # Portability fallback still preserves complete file bytes.
                        if target.exists():
                            raise
                        import errno
                        permitted = {errno.EXDEV, errno.EPERM, errno.EACCES,
                                     errno.ENOSYS, errno.EMLINK}
                        permitted.update(getattr(errno, field) for field in
                                         ("ENOTSUP", "EOPNOTSUPP") if hasattr(errno, field))
                        if exc.errno not in permitted:
                            raise
                        with previous.open("rb") as source, target.open("xb") as output:
                            owned = True
                            if digest_stream(source, output) != wanted:
                                raise ValueError("Previously extracted source changed")
                        os.chmod(target, mode)
                        report["copy_fallbacks"] += 1
                    else:
                        report["hardlinks"] += 1
                        report["bytes_saved"] += info.file_size
                else:
                    os.chmod(target, mode)
                    if eligible:
                        linked[key] = target
            except BaseException:
                # Remove only this run's current incomplete member.
                if owned and target.is_file() and not target.is_symlink():
                    target.unlink()
                raise
            report["members"] += 1
        return report


def verify(destination: Path) -> dict:
    root = Path(destination)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Expected a regular extraction directory")
    path = regular_path(root, MANIFEST)
    raw = path.read_bytes()
    manifest_sha = hashlib.sha256(raw).hexdigest()
    expected = read_inventory(raw)
    del raw
    for name, wanted in expected.items():
        target = regular_path(root, name)
        with target.open("rb") as stream:
            if digest_stream(stream) != wanted:
                raise ValueError(f"Manifest hash mismatch: {name}")
    return {"verified_files": len(expected), "manifest_sha256": manifest_sha}


def detach_tasks(destination: Path, tasks) -> dict:
    root = Path(destination)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Expected a regular extraction directory")
    detached = 0
    for task in tasks:
        prefix = task_prefix(task)
        directory = root.joinpath(*PurePosixPath(prefix.rstrip("/")).parts)
        # Validate every ancestor before walking the task tree.
        cursor = root
        for part in PurePosixPath(prefix.rstrip("/")).parts:
            cursor /= part
            if cursor.is_symlink():
                raise ValueError("Cannot detach through a symlink")
        if not directory.is_dir():
            raise ValueError(f"Missing task directory: {task}")
        for path in directory.rglob("*"):
            if path.is_symlink():
                raise ValueError("Cannot detach a tree containing symlinks")
            if not path.is_file() or path.stat().st_nlink < 2:
                continue
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(prefix=".detach-", dir=path.parent,
                                                 delete=False) as output:
                    temporary = Path(output.name)
                    with path.open("rb") as source:
                        digest_stream(source, output)
                shutil.copystat(path, temporary)
                os.replace(temporary, path)
                detached += 1
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
    return {"detached_files": detached, "task_ids": list(tasks)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    command = actions.add_parser("extract")
    command.add_argument("archive", type=Path)
    command.add_argument("destination", type=Path)
    command.add_argument("--editable-task", action="append", default=[],
                         help="Never hardlink this task; repeat for multiple tasks")
    command.add_argument("--verify", action="store_true",
                         help="Run an additional on-disk hash verification pass")
    command = actions.add_parser("verify")
    command.add_argument("destination", type=Path)
    command = actions.add_parser("detach")
    command.add_argument("destination", type=Path)
    command.add_argument("--task", action="append", required=True,
                         help="Make this task's files independent before editing")
    args = parser.parse_args(argv)
    try:
        if args.action == "extract":
            report = extract(args.archive, args.destination,
                             editable_tasks=args.editable_task)
            if args.verify:
                report["verification"] = verify(args.destination)
        elif args.action == "verify":
            report = verify(args.destination)
        else:
            report = detach_tasks(args.destination, args.task)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
