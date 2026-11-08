#!/usr/bin/env python3
"""One source-bound valid/invalid override comparison for ticket-c641d73790e4993e."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TICKET_ID = "ticket-c641d73790e4993e"
TASK_ID = "86e4139d27c1"
TICKET_SEED = "97f2e12ce43770bc1366ddbb80fd643aa6776a45c8226f6be8886f03e28d729c"
EXPECTED_SOURCE_SHA256 = "1c4dfca9395cf2159e1f43e6cfb458dea28fa900b529596efd2a3ddf292cb8d4"
VALID_PROFILE = "odd_floor"
INVALID_PROFILE = "odd-floor"


def grid_sha256(grid: list[list[int]]) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    root = find_root(__file__)
    module, source_path, actual_sha256 = load_selected_generator(TASK_ID, root=root)
    derived_seed = int(TICKET_SEED[:16], 16)
    sample_index = int(TICKET_SEED[16:24], 16) % 10_000
    common = {
        "seed": derived_seed,
        "sample_index": sample_index,
        "difficulty": "medium",
    }

    valid_grid = module.generate(
        derived_seed,
        sample_index,
        difficulty="medium",
        scene_profile=VALID_PROFILE,
    )
    valid_observed = module.observe_overrides(valid_grid)
    valid_errors = module.self_check(valid_grid)
    valid_analysis = module._analysis(valid_grid)

    invalid_exception = None
    invalid_returned = False
    try:
        module.generate(
            derived_seed,
            sample_index,
            difficulty="medium",
            scene_profile=INVALID_PROFILE,
        )
        invalid_returned = True
    except Exception as exc:  # exact type/message are the evidence
        invalid_exception = {"type": type(exc).__name__, "message": str(exc)}

    boundary_holds = bool(
        actual_sha256 == EXPECTED_SOURCE_SHA256
        and valid_observed == {"scene_profile": VALID_PROFILE}
        and valid_errors == []
        and valid_analysis.get("scene_profile") == VALID_PROFILE
        and not invalid_returned
        and invalid_exception
        and invalid_exception["type"] == "ValueError"
        and "unknown scene_profile" in invalid_exception["message"]
    )
    report = {
        "schema": "arcpuzzles-ticket-api-boundary-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "rule_hash": module.RULE_HASH,
        "ticket_seed": TICKET_SEED,
        "seed_derivation": "seed=int(ticket_seed[:16],16); sample_index=int(ticket_seed[16:24],16)%10000",
        "source": {
            "path": str(source_path.relative_to(root)),
            "expected_sha256": EXPECTED_SOURCE_SHA256,
            "actual_sha256": actual_sha256,
            "matches": actual_sha256 == EXPECTED_SOURCE_SHA256,
        },
        "axis": {
            "name": "scene_profile",
            "advertised": module.AXES["scene_profile"],
        },
        "common_call": common,
        "valid_call": {
            "scene_profile": VALID_PROFILE,
            "returned": True,
            "shape": [len(valid_grid), len(valid_grid[0])],
            "grid_sha256": grid_sha256(valid_grid),
            "observe_overrides": valid_observed,
            "self_check": valid_errors,
            "analyzed_scene_profile": valid_analysis.get("scene_profile"),
        },
        "invalid_call": {
            "scene_profile": INVALID_PROFILE,
            "returned": invalid_returned,
            "exception": invalid_exception,
        },
        "conclusion": {
            "boundary_holds": boundary_holds,
            "summary": (
                "The advertised exact scene_profile value is observable and lawful; "
                "a near-miss spelling raises ValueError instead of coercing or falling back."
            ),
        },
    }
    out = Path(__file__).with_name("result.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ticket_id": TICKET_ID, "boundary_holds": boundary_holds, "result": str(out)}, sort_keys=True))
    return 0 if boundary_holds else 1


if __name__ == "__main__":
    raise SystemExit(main())
