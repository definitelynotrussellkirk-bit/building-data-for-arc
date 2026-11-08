"""Run one audit command, retaining exact argv/cwd/exit and its output."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
name, *argv = sys.argv[1:]
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
completed = subprocess.run(argv, cwd=Path.cwd(), env=env, capture_output=True, text=True)
log = HERE / (name + ".log")
log.write_text(completed.stdout + completed.stderr)
path = HERE / "command-records.json"
records = json.loads(path.read_text()) if path.exists() else []
records.append({
    "name": name, "cwd": str(Path.cwd()), "argv": argv,
    "environment_delta": {"PYTHONDONTWRITEBYTECODE": "1"},
    "exit_code": completed.returncode,
    "evidence": str(log.relative_to(HERE)),
    "evidence_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
})
path.write_text(json.dumps(records, indent=2) + "\n")
print(completed.stdout, end="")
print(completed.stderr, end="", file=sys.stderr)
raise SystemExit(completed.returncode)
