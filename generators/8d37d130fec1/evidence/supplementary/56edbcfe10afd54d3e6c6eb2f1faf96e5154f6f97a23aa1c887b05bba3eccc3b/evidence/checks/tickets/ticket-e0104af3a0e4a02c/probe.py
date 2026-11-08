#!/usr/bin/env python3
"""One minimal valid/invalid comparison for the scene_profile override."""
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "8d37d130fec1"
TICKET_ID = "ticket-e0104af3a0e4a02c"
EXPECTED_SOURCE_SHA256 = "6e61c3c5b80429cb09349f8f40dcb0aeb62ff5e1f3f0a8a4884170ba0d002c43"
EXPECTED_RULE_HASH = "78df4fde8dc3"
PROBE_SEED_HEX = "0ea9582c4fece7cd6fe874e031fc8b7f65c78889550c960528f0e662f9817825"
VALID_PROFILE = "two_first_2x2"
INVALID_PROFILE = "two-first-2x2"


def main() -> None:
    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"source drift: {source_sha256}")
    if generator.RULE_HASH != EXPECTED_RULE_HASH:
        raise RuntimeError(f"rule hash drift: {generator.RULE_HASH}")

    seed = int(PROBE_SEED_HEX[:8], 16)
    valid_grid = generator.generate(
        seed, 0, difficulty="easy", scene_profile=VALID_PROFILE
    )
    valid_errors = generator.self_check(valid_grid)
    observed = generator.observe_overrides(valid_grid)

    invalid_exception = None
    try:
        generator.generate(seed, 0, difficulty="easy", scene_profile=INVALID_PROFILE)
    except Exception as exc:  # retain exact current API behavior
        invalid_exception = {"type": type(exc).__name__, "message": str(exc)}

    result = {
        "schema": "arcpuzzles-api-boundary-probe-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "source_path": str(source_path.relative_to(root)),
        "source_sha256": source_sha256,
        "rule_hash": generator.RULE_HASH,
        "probe_seed": PROBE_SEED_HEX,
        "targeted_probe_count": 1,
        "boundary": "scene_profile override membership in SCENE_PROFILES",
        "valid_call": {
            "scene_profile": VALID_PROFILE,
            "returned_shape": [len(valid_grid), len(valid_grid[0])],
            "self_check_errors": valid_errors,
            "observed_overrides": observed,
        },
        "invalid_call": {
            "scene_profile": INVALID_PROFILE,
            "exception": invalid_exception,
        },
        "checks": {
            "valid_profile_advertised": VALID_PROFILE in generator.SCENE_PROFILES,
            "valid_call_passes_self_check": valid_errors == [],
            "valid_call_round_trips": observed == {"scene_profile": VALID_PROFILE},
            "invalid_profile_not_advertised": INVALID_PROFILE not in generator.SCENE_PROFILES,
            "invalid_call_rejected_with_value_error": (
                invalid_exception is not None
                and invalid_exception["type"] == "ValueError"
                and "unknown scene_profile" in invalid_exception["message"]
            ),
        },
        "outcome": (
            "advertised scene_profile override boundary is enforced: one valid "
            "profile round-trips and one near-spelling invalid profile is rejected"
        ),
    }
    if not all(result["checks"].values()):
        raise AssertionError(json.dumps(result["checks"], sort_keys=True))
    out = Path(__file__).with_name("result.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "pass", "result": str(out), "checks": result["checks"]}, sort_keys=True))


if __name__ == "__main__":
    main()
