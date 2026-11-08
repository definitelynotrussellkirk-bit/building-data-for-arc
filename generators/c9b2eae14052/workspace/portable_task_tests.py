"""Run every task-local pytest file in the packet's portable runtime layout.

The review packet stores generators separately from ``shared/runtime``.  Some
frozen tests expect the installed per-puzzle layout and a task-local canonical
ledger.  This helper builds that layout in a temporary directory, prints the
actual runtime path, runs pytest, and removes the tree afterward.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[1]
TASK_ID = TASK_ROOT.name


def main() -> int:
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-portable-pytest-") as tmp:
        runtime = Path(tmp)
        shutil.copytree(REPO_ROOT / "shared" / "runtime", runtime, dirs_exist_ok=True)
        runtime_task = runtime / "puzzle_generators" / "per_puzzle" / TASK_ID
        shutil.copytree(
            TASK_ROOT,
            runtime_task,
            ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc", "*.pyo"),
        )
        canonical = runtime_task / "data" / "canonical"
        canonical.mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl",
            canonical / "puzzles.jsonl",
        )
        print(f"portable_runtime_directory={runtime}", flush=True)
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", str(runtime_task / "tests")],
            cwd=runtime,
            text=True,
        )
        return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
