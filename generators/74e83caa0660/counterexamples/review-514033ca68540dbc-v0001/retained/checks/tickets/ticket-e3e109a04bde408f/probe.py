#!/usr/bin/env python3
"""Pinned one-shot API-boundary probe for ticket-e3e109a04bde408f."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "74e83caa0660"
EXPECTED_SHA256 = "26f5b1f9c343e2e9faa3a69fb4d7065dc8ca33d7e9ec44754f0199023b89e690"
TICKET_ID = "ticket-e3e109a04bde408f"
PROBE_SEED = "b49ff23e58716fd7f7545ef205edd63deaa97895bc627373dbab3a63f5abe01b"


def _active_color_count(grid: list[list[int]]) -> int:
    return len(Counter(cell for row in grid for cell in row if cell != 0))


def run(out: Path) -> dict:
    root = find_root(__file__)
    generator, source, digest = load_selected_generator(TASK_ID, root=root)
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"source changed: expected {EXPECTED_SHA256}, got {digest}")

    seed = int(PROBE_SEED[:16], 16)
    sample_index = 0
    baseline = generator.generate(seed, sample_index)
    valid_advertised = generator.generate(seed, sample_index, n_pairs=1)
    invalid_advertised = generator.generate(seed, sample_index, n_pairs=9)
    hidden_two = generator.generate(seed, sample_index, pairs=2)
    hidden_four = generator.generate(seed, sample_index, pairs=4)

    result = {
        "schema": "arcpuzzles-api-boundary-ticket-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "probe_seed": PROBE_SEED,
        "source": {
            "path": str(source.relative_to(root)),
            "sha256": digest,
            "version": generator.VERSION,
            "declared_n_pairs": generator.AXES["n_pairs"],
        },
        "calls": {
            "baseline": {"kwargs": {}, "active_colors": _active_color_count(baseline)},
            "advertised_valid": {
                "kwargs": {"n_pairs": 1},
                "accepted": True,
                "active_colors": _active_color_count(valid_advertised),
                "same_grid_as_baseline": valid_advertised == baseline,
            },
            "advertised_invalid": {
                "kwargs": {"n_pairs": 9},
                "accepted": True,
                "active_colors": _active_color_count(invalid_advertised),
                "same_grid_as_baseline": invalid_advertised == baseline,
            },
            "implementation_label_two": {
                "kwargs": {"pairs": 2},
                "active_colors": _active_color_count(hidden_two),
            },
            "implementation_label_four": {
                "kwargs": {"pairs": 4},
                "active_colors": _active_color_count(hidden_four),
            },
        },
    }
    result["finding"] = {
        "present": (
            valid_advertised == baseline
            and invalid_advertised == baseline
            and _active_color_count(hidden_two) == 2
            and _active_color_count(hidden_four) == 4
        ),
        "summary": (
            "AXES advertises n_pairs=1..8, but generate consumes the key 'pairs'; "
            "the advertised valid value is inert and the advertised out-of-range "
            "value is silently accepted."
        ),
        "suggested_fix": (
            "Validate unknown/advertised overrides and consume n_pairs through the "
            "same exact label, with tests for 1, 8, and out-of-range values."
        ),
    }
    if not result["finding"]["present"]:
        raise AssertionError("pinned API mismatch did not reproduce")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.out.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
