#!/usr/bin/env python3
"""Source-bound probe for invalid scalar generator-call inputs.

Run from WORK/repo through run_with_racket.py so the generator imports the
same runtime helpers used by public checks. The report is evidence only: it
records whether values that should fail closed were accepted.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, task_id: str):
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grid_digest(value: Any) -> str | None:
    if not isinstance(value, list):
        return None
    raw = json.dumps(value, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(raw).hexdigest()


def shape(value: Any) -> list[int] | None:
    if not isinstance(value, list) or not value or not isinstance(value[0], list):
        return None
    return [len(value), len(value[0])]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    repo = Path.cwd().resolve()
    source = repo / "generators" / args.task_id / "generator.py"
    if not source.is_file():
        raise SystemExit(f"missing selected generator: {source}")
    module = load_module(source, args.task_id)

    # These are invalid under the review generator-call contract: booleans are
    # not integer seeds/indices; floats and strings are not integers; indices
    # must be nonnegative.
    cases = [
        ("seed_bool", True, 0),
        ("seed_float", 1.5, 0),
        ("seed_string", "1", 0),
        ("sample_index_bool", 0, True),
        ("sample_index_negative", 0, -1),
        ("sample_index_float", 0, 1.5),
        ("sample_index_string", 0, "1"),
    ]
    observations: list[dict[str, Any]] = []
    for name, seed, sample_index in cases:
        row: dict[str, Any] = {
            "case": name,
            "seed_repr": repr(seed),
            "sample_index_repr": repr(sample_index),
            "expected": "reject",
        }
        try:
            result = module.generate(seed, sample_index)
        except Exception as exc:  # noqa: BLE001 - the exception is evidence
            row.update(
                {
                    "observed": "rejected",
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                }
            )
        else:
            check_errors = module.self_check(result) if hasattr(module, "self_check") else None
            row.update(
                {
                    "observed": "accepted",
                    "grid_shape": shape(result),
                    "grid_sha256": grid_digest(result),
                    "self_check_errors": check_errors,
                }
            )
        observations.append(row)

    accepted = [row["case"] for row in observations if row["observed"] == "accepted"]
    report = {
        "schema": "generator-call-contract-probe-v1",
        "task_id": args.task_id,
        "source_path": source.relative_to(repo).as_posix(),
        "generator_sha256": sha256(source),
        "declared_version": getattr(module, "VERSION", None),
        "declared_rule_hash": getattr(module, "RULE_HASH", None),
        "working_directory": str(repo),
        "command": [
            "python3",
            "../checks/audit/call_contract_probe.py",
            args.task_id,
            "--out",
            args.out.as_posix(),
        ],
        "contract": {
            "seed": "literal int, not bool",
            "sample_index": "literal nonnegative int, not bool",
        },
        "observations": observations,
        "accepted_invalid_cases": accepted,
        "verdict": "FAIL" if accepted else "PASS",
        "finding": (
            f"generator accepted {len(accepted)}/{len(observations)} invalid scalar calls"
            if accepted
            else "all invalid scalar calls were rejected"
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"task_id": args.task_id, "verdict": report["verdict"], "accepted": accepted}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
