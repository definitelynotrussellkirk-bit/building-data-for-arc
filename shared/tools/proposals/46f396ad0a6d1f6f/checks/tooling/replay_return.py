#!/usr/bin/env python3
"""Replay a builder-created ARCpuzzles delta into a new original extraction.

The outer wrapper layout contains WORK/repo while returned patches start with
repo/. Initialize Git at the fresh outer root and use --directory=WORK. Refuse
an existing destination, record all commands, and verify the repaired source
hash. Run the packet's normal task_tests stage afterward with an isolated venv.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import zipfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--return-zip", type=Path, required=True)
    parser.add_argument("--fresh", type=Path, required=True)
    parser.add_argument("--expected-generator-sha256", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    fresh = args.fresh.resolve()
    if fresh.exists() or args.receipt.exists():
        parser.error("fresh extraction and receipt paths must not exist")
    receipt = {"schema": "review-final-patch-replay-v1", "packet_sha256": sha(args.packet),
               "return_sha256": sha(args.return_zip), "fresh_root": str(fresh),
               "commands": [], "passed": False}
    args.receipt.parent.mkdir(parents=True, exist_ok=True)

    def run(argv):
        result = subprocess.run(argv, cwd=fresh, text=True, capture_output=True)
        receipt["commands"].append({"argv": argv, "cwd": str(fresh), "exit_code": result.returncode,
                                    "stdout": result.stdout, "stderr": result.stderr})
        if result.returncode:
            raise RuntimeError(f"command failed: {argv}")
        return result.stdout.strip()

    try:
        with zipfile.ZipFile(args.packet) as archive:
            for info in archive.infolist():
                path = PurePosixPath(info.filename)
                if path.is_absolute() or ".." in path.parts or "\\" in info.filename or stat.S_ISLNK(info.external_attr >> 16):
                    raise ValueError("unsafe original archive member")
            archive.extractall(fresh)
        with zipfile.ZipFile(args.return_zip) as archive:
            contract = json.loads(archive.read("ASSIGNMENT.json"))
            patch = archive.read("patches/source.patch")
        task = contract["task_id"]
        if not task.isalnum():
            raise ValueError("invalid task identifier")
        work = fresh / "WORK" if (fresh / "WORK/PACKET-MANIFEST.json").is_file() else fresh
        receipt["task_id"] = task
        receipt["patch_sha256"] = hashlib.sha256(patch).hexdigest()
        patch_path = fresh / "review-source.patch"
        patch_path.write_bytes(patch)
        run(["git", "init", "-q"])
        git_root = run(["git", "rev-parse", "--show-toplevel"])
        if Path(git_root).resolve() != fresh:
            raise ValueError("Git resolved to a parent worktree")
        options = ["--directory=WORK"] if work != fresh else []
        run(["git", "apply", "--check", *options, str(patch_path)])
        run(["git", "apply", *options, str(patch_path)])
        generator = work / "repo/generators" / task / "generator.py"
        receipt["generator_sha256"] = sha(generator)
        receipt["expected_generator_sha256"] = args.expected_generator_sha256
        if receipt["generator_sha256"] != args.expected_generator_sha256:
            raise ValueError("replayed generator bytes differ from the checked final source")
        receipt["passed"] = True
    except Exception as exc:
        receipt["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({key: receipt.get(key) for key in ("passed", "task_id", "patch_sha256", "generator_sha256", "error")}))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
