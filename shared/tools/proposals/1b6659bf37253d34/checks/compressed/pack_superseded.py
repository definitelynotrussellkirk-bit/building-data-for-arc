#!/usr/bin/env python3
"""One-shot lossless packaging of the five explicitly authorized evidence paths."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile

from restore_evidence import destination_path, file_digest, restore, safe_relative, verify


CANDIDATES = [
    ("checks/after", "after-failed-seed-cap"),
    ("checks/schedule-census-final.json", "schedule-census-intermediate"),
    ("checks/parametric/height-suite-v1", "parametric-height-suite-v1"),
    ("checks/parametric/v2-privacy-red-fixtures", "parametric-v2-privacy-red-fixtures"),
    ("checks/parametric/v2-focused-green-fixtures", "parametric-v2-focused-green-fixtures"),
]
PROTECTED = [
    "checks/after-final", "checks/parametric/height-suite-v2",
    "checks/schedule-census-v3.json", "checks/lesson-census-v3.json.gz",
]


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def regular_files(path):
    if path.is_file() and not path.is_symlink():
        return [path]
    return sorted(p for p in path.rglob("*") if p.is_file() and not p.is_symlink())


def total_bytes(path):
    return sum(p.stat().st_size for p in regular_files(path))


def snapshot(work, relative, archive_file):
    safe_relative(relative)
    source = work / relative
    if source.is_symlink() or not source.exists():
        raise ValueError(f"candidate is absent or a symlink: {relative}")
    paths = [source, *sorted(source.rglob("*"))] if source.is_dir() else [source]
    files, links, directories = [], [], []
    for path in paths:
        original = path.relative_to(work).as_posix()
        safe_relative(original)
        if path.is_symlink():
            target = os.readlink(path)
            resolved = path.resolve(strict=True)
            if not resolved.is_relative_to(source):
                raise ValueError(f"alias escapes its candidate directory: {path}")
            target_bytes = os.fsencode(target)
            links.append({"original_path": original, "original_target": target,
                          "original_target_bytes": len(target_bytes),
                          "original_target_sha256": hashlib.sha256(target_bytes).hexdigest(),
                          "target_path": resolved.relative_to(work).as_posix(),
                          "portable_target": os.path.relpath(resolved, path.parent)})
        elif path.is_dir():
            directories.append(original)
        elif path.is_file():
            size, digest = file_digest(path)
            files.append({"original_path": original, "original_bytes": size,
                          "original_sha256": digest, "archive_file": archive_file})
        else:
            raise ValueError(f"unsupported filesystem object: {path}")
    return files, links, directories


def package(work, *, remove_verified_originals):
    work = work.resolve()
    out = work / "checks/compressed"
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "MANIFEST.json"
    if manifest_path.exists():
        raise FileExistsError("archive manifest already exists; refusing to overwrite evidence")
    before = total_bytes(work / "checks")
    protected_paths = set()
    for relative in PROTECTED:
        protected_paths.update(regular_files(work / relative))
    protected_paths.update(p for p in (work / "checks").glob("*.log") if p.is_file())
    protected_paths.update(p for p in (work / "checks/parametric").glob("*.log") if p.is_file())
    protected = {p.relative_to(work).as_posix(): file_digest(p) for p in sorted(protected_paths)}
    staging = out / "_tar_staging"
    staging.mkdir(exist_ok=False)
    manifest = {"schema": "arc-review-tar-members-v1", "created_utc": datetime.now(timezone.utc).isoformat(),
                "original_work_root": str(work),
                "purpose": "Lossless compression of superseded and intermediate evidence; failures remain retained.",
                "archives": [], "files": [], "symlinks": [], "directories": [],
                "symlink_policy": "Preserve exact original alias target strings/hashes; restore equivalent internal relative aliases for portability."}
    native = {"schema": "arcpuzzles-evidence-gzip-v1", "compression": "gzip", "archive_format": "tar",
              "restore_note": "Use restore_evidence.py for safe member restoration. This native index verifies gzip and raw tar bytes; MANIFEST.json verifies original members.",
              "files": []}
    for relative, label in CANDIDATES:
        archive_name = label + ".tar.gz"
        archive_path = out / archive_name
        if archive_path.exists():
            raise FileExistsError(archive_path)
        files, links, directories = snapshot(work, relative, archive_name)
        tar_path = staging / (label + ".tar")
        with tarfile.open(tar_path, "w", format=tarfile.PAX_FORMAT) as bundle:
            for row in files:
                info = tarfile.TarInfo(row["original_path"])
                info.size = row["original_bytes"]
                info.mode = 0o644
                info.mtime = 0
                with (work / row["original_path"]).open("rb") as stream:
                    bundle.addfile(info, stream)
        tar_size, tar_hash = file_digest(tar_path)
        with tar_path.open("rb") as source, archive_path.open("xb") as output:
            with gzip.GzipFile(filename="", mode="wb", fileobj=output, compresslevel=9, mtime=0) as compressed:
                shutil.copyfileobj(source, compressed)
        compressed_size, compressed_hash = file_digest(archive_path)
        manifest["archives"].append({
            "original_root": relative, "archive_file": archive_name,
            "file_count": len(files), "original_bytes": sum(row["original_bytes"] for row in files),
            "tar_bytes": tar_size, "tar_sha256": tar_hash,
            "compressed_bytes": compressed_size, "compressed_sha256": compressed_hash,
        })
        manifest["files"].extend(files)
        manifest["symlinks"].extend(links)
        manifest["directories"].extend(directories)
        native["files"].append({"path": label + ".tar", "compressed_path": archive_name,
                                "raw_size": tar_size, "raw_sha256": tar_hash,
                                "compressed_size": compressed_size, "compressed_sha256": compressed_hash})
    write_json(manifest_path, manifest)
    write_json(out / "archives.json", native)
    verification = verify(manifest_path)
    restore_root = out / "_restore_validation"
    restoration = restore(manifest_path, restore_root)
    rejected_paths = ["../escape", "/tmp/escape", "checks/../escape",
                      "checks/a/../../escape", "checks\\escape", "checks/C:/escape"]
    for unsafe in rejected_paths:
        try:
            safe_relative(unsafe)
        except ValueError:
            pass
        else:
            raise AssertionError(f"unsafe path accepted: {unsafe}")
    try:
        restore(manifest_path, restore_root)
    except FileExistsError:
        overwrite_rejected = True
    else:
        raise AssertionError("restoration overwrote existing evidence")
    alias_probe = restore_root / "checks/_unsafe_parent_probe"
    alias_probe.symlink_to(out, target_is_directory=True)
    try:
        destination_path(restore_root, "checks/_unsafe_parent_probe/file")
    except ValueError:
        symlink_parent_rejected = True
    else:
        raise AssertionError("restoration accepted a symlink ancestor")
    finally:
        alias_probe.unlink()
    # Recheck every original and inventory after archive/restore validation,
    # before removing any original evidence.
    for relative, label in CANDIDATES:
        observed = snapshot(work, relative, label + ".tar.gz")
        expected = ([row for row in manifest["files"] if row["archive_file"] == label + ".tar.gz"],
                    [row for row in manifest["symlinks"] if row["original_path"].startswith(relative + "/")],
                    [row for row in manifest["directories"] if row == relative or row.startswith(relative + "/")])
        if observed != expected:
            raise RuntimeError(f"original inventory or bytes changed before removal: {relative}")
    if remove_verified_originals:
        for row in manifest["files"]:
            (work / row["original_path"]).unlink()
        for row in manifest["symlinks"]:
            (work / row["original_path"]).unlink()
        for directory in sorted(manifest["directories"], key=lambda value: len(Path(value).parts), reverse=True):
            (work / directory).rmdir()
    # Only locally created validation copies and uncompressed tar staging.
    shutil.rmtree(restore_root)
    shutil.rmtree(staging)
    for relative, identity in protected.items():
        if file_digest(work / relative) != identity:
            raise RuntimeError(f"protected final evidence changed: {relative}")
    receipt = {
        "status": "verified-compressed-originals-removed" if remove_verified_originals else "verified-compressed-originals-retained",
        "command_argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd()), "exit_code": 0,
        "checks_regular_bytes_before": before, "checks_regular_bytes_after": 0,
        "removed_original_regular_bytes": sum(row["original_bytes"] for row in manifest["files"]) if remove_verified_originals else 0,
        "archive_regular_bytes": sum(row["compressed_bytes"] for row in manifest["archives"]),
        "manifest_sha256": file_digest(manifest_path)[1],
        "native_gzip_index_sha256": file_digest(out / "archives.json")[1],
        "archive_verification": verification, "portable_restore_verification": restoration,
        "safe_restore_probes": {"unsafe_paths_rejected": rejected_paths,
                                "existing_file_overwrite_rejected": overwrite_rejected,
                                "symlink_parent_rejected": symlink_parent_rejected},
        "protected_final_files_verified": len(protected),
        "protected_final_files": {path: {"bytes": identity[0], "sha256": identity[1]} for path, identity in protected.items()},
        "restore_tool_sha256": file_digest(out / "restore_evidence.py")[1],
        "pack_tool_sha256": file_digest(Path(__file__).resolve())[1],
        "budget_bytes": 19 * 1024 * 1024,
    }
    receipt_path = out / "compression-receipt.json"
    for _ in range(4):
        write_json(receipt_path, receipt)
        measured = total_bytes(work / "checks")
        if measured == receipt["checks_regular_bytes_after"]:
            break
        receipt["checks_regular_bytes_after"] = measured
    write_json(receipt_path, receipt)
    if receipt["checks_regular_bytes_after"] > receipt["budget_bytes"]:
        raise RuntimeError("compression completed but the requested checks budget is not yet met")
    return {key: receipt[key] for key in (
        "status", "checks_regular_bytes_before", "checks_regular_bytes_after",
        "removed_original_regular_bytes", "archive_regular_bytes", "protected_final_files_verified")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--remove-verified-originals", action="store_true")
    args = parser.parse_args()
    print(json.dumps(package(args.work_root, remove_verified_originals=args.remove_verified_originals), indent=2))
