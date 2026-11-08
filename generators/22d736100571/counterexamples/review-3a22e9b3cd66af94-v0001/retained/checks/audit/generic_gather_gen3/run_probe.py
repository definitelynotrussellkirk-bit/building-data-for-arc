#!/usr/bin/env python3
"""Run the focused audit command and retain exact stdout/stderr/return code."""
import json
from pathlib import Path
import subprocess
import sys

HOME = Path(__file__).resolve().parent
WORK = HOME.parents[2]
mode = sys.argv[1]
argv = ["python3", "run_with_racket.py", "python3",
        "../checks/audit/generic_gather_gen3/probe.py", mode, *sys.argv[2:]]
run = subprocess.run(argv, cwd=WORK, capture_output=True, text=True)
stem = f"{mode}-execution"
stdout, stderr = HOME / f"{stem}.stdout", HOME / f"{stem}.stderr"
stdout.write_text(run.stdout)
stderr.write_text(run.stderr)
paths = [stdout.relative_to(WORK).as_posix(), stderr.relative_to(WORK).as_posix()]
paths += [f"checks/audit/generic_gather_gen3/{name}" for name in
          (["search-report.json", "search-witness.json"] if mode == "search"
           else ["verification.json", "racket-episode.json", "input.json", "racket-output.json", "rival-output.json"])
          if (HOME / name).exists()]
record = {"cwd": "packet_root", "argv": argv, "exit_code": run.returncode,
          "evidence_paths": paths}
records_path = HOME / "commands.json"
records = json.loads(records_path.read_text()) if records_path.exists() else []
records.append(record)
records_path.write_text(json.dumps(records, indent=2) + "\n")
print(run.stdout, end="")
print(run.stderr, end="", file=sys.stderr)
print(json.dumps({"exit_code": run.returncode, "evidence_paths": paths}))
raise SystemExit(run.returncode)
