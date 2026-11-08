#!/usr/bin/env python3
"""Run this review's new focused tests in a clean, portable mini-runtime.

The issued portable task-test stage is blocked before pytest by the frozen
legacy fixture.  This helper deliberately selects only the two reviewer-added
test files, copies the final generator and its public runtime dependencies into
a fresh temporary tree, and records source hashes plus complete pytest output.
It does not turn the blocked aggregate task-test stage into a pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from reviewer_support import find_root


TASK_ID = "113d9bb402d3"
TEST_NAMES = ("test_repair_schedule.py", "test_parametric_variant.py")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy_file(source: Path, destination: Path) -> None:
    if not source.is_file() or source.is_symlink():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def _ignore_runtime(_directory: str, names: list[str]) -> set[str]:
    return {
        name
        for name in names
        if name in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
        or name.endswith((".pyc", ".pyo"))
    }


def _count(pattern: str, text: str) -> int:
    matches = re.findall(pattern, text)
    return int(matches[-1]) if matches else 0


def run(out: Path) -> int:
    root = find_root(__file__)
    task_home = root / "generators" / TASK_ID
    generator = task_home / "generator.py"
    tests = [task_home / "tests" / name for name in TEST_NAMES]
    prototype = task_home / "workspace" / "parametric" / "prototype.py"
    canonical = root / "shared" / "data" / "canonical" / "puzzles.jsonl"
    runtime = root / "shared" / "runtime"

    required = [generator, prototype, canonical, *tests]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing focused-test inputs: " + ", ".join(missing))

    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-focused-") as raw_tmp:
        tmp = Path(raw_tmp)
        shutil.copytree(runtime, tmp / "shared" / "runtime", ignore=_ignore_runtime)
        _copy_file(canonical, tmp / "shared" / "data" / "canonical" / "puzzles.jsonl")

        # Preserve a repository-shaped authoring tree for the prototype tests.
        _copy_file(generator, tmp / "generators" / TASK_ID / "generator.py")
        init = task_home / "__init__.py"
        if init.is_file():
            _copy_file(init, tmp / "generators" / TASK_ID / "__init__.py")
        _copy_file(prototype, tmp / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py")
        copied_tests = []
        for source in tests:
            destination = tmp / "generators" / TASK_ID / "tests" / source.name
            _copy_file(source, destination)
            copied_tests.append(destination)

        # Provide the selected execution-layout alias expected by the generator test.
        alias_home = tmp / "shared" / "runtime" / "puzzle_generators" / "per_puzzle" / TASK_ID
        _copy_file(generator, alias_home / "generator.py")
        _copy_file(init, alias_home / "__init__.py")

        command = [sys.executable, "-m", "pytest", "-q", *[str(path) for path in copied_tests]]
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(
            [str(tmp / "shared" / "runtime"), env.get("PYTHONPATH", "")]
        ).rstrip(os.pathsep)
        completed = subprocess.run(
            command,
            cwd=tmp,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    combined = completed.stdout + "\n" + completed.stderr
    report = {
        "schema": "arcpuzzles-review-focused-tests-v1",
        "task_id": TASK_ID,
        "scope": "reviewer-added tests only; frozen legacy fixture excluded because the official aggregate preflight blocks before pytest",
        "runtime_layout": "fresh temporary repository-shaped tree with copied public runtime, canonical ledger, final selected generator, prototype, and two tests",
        "generator_sha256": _sha256(generator),
        "prototype_sha256": _sha256(prototype),
        "test_sha256": {path.name: _sha256(path) for path in tests},
        "command": ["python3", "-m", "pytest", "-q", *[f"generators/{TASK_ID}/tests/{name}" for name in TEST_NAMES]],
        "cwd": "fresh temporary runtime root",
        "exit_code": completed.returncode,
        "counts": {
            "passed": _count(r"(\d+) passed", combined),
            "failed": _count(r"(\d+) failed", combined),
            "errors": _count(r"(\d+) errors?", combined),
            "skipped": _count(r"(\d+) skipped", combined),
        },
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "limitations": [
            "This focused run does not include or waive the immutable frozen fixture.",
            "The official selected task-test aggregate remains blocked until that fixture uses portable root helpers.",
        ],
    }
    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    print(f"focused test report: {out}")
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    return run(args.out)


if __name__ == "__main__":
    raise SystemExit(main())
