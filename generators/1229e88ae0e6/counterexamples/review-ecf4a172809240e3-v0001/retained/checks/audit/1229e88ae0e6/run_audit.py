"""Replay the compact audit through the packet entry point; retain commands."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

OUT = Path(__file__).resolve().parent
PACKET = Path(__file__).resolve().parents[4]
REPO = PACKET / "WORK/repo"
PAYLOAD = "../checks/audit/1229e88ae0e6"


def main():
    verify_existing = sys.argv[1:] == ["--verify-existing"]
    if sys.argv[1:] and not verify_existing:
        raise SystemExit("Usage: run_audit.py [--verify-existing]")
    if (OUT / "racket.json").exists() and not verify_existing:
        raise SystemExit("Preserve current evidence: run with --verify-existing to verify "
                         "retained labels, or replay in a relocated packet without prior audit outputs.")
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    steps = [
        ("scan", ["python3", "-B", f"{PAYLOAD}/reprobe.py", "scan"]),
        ("racket", ["python3", "-B", "-m", "arcpuzzles", "apply", "1229e88ae0e6",
                    "--input", f"{PAYLOAD}/input.json", "--out", f"{PAYLOAD}/racket.json",
                    "--check-generator-domain"]),
        ("verify", ["python3", "-B", f"{PAYLOAD}/reprobe.py", "verify"]),
    ]
    if verify_existing:
        records = json.loads((OUT / "commands.json").read_text())["commands"]
        verification_number = 1 + sum(row["label"].startswith("verify") for row in records)
        steps = [(f"verify-v{verification_number}", steps[-1][1])]
    else:
        records = []
    for label, payload in steps:
        argv = ["python3", "review.py", "run", *payload]
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        clock = time.monotonic()
        proc = subprocess.run(argv, cwd=PACKET, env=env, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (OUT / f"{label}.stdout.txt").write_text(proc.stdout)
        (OUT / f"{label}.stderr.txt").write_text(proc.stderr)
        records.append({"label": label, "argv": argv, "cwd": str(PACKET),
                        "payload_argv": payload, "payload_cwd": str(REPO),
                        "environment_overrides": {"PYTHONDONTWRITEBYTECODE": "1"},
                        "audit_probe_sha256": hashlib.sha256((OUT / "reprobe.py").read_bytes()).hexdigest(),
                        "started_utc": started, "elapsed_seconds": round(time.monotonic()-clock, 3),
                        "exit_code": proc.returncode,
                        "stdout_path": f"{label}.stdout.txt", "stderr_path": f"{label}.stderr.txt"})
        sources = {}
        if (OUT / "census.json").exists():
            census_binding = json.loads((OUT / "census.json").read_text())["binding"]
            sources = {key: census_binding[key] for key in (
                "generator_sha256", "generator_declared_rule_hash", "canonical_rule_text_sha256",
                "canonical_row_sha256_without_newline", "canonical_ledger_sha256")}
        if (OUT / "racket.json").exists():
            authority = json.loads((OUT / "racket.json").read_text())
            sources["executed_rule_hash"] = authority["executed_rule_hash"]
            sources["executed_callable_sha256"] = authority["rule_text_sha256"]
        (OUT / "commands.json").write_text(json.dumps({
            "schema": "centering-audit-commands-v1", "task_id": "1229e88ae0e6",
            "launcher_argv": sys.orig_argv, "launcher_cwd": os.getcwd(), "source_bindings": sources,
            "commands": records}, indent=2) + "\n")
        print(json.dumps({"step": label, "exit_code": proc.returncode,
                          "elapsed_seconds": records[-1]["elapsed_seconds"]}), flush=True)
        if proc.returncode:
            print(proc.stderr[-3000:], file=sys.stderr)
            return proc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
