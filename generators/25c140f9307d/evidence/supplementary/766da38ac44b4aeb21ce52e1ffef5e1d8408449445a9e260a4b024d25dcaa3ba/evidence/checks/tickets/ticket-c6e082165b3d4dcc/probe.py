#!/usr/bin/env python3
"""One source-bound valid/invalid comparison for the advertised rect_size axis."""
from __future__ import annotations

import hashlib
import json
import traceback
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "25c140f9307d"
TICKET_ID = "ticket-c6e082165b3d4dcc"
PINNED_SOURCE_SHA256 = "524e9f948170fd75c7c84e708165d6ebc2da759753f5b0f77f410d3e4ffbb19b"
PINNED_RULE_HASH = "fafb0679bd1e"
PROBE_SEED = "3408f4cc41f80e32f0d0240072f6d3e84d167b5bd0422249b6da6ee781f61a6f"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def grid_sha(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def capture(module, seed: int, rect_size: int):
    try:
        grid = module.generate(seed, 0, difficulty="medium", rect_size=rect_size)
    except Exception as exc:
        return {
            "rect_size": rect_size,
            "accepted": False,
            "exception_type": type(exc).__name__,
            "exception": str(exc),
        }
    return {
        "rect_size": rect_size,
        "accepted": True,
        "shape": [len(grid), len(grid[0])],
        "grid_sha256": grid_sha(grid),
        "self_check": module.self_check(grid, difficulty="medium"),
        "grid": grid,
    }


def main() -> int:
    report = {
        "schema": "arc-supplementary-api-boundary-v1",
        "ticket_id": TICKET_ID,
        "type": "api_boundary",
        "task_id": TASK_ID,
        "consumer": "target_current_audit",
        "probe_seed": PROBE_SEED,
        "seed_derivation": "int(probe_seed[:16], 16)",
        "targeted_probe_count": 1,
        "rule_hash": PINNED_RULE_HASH,
        "comparison": "advertised valid rect_size=5 versus invalid rect_size=4",
    }
    try:
        module, source_path, source_sha = load_selected_generator(TASK_ID, root=ROOT)
        if source_sha != PINNED_SOURCE_SHA256:
            raise ValueError(f"pinned source mismatch: {source_sha}")
        seed = int(PROBE_SEED[:16], 16)
        valid = capture(module, seed, 5)
        invalid = capture(module, seed, 4)
        if not valid.get("accepted") or valid.get("self_check"):
            raise AssertionError(f"valid comparison call failed: {valid}")
        ignored_invalid = (
            invalid.get("accepted") is True
            and invalid.get("self_check") == []
            and invalid.get("grid_sha256") == valid.get("grid_sha256")
        )
        report.update({
            "status": "finding" if ignored_invalid else "completed",
            "summary": (
                "The advertised rect_size boundary is not enforced: invalid rect_size=4 is accepted, "
                "passes self_check, and returns exactly the same grid as valid rect_size=5."
                if ignored_invalid else
                "The invalid rect_size=4 call was rejected or observably differed from valid rect_size=5."
            ),
            "source": {"path": str(source_path.relative_to(ROOT)), "sha256": source_sha},
            "actual_seed": seed,
            "sample_index": 0,
            "difficulty": "medium",
            "advertised_axis": module.AXES.get("rect_size"),
            "valid": valid,
            "invalid": invalid,
            "contract_satisfied": not ignored_invalid,
            "impact": "Override/API contract and reproducibility; this probe does not establish an incorrect Racket label.",
            "limitations": [
                "One valid/invalid comparison at one pinned seed; no other axis or seed was tested.",
                "The peer source was not modified and remains unapproved by this probe.",
            ],
        })
    except Exception as exc:
        report.update({
            "status": "unknown",
            "summary": f"Bounded API comparison could not complete: {type(exc).__name__}: {exc}",
            "error": traceback.format_exc(),
        })
    (HERE / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: report.get(k) for k in ("ticket_id", "status", "summary")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
