#!/usr/bin/env python3
"""Stage the selected generator in the portable runtime and run its focused tests."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent
TASK_DIR = WORKSPACE.parent
REPO = TASK_DIR.parents[1]
TASK_ID = TASK_DIR.name
TEST_FILE = TASK_DIR / "tests" / f"test_generator_{TASK_ID}.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix=f"arc-{TASK_ID}-test-") as tmp:
        root = Path(tmp)
        runtime_package = root / "puzzle_generators"
        shutil.copytree(REPO / "shared" / "runtime" / "puzzle_generators", runtime_package)
        selected = runtime_package / "per_puzzle" / TASK_ID
        selected.mkdir(parents=True, exist_ok=True)
        shutil.copy2(TASK_DIR / "generator.py", selected / "generator.py")
        canonical = root / "data" / "canonical"
        canonical.mkdir(parents=True)
        shutil.copy2(REPO / "shared" / "data" / "canonical" / "puzzles.jsonl", canonical / "puzzles.jsonl")
        staged_workspace = root / "repo" / "generators" / TASK_ID / "workspace"
        staged_workspace.mkdir(parents=True)
        shutil.copy2(
            WORKSPACE / "shape_support_probe.py",
            staged_workspace / "shape_support_probe.py",
        )
        shutil.copy2(
            WORKSPACE / "shortcut_counterexample.py",
            staged_workspace / "shortcut_counterexample.py",
        )
        shutil.copy2(
            WORKSPACE / "candidate_rival_sweep.py",
            staged_workspace / "candidate_rival_sweep.py",
        )
        tests = root / "tests"
        tests.mkdir()
        staged_test = tests / TEST_FILE.name
        shutil.copy2(TEST_FILE, staged_test)
        env = os.environ.copy()
        env["PYTHONPATH"] = str(root)
        env.setdefault("TERM", "xterm")
        command = [sys.executable, "-m", "pytest", "-q", str(staged_test)]
        print(f"staged_runtime={root}")
        print("command=" + " ".join(command))
        completed = subprocess.run(command, cwd=root, env=env, check=False)
        return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
