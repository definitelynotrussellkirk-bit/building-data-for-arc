#!/usr/bin/env python3
"""Revalidate a saved parametric qualification against the current exact source closure."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from arcpuzzles.catalog import Catalog, sha256
from arcpuzzles.parametric_promotion import _check_execution, _ready


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id")
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--execution", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = Path.cwd().resolve()
    qualification_path = args.qualification.resolve()
    execution_path = args.execution.resolve()
    q = json.loads(qualification_path.read_text(encoding="utf-8"))
    execution = json.loads(execution_path.read_text(encoding="utf-8"))
    contract, binding = _ready(Catalog(root), args.task_id)
    programs = _check_execution(execution, q["jobs"], binding, contract)

    checks = {
        "task_id_matches": q.get("task_id") == args.task_id,
        "status_qualified": q.get("status") == "qualified",
        "source_binding_exact": q.get("source_binding") == binding,
        "contract_exact": q.get("contract") == contract,
        "execution_sha256_exact": q.get("execution", {}).get("sha256") == sha256(execution_path),
        "programs_exact": q.get("programs") == programs,
        "training_not_admitted": q.get("training_admitted") is False,
    }
    passed = all(checks.values())
    report = {
        "schema": "arcpuzzles-parametric-qualification-recheck-v1",
        "status": "passed" if passed else "failed",
        "task_id": args.task_id,
        "checks": checks,
        "qualification_path": str(qualification_path),
        "qualification_sha256": hashlib.sha256(qualification_path.read_bytes()).hexdigest(),
        "execution_path": str(execution_path),
        "execution_sha256": hashlib.sha256(execution_path.read_bytes()).hexdigest(),
        "current_source_binding": binding,
        "programs": programs,
        "jobs": len(q["jobs"]),
        "racket_evaluations": execution.get("racket_evaluations"),
        "training_admitted": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "jobs": report["jobs"], "racket_evaluations": report["racket_evaluations"], "out": str(args.out)}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
