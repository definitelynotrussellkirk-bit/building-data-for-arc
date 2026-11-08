"""Run a review.py payload check and retain packet-compatible execution records."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

WORK = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--label", required=True)
parser.add_argument("command", nargs=argparse.REMAINDER)
args = parser.parse_args()
if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", args.label):
    parser.error("label must contain only letters, digits, underscores or hyphens")
command = args.command[1:] if args.command[:1] == ["--"] else args.command
if len(command) < 4 or command[:3] != ["python3", "review.py", "run"]:
    parser.error("supply python3 review.py run PAYLOAD after --")
log = WORK / "checks/logs" / (args.label + ".txt")
if log.exists():
    parser.error("choose a fresh label after changing source")
log.parent.mkdir(parents=True, exist_ok=True)
assignment = json.loads((WORK / "ASSIGNMENT.json").read_text())
home = WORK / "repo/generators" / assignment["task_id"]
files = [home / "generator.py"] + sorted((home / "workspace/parametric").glob("*.py"))
files += sorted((home / "tests").glob("test_parametric_*.py"))
hashes = {p.relative_to(WORK).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
start = time.monotonic()
p = subprocess.run(command, cwd=WORK.parent, text=True, capture_output=True)
log.write_text(p.stdout + p.stderr)
row = {"argv": command[3:], "cwd": "repo", "exit_code": p.returncode,
       "launcher": {"argv": command, "cwd": str(WORK.parent)},
       "duration_seconds": round(time.monotonic() - start, 3),
       "evidence_paths": [log.relative_to(WORK).as_posix()], "source_sha256": hashes}
result_path = WORK / "RESULTS.json"
results = json.loads(result_path.read_text())
results.setdefault("verification_commands", []).append(row)
result_path.write_text(json.dumps(results, sort_keys=True, indent=2) + "\n")
print(p.stdout, end="")
print(p.stderr, end="", file=sys.stderr)
raise SystemExit(p.returncode)
