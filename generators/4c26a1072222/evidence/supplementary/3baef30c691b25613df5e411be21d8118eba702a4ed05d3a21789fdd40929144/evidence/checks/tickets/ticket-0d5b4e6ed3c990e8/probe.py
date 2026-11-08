#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import time

from reviewer_support import find_root

EXPECTED_SOURCE_SHA256 = "c55bd10cff6e9f5846e33302b895c6316effa805d46c5b85f77bcdcbd1d99580"
TASK_ID = "4c26a1072222"
PROBE_SEED_HEX = "f853fc9340ae5c8c242af93efa047f593cbc2f7f01455292e2aabe64465502a3"


def main() -> None:
    started = time.monotonic()
    root = find_root(__file__)
    source = root / "generators" / TASK_ID / "generator.py"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if source_hash != EXPECTED_SOURCE_SHA256:
        raise AssertionError(f"source hash drift: {source_hash}")

    spec = importlib.util.spec_from_file_location("ticket_api_boundary_4c26a1072222", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load pinned generator")
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)

    seed = int(PROBE_SEED_HEX[:16], 16)
    valid_grid = generator.generate(
        seed,
        0,
        difficulty="medium",
        n_bands=4,
        first_transform="anti_transpose",
    )
    valid_errors = generator.self_check(valid_grid)
    observed = generator.observe_overrides(valid_grid)
    if valid_errors:
        raise AssertionError(valid_errors)
    if observed != {"n_bands": 4, "first_transform": "anti_transpose"}:
        raise AssertionError(f"valid override not observed exactly: {observed}")

    invalid_error = None
    try:
        generator.generate(
            seed,
            0,
            difficulty="medium",
            n_bands=True,
            first_transform="anti_transpose",
        )
    except Exception as exc:  # retain exact public API behavior
        invalid_error = {"type": type(exc).__name__, "message": str(exc)}
    if invalid_error != {
        "type": "ValueError",
        "message": "n_bands must be integer 3 or 4",
    }:
        raise AssertionError(f"unexpected invalid-boundary behavior: {invalid_error}")

    receipt = {
        "schema": "arcpuzzles-supplementary-ticket-api-boundary-v1",
        "ticket_id": "ticket-0d5b4e6ed3c990e8",
        "task_id": TASK_ID,
        "source": {"path": str(source.relative_to(root.parent)), "sha256": source_hash},
        "probe_seed_hex": PROBE_SEED_HEX,
        "boundary": "n_bands advertised as plain integer 3..4; compare 4 with bool True",
        "valid_call": {
            "arguments": {
                "sample_index": 0,
                "difficulty": "medium",
                "n_bands": 4,
                "first_transform": "anti_transpose",
            },
            "grid_shape": [len(valid_grid), len(valid_grid[0])],
            "self_check_errors": valid_errors,
            "observed_overrides": observed,
        },
        "invalid_call": {
            "arguments": {
                "sample_index": 0,
                "difficulty": "medium",
                "n_bands": True,
                "first_transform": "anti_transpose",
            },
            "error": invalid_error,
        },
        "status": "completed",
        "finding": None,
        "disposition": "boundary_behaves_as_advertised",
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
