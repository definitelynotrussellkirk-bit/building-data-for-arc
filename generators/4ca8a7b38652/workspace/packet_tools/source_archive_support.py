"""Strict immutable-source verification for the opt-in copied return builder.

The caller must already have run the unchanged stock candidate baseline/scope
checks. Nothing is extracted, and no source or assignment is modified.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
import zipfile

from packet_zip import Packet, digest_file, digest_stream, no_symlinks

CACHE_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
CACHE_SUFFIXES = {".pyc", ".pyo"}


def _identity(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def verify_archive_backed_sources(packet_root, source_zip, validated_candidates):
    root = Path(packet_root).absolute()
    source = Path(source_zip).absolute()
    no_symlinks(root)
    candidates = set(validated_candidates)
    expected_inventory = hashlib.sha256()
    missing_inventory = hashlib.sha256()
    counts = {"archive_body_count_verified": 0, "materialized_protected_sources_verified": 0,
              "missing_protected_sources_supplied_by_archive": 0,
              "validated_candidate_original_members": 0}
    missing_sample = []
    with source.open("rb") as source_stream:
        before = _identity(os.fstat(source_stream.fileno()))
        with zipfile.ZipFile(source_stream) as archive:
            packet = Packet(archive, source)
            manifest_path = root / "PACKET-MANIFEST.json"
            no_symlinks(manifest_path)
            if not manifest_path.is_file() or digest_file(manifest_path) != packet.packet_id:
                raise ValueError("Live manifest is not the byte-exact original source manifest")
            expected_repo_paths = {name.removeprefix(packet.prefix) for name in packet.files
                                   if name.startswith(packet.prefix + "repo/")}
            for name in sorted(packet.files):
                digest, size = packet.read_verified(name)
                counts["archive_body_count_verified"] += 1
                inventory_line = f"{name}\0{digest}\0{size}\n".encode()
                expected_inventory.update(inventory_line)
                if packet.prefix and not name.startswith(packet.prefix):
                    relative, target = None, root.parent / name
                else:
                    relative = name.removeprefix(packet.prefix)
                    target = root / relative
                # Every candidate has already passed stock baseline/scope checks.
                if relative in candidates:
                    counts["validated_candidate_original_members"] += 1
                    continue
                no_symlinks(target)
                try:
                    live_stat = target.stat()
                except FileNotFoundError:
                    counts["missing_protected_sources_supplied_by_archive"] += 1
                    missing_inventory.update(inventory_line)
                    if len(missing_sample) < 25:
                        missing_sample.append(name)
                    continue
                if (not stat.S_ISREG(live_stat.st_mode) or live_stat.st_mode & 0o111
                        or live_stat.st_size != size or digest_file(target) != digest):
                    raise ValueError(f"Changed or unsafe protected source: {name}")
                counts["materialized_protected_sources_verified"] += 1

            # Retain stock undeclared-source semantics and reject unsafe live types.
            repo = root / "repo"
            no_symlinks(repo)
            for directory, dirs, names in os.walk(repo, followlinks=False):
                parent = Path(directory)
                for name in dirs:
                    no_symlinks(parent / name)
                for name in names:
                    target = parent / name
                    relative = target.relative_to(root).as_posix()
                    no_symlinks(target)
                    if any(part in CACHE_PARTS for part in target.relative_to(root).parts) or target.suffix in CACHE_SUFFIXES:
                        continue
                    if not stat.S_ISREG(target.stat().st_mode):
                        raise ValueError(f"Unsafe live repository source type: {relative}")
                    if relative not in expected_repo_paths and relative not in candidates:
                        raise ValueError(f"Undeclared new source outside selected generator: {relative}")
            source_stream.seek(0)
            source_digest, _ = digest_stream(source_stream)
            if before != _identity(os.fstat(source_stream.fileno())) or before != _identity(source.stat()):
                raise ValueError("Source ZIP changed during verification")
            return {
                "schema": "arcpuzzles-archive-backed-source-verification-v1",
                "status": "passed",
                "mode": "verified_original_archive_plus_present_protected_sources",
                "local_proposal": True,
                "stock_wrapper_supports_sparse_packaging": False,
                "packet_id": packet.packet_id,
                "source_zip_sha256": source_digest,
                "archive_file_count": len(packet.files),
                "archive_inventory_matches_manifest": True,
                "all_archive_bodies_verified": counts["archive_body_count_verified"] == len(packet.files),
                "verified_original_inventory_sha256": expected_inventory.hexdigest(),
                "missing_protected_inventory_sha256": missing_inventory.hexdigest(),
                "missing_protected_source_sample": missing_sample,
                "missing_sample_limit": 25,
                "undeclared_live_repository_sources_checked": True,
                "source_files_extracted": 0,
                "task_tests_run": False,
                "training_admitted": False,
                **counts,
            }
