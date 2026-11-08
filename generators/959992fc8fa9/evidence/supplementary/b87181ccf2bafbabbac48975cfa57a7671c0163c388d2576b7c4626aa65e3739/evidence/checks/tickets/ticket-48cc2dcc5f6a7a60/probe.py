#!/usr/bin/env python3
"""One bounded valid/invalid API-boundary probe for ticket-48cc2dcc5f6a7a60."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "959992fc8fa9"
TICKET_ID = "ticket-48cc2dcc5f6a7a60"
PINNED_GENERATOR_SHA256 = "dc1e74b3723ff2ac8b96ffc1aeea6e7b1bf64b3fc217e10604fec46424678df2"
PROBE_SEED = "eb91cb5c7f101b1b08fe5e8c2a76e037e80e170256ad042411102fa78c347bcc"
ROOT = find_root(__file__)
OUT = ROOT.parent / "checks" / "tickets" / TICKET_ID / "result.json"


def main() -> int:
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    source_bytes_sha256 = hashlib.sha256(Path(source_path).read_bytes()).hexdigest()
    assert source_sha256 == source_bytes_sha256 == PINNED_GENERATOR_SHA256

    valid_overrides = {
        "grid_h": 6,
        "grid_w": 18,
        "n_pixels": 3,
        "color_pattern": "one_repeat",
        "anchor_corner": True,
    }
    grid = generator.generate(
        PROBE_SEED,
        0,
        difficulty="easy",
        **valid_overrides,
    )
    observed = generator.observe_overrides(grid)
    errors = generator.self_check(grid)
    assert errors == []
    assert observed == valid_overrides

    invalid_overrides = dict(valid_overrides)
    invalid_overrides["n_pixels"] = True
    invalid_exception = None
    try:
        generator.generate(
            PROBE_SEED,
            0,
            difficulty="easy",
            **invalid_overrides,
        )
    except Exception as exc:  # retained actual boundary behavior
        invalid_exception = {"type": type(exc).__name__, "message": str(exc)}
    assert invalid_exception == {
        "type": "ValueError",
        "message": "n_pixels must be an integer",
    }

    result = {
        "schema": "arc-generator-api-boundary-probe-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "consumer": "target_current_audit",
        "status": "completed",
        "probe_seed": PROBE_SEED,
        "source": {
            "path": str(Path(source_path).relative_to(ROOT.parent)),
            "sha256": source_sha256,
            "pinned_sha256": PINNED_GENERATOR_SHA256,
            "matches_pin": True,
        },
        "valid_call": {
            "difficulty": "easy",
            "overrides": valid_overrides,
            "observed": observed,
            "self_check": errors,
            "grid": grid,
        },
        "invalid_call": {
            "difficulty": "easy",
            "overrides": invalid_overrides,
            "exception": invalid_exception,
        },
        "conclusion": (
            "The exact lower/upper dimension and one-repeat/corner boundary is "
            "observable, while bool-as-int is rejected before generation."
        ),
        "limits": [
            "One valid/invalid comparison only, as bounded by the ticket.",
            "No claim about unprobed API boundaries or peer safety.",
        ],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "result": str(OUT)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
