#!/usr/bin/env python3
"""Replay the three focused commands in a fresh output directory; preserve all logs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-root", required=True, type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root, out = args.packet_root.resolve(), args.out_dir.resolve()
    work, repo = root / "WORK", root / "WORK/repo"
    out.mkdir(parents=True, exist_ok=True)
    if (out / "command_receipts.json").exists():
        raise FileExistsError("Use --out-dir with a fresh directory for a replay.")
    script = Path(__file__).resolve().with_name("audit_probe.py")
    import os
    script_arg, out_arg = os.path.relpath(script, repo), os.path.relpath(out, repo)
    payloads = [
        ("prepare", ["python3", script_arg, "prepare", "--out-dir", out_arg], ["input.json", "probe.json"]),
        ("racket", ["python3", "-m", "arcpuzzles", "apply", "e1d032e35937", "--input", out_arg + "/input.json",
                    "--out", out_arg + "/racket.json"], ["racket.json"]),
        ("compare", ["python3", script_arg, "compare", "--out-dir", out_arg], ["comparison.json", "counterexample.json"]),
    ]
    commands = []
    for label, payload, outputs in payloads:
        argv = ["python3", "review.py", "run", *payload]
        stdout, stderr = out / f"{label}.stdout.txt", out / f"{label}.stderr.txt"
        started = time.time()
        timed_out = False
        with stdout.open("w") as out_handle, stderr.open("w") as err_handle:
            try:
                run = subprocess.run(argv, cwd=root, stdout=out_handle, stderr=err_handle, timeout=240)
                exit_code = run.returncode
            except subprocess.TimeoutExpired:
                timed_out, exit_code = True, None
        paths = [stdout, stderr, *(out / name for name in outputs)]
        commands.append({"cwd": "packet_root", "actual_cwd": str(root),
                         "effective_payload_cwd": str(repo), "argv": argv,
                         "exit_code": exit_code, "timed_out": timed_out,
                         "elapsed_seconds": round(time.time() - started, 3),
                         "evidence_paths": [str(path.relative_to(work)) for path in paths if path.exists()]})
        (out / "command_receipts.json").write_text(json.dumps(commands, indent=2) + "\n")
        print(json.dumps({"command": label, "exit_code": exit_code, "timed_out": timed_out}), flush=True)
        print(stdout.read_text(), end="", flush=True)
        if exit_code != 0:
            print(stderr.read_text(), end="", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
