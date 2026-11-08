#!/usr/bin/env python3
"""Run every task-local test in a fresh portable runtime; retain its receipt.

From packet_root:
  python3 run_with_racket.py python3 generators/53ffc8bc9584/workspace/run_task_tests.py --out ../checks/task-tests

Only the tests are copied from the source tree. Generator/helpers/reference
data come from the public runtime snapshot, with no source-tree PYTHONPATH.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from arcpuzzles import Catalog
from arcpuzzles.runtime import prepare_runtime

TASK_ID = "53ffc8bc9584"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    library = Path.cwd().resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-task-tests-") as tmp:
        runtime = Path(tmp)
        manifest = prepare_runtime(Catalog(library), runtime, TASK_ID)
        tests = library / "generators" / TASK_ID / "tests"
        shutil.copytree(tests, runtime / "selected_tests", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        # Keep installed dependency locations available.  Some valid Python
        # setups install pytest in the interpreter's user site; disabling it
        # would hide a declared dependency without improving source isolation.
        argv = [sys.executable, "-m", "pytest", "-q", "selected_tests"]
        process = subprocess.run(argv, cwd=runtime, env=env, capture_output=True, text=True)
        (out / "stdout.log").write_text(process.stdout)
        (out / "stderr.log").write_text(process.stderr)
        (out / "runtime-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        report = {
            "task_id": TASK_ID, "command": [sys.executable, *sys.argv], "cwd": str(library),
            "runtime_cwd": str(runtime), "test_command": argv, "exit_code": process.returncode,
            "generator_sha256": hashlib.sha256((library / "generators" / TASK_ID / "generator.py").read_bytes()).hexdigest(),
            "test_sha256": {str(p.relative_to(tests)): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in sorted(tests.rglob("*.py"))},
            "source_tree_pythonpath_removed": True,
        }
        (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(process.stdout, end="")
        print(process.stderr, end="", file=sys.stderr)
        return process.returncode


if __name__ == "__main__":
    raise SystemExit(main())
