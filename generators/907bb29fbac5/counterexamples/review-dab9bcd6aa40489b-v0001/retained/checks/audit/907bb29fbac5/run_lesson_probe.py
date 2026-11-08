#!/usr/bin/env python3
"""Log the adaptive follow-up on a single concrete shortcut hypothesis."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
RECEIPT = HERE / "commands.json"


def run(name, argv, evidence):
    receipt = json.loads(RECEIPT.read_text())
    outpath, errpath = HERE / f"{name}.stdout.log", HERE / f"{name}.stderr.log"
    started = datetime.now(timezone.utc).isoformat()
    with outpath.open("w") as out, errpath.open("w") as err:
        result = subprocess.run(argv, cwd=PACKET, stdout=out, stderr=err)
    receipt["commands"].append({
        "command": shlex.join(argv), "argv": argv, "cwd": str(PACKET),
        "effective_payload_cwd": str(PACKET / "repo") if "run_with_racket.py" in argv else str(PACKET),
        "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
        "exit_status": result.returncode,
        "stdout": str(outpath.relative_to(PACKET)), "stderr": str(errpath.relative_to(PACKET)),
        "evidence": [f"checks/audit/907bb29fbac5/lesson/{f}" for f in evidence],
    })
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"{name}: exit {result.returncode}; {outpath.relative_to(PACKET)}", flush=True)
    if result.returncode:
        sys.exit(result.returncode)


run("lesson_search", ["python3", "checks/audit/907bb29fbac5/lesson_probe.py", "search"],
    ["search.json", "input.json", "rival.json", "independent_xor.json", "domain_validation.json"])
seed = json.loads((HERE / "lesson/search.json").read_text())["selected"]["seed"]
run("lesson_generate", ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "generate",
    "907bb29fbac5", "--count", "1", "--seed", str(seed), "--sample-index", "0",
    "--difficulty", "hard", "--train", "3", "--test", "1", "--allow-unapproved",
    "--out", "../checks/audit/907bb29fbac5/lesson/episode.jsonl"], ["episode.jsonl"])
run("lesson_apply", ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply",
    "907bb29fbac5", "--input", "../checks/audit/907bb29fbac5/lesson/input.json",
    "--out", "../checks/audit/907bb29fbac5/lesson/racket.json"], ["racket.json"])
run("lesson_compare", ["python3", "checks/audit/907bb29fbac5/lesson_probe.py", "compare"],
    ["comparison.json"])
