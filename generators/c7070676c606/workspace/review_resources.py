"""Estimate review staging space from a real runtime manifest, without copying it.

Useful before parallel batteries, task tests, or fresh packet replay. Estimates
include 4-KiB file allocation but are advisory: directories, caches and concurrent
users can consume more space. This tool never deletes files or reserves storage.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import zipfile


def allocated(size):
    return ((size + 4095) // 4096) * 4096


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--temp-dir", type=Path,
                        default=Path(os.environ.get("TMPDIR", "/tmp")))
    parser.add_argument("--packet-zip", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    manifest = json.loads(args.manifest.read_text())
    staged = {}
    for entry in manifest["files"]:
        source = repo / entry["library_path"]
        if source.is_file():
            staged[entry["runtime_path"]] = source.stat().st_size
    # Task-test staging mirrors the same manifest at its library paths, plus
    # the catalog, selected task and public Python controller package.
    portable = dict(staged)
    for entry in manifest["files"]:
        source = repo / entry["library_path"]
        if source.is_file():
            portable[entry["library_path"]] = source.stat().st_size
    for home in (repo / "catalog", repo / "generators" / args.task,
                 repo / "src" / "arcpuzzles"):
        for source in home.rglob("*"):
            relative = source.relative_to(repo)
            if (source.is_file() and "__pycache__" not in relative.parts
                    and "evidence" not in relative.parts and source.suffix != ".pyc"):
                portable[relative.as_posix()] = source.stat().st_size
    available = shutil.disk_usage(args.temp_dir).free
    report = {
        "schema": "review-resource-estimate-v1", "task_id": args.task,
        "repo": str(repo), "manifest": str(args.manifest.resolve()),
        "temp_dir": str(args.temp_dir.resolve()), "available_bytes": available,
        "runtime_file_bytes": sum(staged.values()),
        "runtime_allocated_file_bytes": sum(map(allocated, staged.values())),
        "portable_test_file_bytes": sum(portable.values()),
        "portable_test_allocated_file_bytes": sum(map(allocated, portable.values())),
        "scope": "File-content estimate; excludes directories, caches, process memory and concurrent writes.",
        "advice": "Run large stages sequentially when their combined estimates approach available bytes."
    }
    if args.packet_zip:
        with zipfile.ZipFile(args.packet_zip) as archive:
            files = [row for row in archive.infolist() if not row.is_dir()]
        report["fresh_packet_files"] = len(files)
        report["fresh_packet_file_bytes"] = sum(row.file_size for row in files)
        report["fresh_packet_allocated_file_bytes"] = sum(allocated(row.file_size) for row in files)
    report["runtime_plus_portable_test_allocated_bytes"] = (
        report["runtime_allocated_file_bytes"] + report["portable_test_allocated_file_bytes"])
    rendered = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("x") as handle:
            handle.write(rendered)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
