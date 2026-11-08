from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from reviewer_support import find_root, load_selected_generator

TASK_ID = "298700c0dc02"
TICKET_ID = "ticket-c15fde8a98cfa2ff"
EXPECTED_SOURCE_SHA256 = "a4489292f3ac8fb3c57300cc5496f8dde0964184ae72ceb088ceb67d99c1cb8c"
EXPECTED_RULE_HASH = "7bd61d1b9182"
PROBE_SEED = "10a82ad926102e3eeb44ff2450cc1b5db5fe27d8bcf71999cd34830d12539279"
OUTPUT = Path(__file__).with_name("api-boundary.json")


def attempt(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> dict[str, Any]:
    try:
        value = fn(*args, **kwargs)
    except Exception as exc:  # The concrete exception is the boundary evidence.
        return {
            "accepted": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    return {"accepted": True, "value": value}


def main() -> int:
    root = find_root(__file__)
    generator, source, source_sha256 = load_selected_generator(TASK_ID, root=root)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(
            f"source pin mismatch: expected {EXPECTED_SOURCE_SHA256}, got {source_sha256}"
        )
    if getattr(generator, "RULE_HASH", None) != EXPECTED_RULE_HASH:
        raise RuntimeError(
            f"rule pin mismatch: expected {EXPECTED_RULE_HASH}, "
            f"got {getattr(generator, 'RULE_HASH', None)}"
        )

    seed = int(PROBE_SEED[:16], 16)
    sample_index = 1
    valid_raw = attempt(generator.generate, seed, sample_index, grid_h=9)
    if not valid_raw["accepted"]:
        valid = valid_raw
    else:
        grid = valid_raw["value"]
        valid = {
            "accepted": True,
            "requested": {"grid_h": 9},
            "observed_overrides": generator.observe_overrides(grid),
            "dimensions": [len(grid), len(grid[0])],
            "self_check": generator.self_check(grid),
            "grid_sha256": hashlib.sha256(
                json.dumps(grid, separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
        }

    invalid = attempt(generator.generate, seed, sample_index, grid_h=9.0)
    boundary_enforced = (
        valid.get("accepted") is True
        and valid.get("observed_overrides", {}).get("grid_h") == 9
        and valid.get("self_check") == []
        and invalid.get("accepted") is False
        and invalid.get("error_type") == "ValueError"
        and invalid.get("error") == "grid_h override must be an integer"
    )
    result = {
        "schema": "arcpuzzles-api-boundary-probe-v1",
        "ticket_id": TICKET_ID,
        "ticket_seed": PROBE_SEED,
        "task_id": TASK_ID,
        "source": {
            "path": source.relative_to(root).as_posix(),
            "sha256": source_sha256,
            "rule_hash": getattr(generator, "RULE_HASH", None),
        },
        "boundary": {
            "axis": "grid_h",
            "advertised_type": generator.AXES["grid_h"]["type"],
            "advertised_valid": generator.AXES["grid_h"]["valid"],
            "valid_call": valid,
            "invalid_call": {
                "requested": {"grid_h": 9.0},
                **invalid,
            },
        },
        "boundary_enforced": boundary_enforced,
        "finding": None if boundary_enforced else "advertised integer boundary was not enforced",
        "limits": [
            "One pinned source and one advertised axis were inspected.",
            "The comparison covers the valid minimum integer and the same-valued float only.",
            "No peer battery or generator source edit was performed.",
        ],
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if boundary_enforced else 1


if __name__ == "__main__":
    raise SystemExit(main())
