"""Replay only the selected eight-test file in the task-test runtime layout.

Run through the packet wrapper. This uses the real task snapshot and import
preflight but unittest as the runner, so it does not claim a pytest stage pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from arcpuzzles import Catalog
from arcpuzzles.runtime import (
    _task_test_import_diagnostics,
    _task_test_snapshot,
    prepare_runtime,
)
from reviewer_support import find_root

TASK = "cbf77aa253ac"
TEST = f"generators/{TASK}/tests/test_generator_{TASK}.py"
parser = argparse.ArgumentParser()
parser.add_argument("label")
args = parser.parse_args()
repository = find_root(__file__)
evidence = Path(__file__).resolve().parent

with tempfile.TemporaryDirectory(prefix="cbf77aa253ac-portable-") as temporary:
    runtime = Path(temporary)
    catalog = Catalog(repository)
    manifest = prepare_runtime(catalog, runtime, TASK)
    selected = _task_test_snapshot(catalog, runtime, manifest, TASK)
    diagnostics = _task_test_import_diagnostics(runtime, [TEST])
    command = [sys.executable, "-m", "unittest", "discover", "-s",
               str(Path(TEST).parent), "-p", Path(TEST).name, "-v"]
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env["PYTHONNOUSERSITE"] = "1"
    result = subprocess.run(command, cwd=runtime, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=120)
    log = evidence / f"{args.label}.log"
    log.write_text(result.stdout)
    ran = re.search(r"Ran (\d+) tests? in", result.stdout)
    counts = None
    if ran:
        failed = re.search(r"FAILED \(([^)]*)\)", result.stdout)
        skipped = re.search(r"OK \(skipped=(\d+)\)", result.stdout)
        totals = {"tests": int(ran.group(1)), "failed": 0, "errors": 0,
                  "skipped": int(skipped.group(1)) if skipped else 0}
        if failed:
            for key, number in re.findall(r"(failures|errors|skipped)=(\d+)", failed.group(1)):
                totals[{"failures": "failed"}.get(key, key)] = int(number)
        totals["passed"] = totals["tests"] - sum(totals[key] for key in ("failed", "errors", "skipped"))
        counts = totals
    selected_bindings = [item for item in manifest["files"]
                         if item["library_path"] in (TEST, f"generators/{TASK}/generator.py")
                         or item["library_path"] == "shared/data/canonical/puzzles.jsonl"
                         or item["runtime_path"].startswith("data/base/solutions/")]
    report = {"task_id": TASK, "runner": "unittest", "command": command,
              "runtime_path": str(runtime), "exit_code": result.returncode,
              "passed": result.returncode == 0, "test_counts": counts,
              "test_path": TEST, "task_test_selected_roots": selected,
              "test_import_diagnostics": diagnostics,
              "source_bindings": selected_bindings,
              "python_no_user_site": True, "pythonpath": None,
              "log": log.name,
              "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
              "limitation": "Focused unittest execution; not the pytest task_tests aggregate stage."}
    (evidence / f"{args.label}.json").write_text(json.dumps(report, indent=2) + "\n")
    print(result.stdout)
    print(json.dumps({key: report[key] for key in ("exit_code", "test_counts", "test_import_diagnostics")}))
    raise SystemExit(result.returncode)
