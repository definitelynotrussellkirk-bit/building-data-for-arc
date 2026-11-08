from __future__ import annotations

import argparse
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "8b0844e3951e"
EXPECTED_SOURCE_SHA256 = "dd29df3ec18cda8c98a1ba1f165a0b013e2e2f4519d4eb10750f528b283af5f2"
EXPECTED_RULE_HASH = "b2abbd0be28f"
PROBE_SEED = "c9c97322d0647d97d3857a4f7f404466f97094fab02ca2e21a75311b26a5ad02"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = find_root(__file__)
    generator, source, source_sha = load_selected_generator(TASK_ID, root=root)
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"source drift: {source_sha}")
    if generator.RULE_HASH != EXPECTED_RULE_HASH:
        raise RuntimeError(f"rule drift: {generator.RULE_HASH}")
    seed = int(PROBE_SEED[:16], 16)

    valid = generator.generate(seed, 0, mode_color=9)
    valid_errors = generator.self_check(valid)
    observed = generator.observe_overrides(valid)
    if valid_errors or observed.get("mode_color") != 9:
        raise AssertionError({"errors": valid_errors, "observed": observed})

    invalid = {"raised": False, "exception_type": None, "message": None}
    try:
        generator.generate(seed, 0, mode_color=0)
    except Exception as exc:
        invalid = {
            "raised": True,
            "exception_type": type(exc).__name__,
            "message": str(exc),
        }
    if not invalid["raised"]:
        raise AssertionError("mode_color=0 did not fail closed")

    result = {
        "schema": "arcpuzzles-api-boundary-v1",
        "ticket_id": "ticket-c95e020b1688bb0e",
        "type": "api_boundary",
        "task_id": TASK_ID,
        "probe_seed": PROBE_SEED,
        "numeric_seed": seed,
        "source": str(source.relative_to(root)),
        "source_sha256": source_sha,
        "rule_hash": generator.RULE_HASH,
        "axis": "mode_color",
        "declared_valid": "1..9",
        "valid_call": {
            "override": 9,
            "self_check_errors": valid_errors,
            "observed": observed,
            "grid": valid,
        },
        "invalid_call": {"override": 0, **invalid},
        "observation": "The upper boundary 9 generates and round-trips exactly; the adjacent forbidden value 0 fails closed.",
        "limits": "One valid/invalid boundary comparison; no exhaustive override matrix.",
    }
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"valid_mode_color": observed["mode_color"], "invalid_exception": invalid["exception_type"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
