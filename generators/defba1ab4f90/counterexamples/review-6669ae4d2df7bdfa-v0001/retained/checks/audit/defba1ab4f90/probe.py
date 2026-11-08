#!/usr/bin/env python3
"""Reproduce the pinned defba1ab4f90 scalar-control validation hole."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import load_selected_generator

TASK_ID = "defba1ab4f90"
EXPECTED_GENERATOR_SHA256 = "4189136b4e863e70bf07ee2466d865493554544a72273e4f3918da61da7f7c26"


def _grid_sha256(grid: Any) -> str:
    payload = json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _describe(value: Any) -> dict[str, Any]:
    return {"repr": repr(value), "type": type(value).__name__}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    generator, source_path, source_sha256 = load_selected_generator(TASK_ID)
    if source_sha256 != EXPECTED_GENERATOR_SHA256:
        raise RuntimeError(
            f"source drift: expected {EXPECTED_GENERATOR_SHA256}, got {source_sha256}"
        )

    cases = [
        ("seed", True, 0),
        ("seed", False, 0),
        ("seed", 1.0, 0),
        ("seed", 1.75, 0),
        ("seed", "1", 0),
        ("sample_index", 1, True),
        ("sample_index", 1, -1),
        ("sample_index", 1, 1.0),
        ("sample_index", 1, "1"),
    ]
    rows: list[dict[str, Any]] = []
    for axis, seed, sample_index in cases:
        row: dict[str, Any] = {
            "axis": axis,
            "seed": _describe(seed),
            "sample_index": _describe(sample_index),
        }
        try:
            profile = generator.schedule_profile(seed, sample_index)
            row["schedule_profile"] = {"status": "accepted", "value": profile}
        except Exception as error:  # pragma: no cover - retained for drift diagnosis
            row["schedule_profile"] = {
                "status": "rejected",
                "error_type": type(error).__name__,
                "message": str(error),
            }
        try:
            grid = generator.generate(seed, sample_index)
            row["generate"] = {
                "status": "accepted",
                "shape": [len(grid), len(grid[0])],
                "grid_sha256": _grid_sha256(grid),
                "self_check_errors": list(generator.self_check(grid)),
            }
        except Exception as error:  # pragma: no cover - retained for drift diagnosis
            row["generate"] = {
                "status": "rejected",
                "error_type": type(error).__name__,
                "message": str(error),
            }
        rows.append(row)

    accepted = [row for row in rows if row["generate"]["status"] == "accepted"]
    finding_reproduced = len(accepted) == len(rows) and all(
        not row["generate"]["self_check_errors"] for row in accepted
    )
    report = {
        "schema": "arcpuzzles-bounded-audit-probe-v1",
        "status": "finding" if finding_reproduced else "not_reproduced",
        "task_id": TASK_ID,
        "finding": "invalid_scalar_controls_accepted",
        "generator_path": str(source_path),
        "generator_sha256": source_sha256,
        "expected_contract": {
            "seed": "exact int, excluding bool",
            "sample_index": "exact nonnegative int, excluding bool",
        },
        "cases": rows,
        "summary": {
            "invalid_cases": len(rows),
            "accepted_by_generate": len(accepted),
            "accepted_and_self_check_clean": sum(
                not row["generate"]["self_check_errors"] for row in accepted
            ),
        },
        "impact": (
            "The public generator API silently admits booleans, floats, strings, and a "
            "negative index. Those values alias or wrap schedule roles instead of failing "
            "closed, weakening deterministic control validation and corpus identity."
        ),
        "scope": "bounded scalar-control probe only; labels and general semantics were not audited",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], **report["summary"], "out": str(args.out)}, sort_keys=True))
    return 0 if finding_reproduced else 1


if __name__ == "__main__":
    raise SystemExit(main())
