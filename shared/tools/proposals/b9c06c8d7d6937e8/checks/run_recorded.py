"""Run a review command once and retain its exact invocation and source identity."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
CHECKS = ROOT / "WORK/checks"


def main():
    name, *argv = sys.argv[1:]
    if argv[:1] == ["--"]:
        argv = argv[1:]
    if not argv or Path(name).name != name:
        raise SystemExit("Usage: run_recorded.py UNIQUE_LABEL -- COMMAND [ARGS...]")
    log = CHECKS / (name + ".log")
    receipt = CHECKS / (name + ".command.json")
    if log.exists() or receipt.exists():
        raise SystemExit("Choose a new label; existing evidence is never overwritten.")
    assignment = json.loads((ROOT / "WORK/ASSIGNMENT.json").read_text())
    source = ROOT / "WORK/repo/generators" / assignment["task_id"] / "generator.py"
    digest = lambda: hashlib.sha256(source.read_bytes()).hexdigest()
    before = digest()
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    start = time.monotonic()
    with log.open("x") as stream:
        result = subprocess.run(argv, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
    after = digest()
    record = {
        "argv": argv,
        "cwd": "packet_root",
        "actual_cwd": str(ROOT),
        "started_utc": started,
        "exit_code": result.returncode,
        "elapsed_seconds": round(time.monotonic() - start, 3),
        "generator_sha256_before": before,
        "generator_sha256_after": after,
        "source_unchanged_during_command": before == after,
        "evidence_paths": ["checks/" + log.name],
    }
    receipt.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
