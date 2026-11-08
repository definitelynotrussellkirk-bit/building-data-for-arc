#!/usr/bin/env python3
"""Apply a returned ARCpuzzles delta in fresh WORK and retain a hash receipt.

Standard library plus Git. This tool does not draw assignments, read puzzle
answers, run generator code, or run tests. Use it on a disposable fresh copy.
A hash mismatch leaves the applied delta in that copy for inspection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys


def reject_symlink_path(path: Path) -> None:
    """Check before resolve so a symlink cannot hide in an ancestor."""
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError(f"Symlink path is forbidden: {part}")


def replay(args, receipt: dict) -> None:
    root = args.work.absolute()
    patch = args.patch.absolute()
    reject_symlink_path(root)
    reject_symlink_path(patch)
    root = root.resolve()
    patch = patch.resolve()
    if not root.is_dir() or not (root / "repo").is_dir():
        raise ValueError("--work must be the fresh WORK directory containing repo/")
    if not patch.is_file():
        raise ValueError("--patch must be a regular source.patch file")
    relative = PurePosixPath(args.generator)
    if not re.fullmatch(r"repo/generators/[A-Za-z0-9_-]+/generator\.py", args.generator):
        raise ValueError("--generator must name repo/generators/TASK_ID/generator.py")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", args.sha256):
        raise ValueError("--sha256 must be exactly 64 hexadecimal characters")
    generator = root.joinpath(*relative.parts)
    reject_symlink_path(generator)
    if not generator.is_file():
        raise ValueError(f"Selected generator does not exist: {generator}")
    # A fresh extraction must not redirect any patched path through a symlink.
    for member in root.rglob("*"):
        if member.is_symlink():
            raise ValueError(f"Symlink in fresh WORK is forbidden: {member}")
    git_dir = root / ".git"
    if git_dir.exists() and not git_dir.is_dir():
        raise ValueError("Existing WORK/.git must be a real directory, not a gitfile")
    receipt.update(work_directory=str(root), patch_path=str(patch),
                   patch_sha256=hashlib.sha256(patch.read_bytes()).hexdigest(),
                   generator_path=args.generator,
                   expected_generator_sha256=args.sha256.lower())
    # Explicit inherited GIT_DIR/WORK_TREE/etc must not redirect these commands.
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith("GIT_")}

    def run(*arguments: str) -> str:
        argv = ["git", "-C", str(root), *arguments]
        result = subprocess.run(argv, cwd=root, env=environment,
                                capture_output=True, text=True)
        receipt["commands"].append({"argv": argv, "cwd": str(root),
                                    "exit_code": result.returncode,
                                    "stdout": result.stdout,
                                    "stderr": result.stderr})
        if result.returncode:
            raise ValueError(f"Git command failed (exit {result.returncode}): "
                             + " ".join(arguments))
        return result.stdout.strip()

    if not git_dir.exists():
        run("init", "-q")
    top = Path(run("rev-parse", "--show-toplevel")).resolve()
    receipt["git_toplevel"] = str(top)
    if top != root:
        raise ValueError(f"Unexpected Git root: {top}; expected {root}")
    run("apply", "--check", str(patch))
    run("apply", str(patch))
    reject_symlink_path(generator)
    actual = hashlib.sha256(generator.read_bytes()).hexdigest()
    receipt["actual_generator_sha256"] = actual
    if actual != args.sha256.lower():
        raise ValueError(f"Generator SHA-256 mismatch: expected {args.sha256.lower()}, got {actual}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--generator", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--receipt", type=Path, required=True,
                        help="new JSON receipt path; never overwritten")
    args = parser.parse_args()
    destination = args.receipt.absolute()
    receipt = {"schema": "arcpuzzles-reviewer-replay-v1", "status": "failed", "commands": []}
    try:
        reject_symlink_path(destination)
        if destination.exists():
            raise ValueError(f"Receipt already exists; choose a new path: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    try:
        replay(args, receipt)
        receipt["status"] = "passed"
    except (ValueError, OSError) as exc:
        receipt["error"] = str(exc)
    try:
        with destination.open("x", encoding="utf-8") as handle:
            json.dump(receipt, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except OSError as exc:
        print(f"Could not write replay receipt: {exc}", file=sys.stderr)
        return 2
    print(f"Replay {receipt['status']}: {destination}")
    if receipt["status"] != "passed":
        print(receipt["error"], file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
