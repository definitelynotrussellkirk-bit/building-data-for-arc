"""Run the bounded audit through public packet commands and retain receipts."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path.cwd()
BASE = ROOT / "WORK/checks/audit/c0966960e255"
OUT = BASE
if (OUT / "racket.json").exists():
    index = 1
    while (BASE / f"replay-{index}").exists():
        index += 1
    OUT = BASE / f"replay-{index}"
    OUT.mkdir()
    for filename in ("probe.py", "verify.py"):
        shutil.copyfile(BASE / filename, OUT / filename)
relative_out = "../" + str(OUT.relative_to(ROOT / "WORK"))
PREFIX = ["WORK/.venv-review/bin/python", "review.py", "run", "../.venv-review/bin/python"]
commands = [
    ("prepare", PREFIX + [relative_out + "/probe.py", "prepare"]),
    ("racket", PREFIX + ["-m", "arcpuzzles", "apply", "c0966960e255", "--input", relative_out + "/input.json", "--out", relative_out + "/racket.json"]),
    ("verify", PREFIX + [relative_out + "/verify.py"]),
]
print(f"Evidence directory: {OUT.relative_to(ROOT)}", flush=True)
receipts = []
for name, argv in commands:
    completed = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    (OUT / f"{name}.log").write_text(completed.stdout + completed.stderr)
    receipts.append({
        "name": name, "cwd": "packet_root", "actual_cwd": str(ROOT), "argv": argv,
        "exit_code": completed.returncode,
        "evidence_paths": [str((OUT / f"{name}.log").relative_to(ROOT))],
    })
    (OUT / "commands.json").write_text(json.dumps(receipts, indent=2) + "\n")
    print(f"{name}: exit {completed.returncode}", flush=True)
    if completed.returncode:
        print(completed.stdout[-1000:] + completed.stderr[-1000:])
        raise SystemExit(completed.returncode)
