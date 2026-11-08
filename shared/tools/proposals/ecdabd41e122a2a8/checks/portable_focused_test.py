"""Replay selected existing task tests in a native isolated runtime snapshot.

This is a focused portability check, not the complete task_tests stage. No
source checkout is added to the child import path; the copied source identities,
preflight diagnostics, exact command and pytest result are retained compactly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

from arcpuzzles import Catalog
from arcpuzzles.runtime import prepare_runtime, run_process, _task_test_import_diagnostics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True)
    parser.add_argument("--test", required=True)
    parser.add_argument("--select", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    source = Path(args.test)
    if source.is_absolute() or ".." in source.parts or not source.as_posix().startswith(f"generators/{args.task}/tests/"):
        raise ValueError("Choose an explicit test inside the selected task")
    catalog = Catalog(".")
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-focused-portable-") as temporary:
        stage = Path(temporary) / "runtime"
        snapshot = prepare_runtime(catalog, stage, args.task)
        match = [item for item in snapshot["files"] if item["library_path"] == source.as_posix()]
        if len(match) != 1:
            raise ValueError("Expected exactly one native mapping for selected existing test")
        test_path = match[0]["runtime_path"]
        diagnostics = _task_test_import_diagnostics(stage, [test_path])
        errors = [item for item in diagnostics if item["severity"] == "error"]
        command = [sys.executable, "-m", "pytest", "--import-mode=importlib", test_path,
                   "-q", "-k", args.select]
        result = ({"exit_code": 2, "stdout": "", "stderr": "Native preflight failed", "timed_out": False}
                  if errors else run_process(command, stage, timeout=60, extra_env={
                      "PYTHONPATH": os.pathsep.join(str(stage / name) for name in (".", "src", "scripts", "shared/runtime")),
                      "ARCPUZZLES_HOME": str(stage), "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"}))
        report = {
            "schema": "arcpuzzles-focused-portability-check-v1", "task_id": args.task,
            "status": "passed" if result["exit_code"] == 0 and not result.get("timed_out") else "failed",
            "scope": "Only the selected existing test functions in a fresh native runtime; not the full task_tests stage or generator battery.",
            "source_test": source.as_posix(), "source_test_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "generator_sha256": catalog.describe(args.task)["generator_sha256"],
            "snapshot_manifest_sha256": hashlib.sha256((stage / "RUNTIME_MANIFEST.json").read_bytes()).hexdigest(),
            "snapshot_file_count": len(snapshot["files"]), "test_mapping": match[0],
            "native_preflight_diagnostics": diagnostics,
            "child_import_scope": "Native snapshot paths only; no source or predecessor checkout in PYTHONPATH.",
            "argv": ["python3", *command[1:]], "result": result,
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "test": report["source_test"],
                      "diagnostics": len(diagnostics), "out": str(args.out)}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
