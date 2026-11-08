"""Record the bounded audit command, streams, hashes, and actual exit code."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
PYTHON = WORK / ".venv/bin/python"
SOURCE = WORK / "repo/generators/77e696585932/generator.py"
CANONICAL = WORK / "repo/shared/data/base/solutions/training/1a07d186__77e696585932.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


command = [str(PYTHON), "-B", str(WORK / "run_with_racket.py"), str(PYTHON), "-B",
           str(HERE / "rotation_probe.py"), "--out", str(HERE / "evidence.json")]
before = {str(path.relative_to(WORK)): sha(path) for path in (SOURCE, CANONICAL)}
started = time.monotonic()
environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
completed = subprocess.run(command, cwd=WORK, env=environment, capture_output=True,
                           text=True, timeout=120)
(HERE / "stdout.log").write_text(completed.stdout)
(HERE / "stderr.log").write_text(completed.stderr)
after = {str(path.relative_to(WORK)): sha(path) for path in (SOURCE, CANONICAL)}
receipt = {"schema": "arc-audit-command-receipt-v1", "command": command, "cwd": str(WORK),
           "exit_code": completed.returncode, "elapsed_seconds": round(time.monotonic()-started, 3),
           "source_before": before, "source_after": after, "source_changed": before != after,
           "probe_sha256": sha(HERE / "rotation_probe.py"),
           "recorder_sha256": sha(Path(__file__)), "stdout_sha256": sha(HERE / "stdout.log"),
           "stderr_sha256": sha(HERE / "stderr.log")}
if (HERE / "evidence.json").exists():
    receipt["evidence_sha256"] = sha(HERE / "evidence.json")
(HERE / "command_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(completed.stdout, end="")
print(completed.stderr, end="", file=sys.stderr)
print(json.dumps({"recorded_exit_code": completed.returncode,
                  "source_changed": before != after, "receipt": str(HERE / "command_receipt.json")}))
raise SystemExit(completed.returncode)
