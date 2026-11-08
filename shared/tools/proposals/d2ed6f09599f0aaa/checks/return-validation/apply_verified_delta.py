"""Apply a task delta with explicit Git prefix and before/after byte checks.

Run only on an authorized disposable checkout. The caller supplies the reviewed
patch, expected before/after hashes, workspace, and independent Git root.
Uses only Python's standard library and Git; sends no signals or network calls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import time


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_delta(args: argparse.Namespace, report: dict) -> None:
    workspace = args.workspace.resolve(strict=True)
    expected_root = args.git_root.resolve(strict=True)
    patch = args.patch.resolve(strict=True)
    expected_file = args.expected_files.resolve(strict=True)
    expected = json.loads(expected_file.read_text())
    report.update(workspace=str(workspace), expected_git_root=str(expected_root),
                  patch_sha256=digest(patch), expected_files_sha256=digest(expected_file),
                  generator_sha256=expected["generator_sha256"], commands=[])
    if report["patch_sha256"] != expected["source_patch_sha256"]:
        raise ValueError("Patch bytes do not match the reviewed source manifest")

    def run(argv: list[str]) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(argv, cwd=workspace, text=True, capture_output=True)
        report["commands"].append({"cwd": ".", "actual_cwd": str(workspace),
                                   "argv": argv, "exit_code": result.returncode,
                                   "stdout": result.stdout, "stderr": result.stderr})
        if result.returncode:
            raise RuntimeError(f"Command failed ({result.returncode}): {argv!r}")
        if "Skipped patch" in result.stderr:
            raise RuntimeError("Git skipped a patch; zero exit status is insufficient")
        return result

    actual_root = Path(run(["git", "rev-parse", "--show-toplevel"]).stdout.strip()).resolve()
    if actual_root != expected_root:
        raise ValueError(f"Unexpected Git root: {actual_root}; expected {expected_root}")
    prefix = workspace.relative_to(actual_root).as_posix()
    report["git_prefix"] = "" if prefix == "." else prefix

    patch_paths = [line[6:] for line in patch.read_text().splitlines()
                   if line.startswith("+++ b/")]
    expected_rows = expected["files"]
    if len(patch_paths) != len(set(patch_paths)):
        raise ValueError("Repeated patch path")
    if sorted(patch_paths) != sorted(row["path"] for row in expected_rows):
        raise ValueError("Patch paths differ from the reviewed source manifest")
    task_prefix = f"repo/generators/{expected['task_id']}/"
    for row in expected_rows:
        rel = PurePosixPath(row["path"])
        if rel.is_absolute() or ".." in rel.parts or not str(rel).startswith(task_prefix):
            raise ValueError(f"Path outside selected task: {rel}")
        path = workspace.joinpath(*rel.parts)
        if any(part.is_symlink() for part in [path, *path.parents]
               if part == workspace or workspace in part.parents):
            raise ValueError(f"Symlink in source path: {rel}")
        before = row["before_sha256"]
        if before is None:
            if path.exists():
                raise ValueError(f"Expected new file already exists: {rel}")
        elif not path.is_file() or digest(path) != before:
            raise ValueError(f"Baseline bytes do not match: {rel}")

    directory = [] if prefix == "." else [f"--directory={prefix}"]
    run(["git", "apply", "--check", "--verbose", *directory, str(patch)])
    run(["git", "apply", "--verbose", *directory, str(patch)])
    actual_rows = []
    for row in expected_rows:
        path = workspace / row["path"]
        actual = digest(path)
        if actual != row["after_sha256"]:
            raise ValueError(f"Applied bytes do not match expected result: {row['path']}")
        actual_rows.append({"path": row["path"], "sha256": actual,
                            "bytes": path.stat().st_size, "matches_expected": True})
    generator = workspace / task_prefix / "generator.py"
    if digest(generator) != expected["generator_sha256"]:
        raise ValueError("Final generator identity mismatch")
    report.update(status="verified_applied", changed_files=actual_rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("workspace", "git-root", "patch", "expected-files", "receipt"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    source_tree = args.workspace.resolve() / "repo"
    receipt_path = args.receipt.resolve()
    if receipt_path == source_tree or source_tree in receipt_path.parents:
        parser.error("Receipt must be outside the workspace source tree")
    if args.receipt.exists() or args.receipt.is_symlink():
        parser.error("Receipt exists; choose a fresh path to retain earlier attempts")
    started = time.monotonic()
    report = {"schema": "verified-task-delta-replay-v1", "status": "started",
              "argv": [sys.executable, *sys.argv], "actual_cwd": str(Path.cwd()),
              "helper_source_sha256": digest(Path(__file__)),
              "exit_code": None, "error": None}
    code = 0
    try:
        apply_delta(args, report)
    except Exception as exc:
        code = 1
        report.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    report.update(exit_code=code, elapsed_seconds=round(time.monotonic() - started, 3))
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    with args.receipt.open("x") as receipt_file:
        receipt_file.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "exit_code": code,
                      "receipt": str(args.receipt), "error": report["error"]}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
