#!/usr/bin/env python3
"""One bounded valid/invalid API boundary comparison for ticket-b2044bff4fd3ffc4."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import time
from pathlib import Path

TASK_ID = "26e0ef7cf48b"
EXPECTED_SOURCE_SHA256 = "e05c1a6b069308a67c1a233d0e242be5e3495fd043f4e6d70f4290e700ddb4b9"
SEED_HEX = "b54efaade940d601256a2f351988fdc4f7a0d43e4d2d598e3e1f64322584c9b7"
SEED = int(SEED_HEX, 16)
COMMON = {
    "difficulty": "medium",
    "grid_h": 24,
    "grid_w": 24,
    "n_markers_3": 1,
    "n_markers_4": 1,
}


def main() -> int:
    source = Path(__file__).resolve().parents[3] / "repo" / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"ticket_generator_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator source: {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"source hash mismatch: {source_sha256}")

    started = time.perf_counter()
    valid_grid = module.generate(SEED, 3, template_size=7, **COMMON)
    valid_observed = module.observe_overrides(valid_grid)
    valid_errors = module.self_check(
        valid_grid,
        meta={"overrides": {**{k: v for k, v in COMMON.items() if k != "difficulty"}, "template_size": 7}},
    )

    invalid_returned = False
    invalid_exception = None
    try:
        module.generate(SEED, 3, template_size=8, **COMMON)
        invalid_returned = True
    except Exception as exc:  # evidence captures the actual public behavior
        invalid_exception = {"type": type(exc).__name__, "message": str(exc)}
    elapsed = time.perf_counter() - started

    result = {
        "schema": "arc-review-supplementary-ticket-v1",
        "ticket_id": "ticket-b2044bff4fd3ffc4",
        "type": "api_boundary",
        "status": "completed" if not invalid_returned else "finding",
        "task_id": TASK_ID,
        "rule_hash": module.RULE_HASH,
        "source_sha256_expected": EXPECTED_SOURCE_SHA256,
        "source_sha256_observed": source_sha256,
        "probe_seed_hex": SEED_HEX,
        "probe_seed_integer": SEED,
        "sample_index": 3,
        "comparison": {
            "axis": "template_size",
            "advertised_valid_range": "3..7",
            "common_arguments": COMMON,
            "valid_call": {
                "template_size": 7,
                "returned_grid_shape": [len(valid_grid), len(valid_grid[0])],
                "observed_overrides": valid_observed,
                "self_check_errors": valid_errors,
            },
            "invalid_call": {
                "template_size": 8,
                "returned": invalid_returned,
                "exception": invalid_exception,
            },
        },
        "checks": {
            "valid_boundary_realized_exactly": valid_observed == {
                "grid_h": 24,
                "grid_w": 24,
                "template_size": 7,
                "n_markers_3": 1,
                "n_markers_4": 1,
            },
            "valid_boundary_self_check_clean": valid_errors == [],
            "invalid_boundary_rejected": not invalid_returned,
            "invalid_rejection_is_value_error": bool(invalid_exception and invalid_exception["type"] == "ValueError"),
        },
        "elapsed_seconds": elapsed,
        "summary": (
            "The advertised upper boundary template_size=7 returns a lawful 24x24 scene and is observed exactly; "
            "the adjacent invalid value 8 is rejected with ValueError."
        ),
        "limits": ["One integer axis and one adjacent invalid value were checked; other API axes were not probed."],
    }
    Path(__file__).with_name("ticket_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all(result["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
