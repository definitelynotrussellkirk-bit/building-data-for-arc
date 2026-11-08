"""Run and retain exact public apply commands for this findings-only audit."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REL = "../checks/audit/2b3472c73d30"
TASK = "2b3472c73d30"


def main():
    commands = []
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    jobs = [
        ("prepare", ["python3", "run_with_racket.py", "python3", f"{REL}/probe.py", "prepare"], ["source_metadata.json", "catalog_description.json", "input.json", "records.json", "coverage_inputs.json", "bounded_draw_observations.json"]),
        ("minimal_apply", ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK, "--input", f"{REL}/input.json", "--out", f"{REL}/racket.json"], ["racket.json"]),
        ("coverage_apply", ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK, "--input", f"{REL}/coverage_inputs.json", "--out", f"{REL}/coverage_racket.json"], ["coverage_racket.json"]),
        ("analyze", ["python3", "run_with_racket.py", "python3", f"{REL}/probe.py", "analyze"], ["comparisons.json", "findings.json"]),
    ]
    for label, argv, assets in jobs:
        started = time.time()
        process = subprocess.run(argv, cwd=WORK, env=env, capture_output=True, text=True, timeout=300)
        (HERE / f"{label}.stdout.txt").write_text(process.stdout)
        (HERE / f"{label}.stderr.txt").write_text(process.stderr)
        commands.append({"name": label, "argv": argv, "cwd": str(WORK),
                         "effective_payload_cwd": str(WORK / "repo"),
                         "environment_overrides": {"PYTHONDONTWRITEBYTECODE": "1"},
                         "exit_status": process.returncode,
                         "elapsed_seconds": round(time.time() - started, 3),
                         "stdout_path": str(HERE / f"{label}.stdout.txt"),
                         "stderr_path": str(HERE / f"{label}.stderr.txt"),
                         "evidence_paths": [str(HERE / a) for a in assets]})
        (HERE / "commands.json").write_text(json.dumps({"schema": "audit-exact-commands-v1", "orchestrator_argv": ["python3", "checks/audit/2b3472c73d30/run_probe.py"], "orchestrator_cwd": str(WORK), "commands": commands}, indent=2) + "\n")
        print(f"{label}: exit {process.returncode}", flush=True)
        if process.returncode:
            print(process.stdout, flush=True)
            print(process.stderr, file=sys.stderr, flush=True)
            return process.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
