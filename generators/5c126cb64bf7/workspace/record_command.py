"""Run an argv without a shell and retain a new, source-bound command receipt.

Usage: python record_command.py --cwd DIR --out PREFIX [--source FILE] -- ARGV...
PREFIX.log and PREFIX.json must not exist. The child exit code is propagated.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("argv", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    argv = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
    if not argv:
        parser.error("provide a child command after --")
    cwd, prefix = args.cwd.absolute(), args.out.absolute()
    log_path, receipt_path = Path(str(prefix) + ".log"), Path(str(prefix) + ".json")
    if log_path.exists() or receipt_path.exists():
        parser.error("receipt destination already exists; use a new prefix")
    prefix.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema": "review-command-receipt-v1", "argv": argv, "actual_cwd": str(cwd),
        "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_path": str(args.source.absolute()) if args.source else None,
        "source_sha256_before": digest(args.source), "exit_code": None,
        "console_log": str(log_path),
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    try:
        with log_path.open("x") as log:
            proc = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                log.write(line)
                log.flush()
                print(line, end="", flush=True)
            receipt["exit_code"] = proc.wait()
    except Exception as exc:
        receipt["launch_or_capture_error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        receipt["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        receipt["source_sha256_after"] = digest(args.source)
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
