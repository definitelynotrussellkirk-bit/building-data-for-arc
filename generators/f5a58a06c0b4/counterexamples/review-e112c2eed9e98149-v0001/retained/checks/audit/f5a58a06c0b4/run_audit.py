"""Execute bounded audit probes and retain literal command receipts."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
PACKET = WORK.parent
REPO = WORK / "repo"
PYTHON = str(WORK / ".venv-review/bin/python")
PREFIX = [PYTHON, "-B", "review.py", "run", PYTHON, "-B"]
REL = "../checks/audit/f5a58a06c0b4/"
STEPS = [
    ("prepare", PREFIX + [REL + "probe.py", "prepare"],
     ["source_identity.json", "canonical_records.jsonl", "audited_rule.rkt", "cases.json", "input.json"]),
    ("racket", PREFIX + ["-m", "arcpuzzles", "apply", "f5a58a06c0b4", "--input", REL + "input.json", "--out", REL + "racket.json"],
     ["racket.json"]),
    ("verify", PREFIX + [REL + "probe.py", "verify"],
     ["finding.json", "lesson_medium.json", "minimal_racket_output.json", "minimal_rival_output.json"]),
]

if sys.argv[1:] == ["verify"]:
    receipts = json.loads((HERE / "command_receipts.json").read_text())
    attempt = 1 + sum(row["name"].startswith("verify") for row in receipts)
    STEPS = [(f"verify_attempt_{attempt}", STEPS[-1][1], STEPS[-1][2])]
else:
    receipts = []
for name, argv, evidence in STEPS:
    started = time.monotonic()
    proc = subprocess.run(argv, cwd=PACKET, text=True, capture_output=True)
    (HERE / f"{name}.stdout.log").write_text(proc.stdout)
    (HERE / f"{name}.stderr.log").write_text(proc.stderr)
    receipts.append({"name": name, "argv": argv, "cwd": str(PACKET),
                     "effective_payload_cwd": str(REPO), "exit_code": proc.returncode,
                     "elapsed_seconds": round(time.monotonic() - started, 3),
                     "stdout": str(HERE / f"{name}.stdout.log"),
                     "stderr": str(HERE / f"{name}.stderr.log"),
                     "retained_evidence_paths": [str(HERE / p) for p in evidence if (HERE / p).exists()]})
    (HERE / "command_receipts.json").write_text(json.dumps(receipts, indent=2) + "\n")
    print(json.dumps({"step": name, "exit_code": proc.returncode,
                      "elapsed_seconds": receipts[-1]["elapsed_seconds"]}), flush=True)
    if proc.returncode:
        print(proc.stdout[-4000:], flush=True)
        print(proc.stderr[-4000:], file=sys.stderr, flush=True)
        raise SystemExit(proc.returncode)
