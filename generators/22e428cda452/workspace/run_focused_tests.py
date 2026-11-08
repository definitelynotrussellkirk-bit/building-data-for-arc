#!/usr/bin/env python3
"""Replay this review's focused tests in the public portable runtime layout.

This helper is intentionally task-local.  It uses the public ARCpuzzles runtime
builder, copies only the focused tests and their isolated prototype into the
snapshot, and records source hashes plus the real pytest result.
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

from arcpuzzles.catalog import Catalog
from arcpuzzles.runtime import prepare_runtime


TASK_ID = "22e428cda452"
FOCUSED_TESTS = (
    f"generators/{TASK_ID}/tests/test_review_contract.py",
    f"generators/{TASK_ID}/tests/test_parametric_projection_inset.py",
)
SUPPORT_FILES = (
    f"generators/{TASK_ID}/workspace/parametric/prototype.py",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy_regular(library: Path, runtime: Path, relative: str) -> str:
    source = library / relative
    if source.is_symlink() or not source.is_file():
        raise FileNotFoundError(f"Focused-test source is not a regular file: {source}")
    target = runtime / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return _sha256(target)


def run(library: Path, output: Path | None, timeout: float) -> dict:
    catalog = Catalog(library)
    library = catalog.root
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-focused-") as directory:
        runtime = Path(directory)
        prepare_runtime(catalog, runtime, TASK_ID)
        row = catalog.describe(TASK_ID)
        generator_sha256 = _sha256(runtime / row["runtime_generator"])
        source_hashes = {
            f"generators/{TASK_ID}/generator.py": generator_sha256,
            **{
                relative: _copy_regular(library, runtime, relative)
                for relative in (*FOCUSED_TESTS, *SUPPORT_FILES)
            },
        }
        command = [sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS]
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(runtime)
        environment["ARCPUZZLES_HOME"] = str(runtime)
        completed = subprocess.run(
            command,
            cwd=runtime,
            env=environment,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        report = {
            "schema": "focused_test_replay/1",
            "task_id": TASK_ID,
            "library": str(library),
            "runtime_layout": "arcpuzzles.runtime.prepare_runtime",
            "runtime_manifest_sha256": _sha256(runtime / "RUNTIME_MANIFEST.json"),
            "generator_sha256": generator_sha256,
            "source_sha256": source_hashes,
            "argv": command,
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    if output is not None:
        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    sys.stdout.write(report["stdout"])
    sys.stderr.write(report["stderr"])
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path)
    parser.add_argument("--timeout", type=float, default=300.0)
    args = parser.parse_args()
    if not (args.timeout > 0):
        parser.error("--timeout must be positive")
    try:
        report = run(args.library, args.out, args.timeout)
    except subprocess.TimeoutExpired as exc:
        print(f"focused tests timed out after {exc.timeout} seconds", file=sys.stderr)
        return 124
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
