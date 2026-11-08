"""Replay the retained audit using only public review wrapper commands."""
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
PACKET = WORK.parent
TARGET = "7e7614405852"
REL = f"checks/audit/{TARGET}"
PREFIX = ["python3", "review.py", "run", "python3"]
STEPS = {
    "prepare": (PREFIX + [f"../{REL}/probe.py", "prepare"], ["input.json", "fixtures.json", "bindings.json", "canonical_record.json"]),
    "apply": (PREFIX + ["-m", "arcpuzzles", "apply", TARGET,
                         "--input", f"../{REL}/input.json",
                         "--out", f"../{REL}/racket.json",
                         "--check-generator-domain"], ["racket.json"]),
    "compare": (PREFIX + [f"../{REL}/probe.py", "compare"], ["probe_report.json"]),
}


def main(step):
    argv, artifacts = STEPS[step]
    done = subprocess.run(argv, cwd=PACKET, text=True, capture_output=True)
    (HERE / f"{step}.log").write_text(done.stdout + done.stderr)
    path = HERE / "command_receipts.json"
    rows = json.loads(path.read_text()) if path.exists() else []
    rows.append({
        "name": f"audit-{TARGET}-{step}", "argv": argv,
        "cwd": "packet_root", "invocation_cwd": str(PACKET),
        "actual_cwd": str(WORK / "repo"), "exit_code": done.returncode,
        "evidence_paths": [f"{REL}/{name}" for name in [f"{step}.log", *artifacts]],
    })
    path.write_text(json.dumps(rows, indent=2) + "\n")
    print(done.stdout, end="")
    print(done.stderr, end="", file=sys.stderr)
    raise SystemExit(done.returncode)


if __name__ == "__main__":
    main(sys.argv[1])
