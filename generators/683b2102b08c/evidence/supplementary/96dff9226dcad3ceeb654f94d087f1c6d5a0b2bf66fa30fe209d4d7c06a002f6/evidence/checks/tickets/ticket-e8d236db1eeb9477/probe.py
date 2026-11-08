#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TICKET_ID = "ticket-e8d236db1eeb9477"
TASK_ID = "683b2102b08c"
PINNED_SHA = "9c1dd4109ccde1034db0823550fc023e9b278ab21e58461264624ec38ee53c38"
PROBE_SEED_HEX = "c1d9419f23741910e8d9e96cfeb75d755c916146831cae67ce66ae4ab18093fe"
ROOT = find_root(__file__)
OUT = Path(__file__).with_name("result.json")


def main() -> None:
    generator, source_path, source_sha = load_selected_generator(TASK_ID, root=ROOT)
    assert source_sha == PINNED_SHA
    seed = int(PROBE_SEED_HEX[:16], 16) & ((1 << 63) - 1)

    valid = generator.generate(
        seed,
        0,
        difficulty="medium",
        scene_family="linked",
    )
    valid_errors = generator.self_check(valid)
    valid_observed = generator.observe_overrides(valid)
    assert valid_errors == []
    assert valid_observed == {"scene_family": "linked"}

    invalid_error = None
    try:
        generator.generate(
            seed,
            0,
            difficulty="medium",
            scene_family="not_advertised",
        )
    except Exception as exc:  # Record the actual public behavior and type.
        invalid_error = {"type": type(exc).__name__, "message": str(exc)}
    else:
        raise AssertionError("invalid scene_family override was accepted")
    assert invalid_error["type"] == "ValueError"
    assert "scene_family" in invalid_error["message"]

    result = {
        "schema": "arcpuzzles-bounded-api-boundary-probe-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "source": {
            "path": str(source_path.relative_to(ROOT)),
            "sha256": source_sha,
        },
        "probe_seed_hex": PROBE_SEED_HEX,
        "boundary": "AXES.scene_family valid linked|generalized",
        "valid_call": {
            "kwargs": {"difficulty": "medium", "scene_family": "linked"},
            "dimensions": [len(valid), len(valid[0])],
            "self_check": valid_errors,
            "observed_overrides": valid_observed,
        },
        "invalid_call": {
            "kwargs": {
                "difficulty": "medium",
                "scene_family": "not_advertised",
            },
            "error": invalid_error,
        },
        "outcome": (
            "Advertised override boundary is enforced: the valid linked value "
            "round-trips through observe_overrides, while an out-of-domain value "
            "is rejected with a scene_family-specific ValueError."
        ),
        "safety_finding": False,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
