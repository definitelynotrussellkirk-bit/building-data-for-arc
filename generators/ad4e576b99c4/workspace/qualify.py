"""Run reproducible focused and authority checks with command receipts."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
HOME = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--count", type=int, default=250)
    parser.add_argument("--battery", action="store_true")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    python = [sys.executable, "-B"]
    jobs = [
        ("focused", python + ["-m", "pytest", str(HOME / "tests"), "-q"], 180),
        (
            "reference",
            python + [str(HOME / "workspace/reference_probe.py"), "--count", str(args.count), "--racket", "--out", str(out / "reference.json")],
            300,
        ),
    ]
    if args.battery:
        jobs.append(
            (
                "battery",
                python + ["-m", "arcpuzzles", "check", "ad4e576b99c4", "--battery", "--timeout", "4000", "--phase", "after", "--out", str(out / "battery")],
                4200,
            )
        )
    env = dict(
        os.environ,
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONPATH=os.pathsep.join([str(ROOT / "src"), str(ROOT / "shared/runtime")]),
    )
    receipt = {
        "schema": "ad4e576b99c4-qualification-v1",
        "generator_sha256": hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest(),
        "checks": [],
    }
    for name, command, timeout in jobs:
        started = time.monotonic()
        with (out / f"{name}.log").open("w", encoding="utf-8") as log:
            try:
                result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
                code, timed_out = result.returncode, False
            except subprocess.TimeoutExpired:
                code, timed_out = None, True
        receipt["checks"].append(
            {
                "name": name,
                "command": command,
                "cwd": str(ROOT),
                "started_utc": datetime.now(timezone.utc).isoformat(),
                "seconds": time.monotonic() - started,
                "exit_code": code,
                "timed_out": timed_out,
            }
        )
        receipt["passed"] = all(row["exit_code"] == 0 and not row["timed_out"] for row in receipt["checks"])
        (out / "commands.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
