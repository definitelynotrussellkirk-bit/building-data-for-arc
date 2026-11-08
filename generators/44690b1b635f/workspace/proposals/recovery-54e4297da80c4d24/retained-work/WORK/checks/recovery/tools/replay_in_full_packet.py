#!/usr/bin/env python3
"""Safely replay a hash-bound recovery overlay into an extracted review packet."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative(value: str) -> Path:
    posix = PurePosixPath(value)
    if posix.is_absolute() or not posix.parts or ".." in posix.parts:
        raise ValueError(f"unsafe relative path in manifest: {value!r}")
    return Path(*posix.parts)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_assignment(packet_root: Path, manifest: dict) -> None:
    assignment_path = packet_root / "WORK" / "ASSIGNMENT.json"
    if not assignment_path.is_file():
        raise ValueError(f"missing packet assignment: {assignment_path}")
    assignment = read_json(assignment_path)
    expected_assignment = manifest.get("assignment_id")
    expected_task = manifest.get("task_id")
    if assignment.get("assignment_id") != expected_assignment:
        raise ValueError(
            f"assignment mismatch: packet={assignment.get('assignment_id')!r}, "
            f"overlay={expected_assignment!r}"
        )
    if assignment.get("task_id") != expected_task:
        raise ValueError(
            f"task mismatch: packet={assignment.get('task_id')!r}, overlay={expected_task!r}"
        )


def preflight(bundle_root: Path, packet_root: Path, manifest: dict):
    if manifest.get("schema") != "arcpuzzles-recovery-overlay-v1":
        raise ValueError(f"unsupported manifest schema: {manifest.get('schema')!r}")
    validate_assignment(packet_root, manifest)
    operations = []
    for row in manifest.get("files", []):
        source_rel = safe_relative(row["source"])
        destination_rel = safe_relative(row["destination"])
        source = bundle_root / source_rel
        destination = packet_root / destination_rel
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"overlay source is not a regular file: {source_rel}")
        source_hash = sha256(source)
        if source_hash != row["sha256"]:
            raise ValueError(
                f"overlay source hash mismatch for {source_rel}: "
                f"expected {row['sha256']}, got {source_hash}"
            )
        if destination.is_symlink():
            raise ValueError(f"refusing symlink destination: {destination_rel}")
        current_hash = sha256(destination) if destination.is_file() else None
        if current_hash == source_hash:
            status = "already-applied"
        else:
            expected_preimage = row.get("preimage_sha256")
            if (
                current_hash is not None
                and expected_preimage is None
                and not row.get("allow_unbound_overwrite", False)
            ):
                raise ValueError(
                    f"unbound overwrite refused for {destination_rel}; "
                    "set allow_unbound_overwrite only after reviewing the existing file"
                )
            if expected_preimage is not None and current_hash != expected_preimage:
                raise ValueError(
                    f"preimage hash mismatch for {destination_rel}: "
                    f"expected {expected_preimage}, got {current_hash or 'missing'}"
                )
            status = "pending"
        operations.append(
            {
                "source": source,
                "source_rel": source_rel,
                "destination": destination,
                "destination_rel": destination_rel,
                "source_hash": source_hash,
                "current_hash": current_hash,
                "status": status,
            }
        )
    return operations


def backup_name(destination: Path, digest: str) -> str:
    suffix = "".join(destination.suffixes)
    stem = destination.name[: -len(suffix)] if suffix else destination.name
    return f"{stem}-{digest[:12]}{suffix}"


def apply_operations(packet_root: Path, operations) -> None:
    backup_dir = packet_root / "WORK" / "checks" / "recovery-replay"
    for operation in operations:
        if operation["status"] == "already-applied":
            continue
        destination = operation["destination"]
        if destination.is_file():
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup = backup_dir / backup_name(destination, operation["current_hash"])
            if backup.exists():
                if sha256(backup) != operation["current_hash"]:
                    raise ValueError(f"existing backup hash mismatch: {backup}")
            else:
                shutil.copy2(destination, backup)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=destination.parent,
            prefix=f".{destination.name}.",
            delete=False,
        ) as handle:
            temp = Path(handle.name)
            with operation["source"].open("rb") as source_handle:
                shutil.copyfileobj(source_handle, handle)
        try:
            os.replace(temp, destination)
        finally:
            if temp.exists():
                temp.unlink()
        if sha256(destination) != operation["source_hash"]:
            raise ValueError(f"post-copy hash mismatch: {operation['destination_rel']}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--packet-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--apply", action="store_true", help="copy files after all preflight checks pass")
    args = parser.parse_args(argv)

    try:
        bundle_root = args.bundle_root.resolve()
        packet_root = args.packet_root.resolve()
        manifest_path = (args.manifest or bundle_root / "PATCH-MANIFEST.json").resolve()
        manifest = read_json(manifest_path)
        operations = preflight(bundle_root, packet_root, manifest)
        for operation in operations:
            print(f"{operation['status']:15s} {operation['destination_rel']}")
        if args.apply:
            apply_operations(packet_root, operations)
            print("overlay applied and destination hashes verified")
        else:
            print("dry run only; add --apply to copy the overlay")
        commands = manifest.get("official_commands", [])
        if commands:
            print("\nOfficial full-packet replay commands:")
            for command in commands:
                print(command)
        return 0
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
