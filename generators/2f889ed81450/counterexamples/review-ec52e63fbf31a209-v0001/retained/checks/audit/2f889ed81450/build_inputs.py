#!/usr/bin/env python3
"""Build source-bound audit inputs for 2f889ed81450 without editing it."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "2f889ed81450"
EXPECTED_GENERATOR_SHA256 = "2d616c5f9f1780fff1ddc8766cce179d3db71f274d90dd88b79e3c78dfd49e06"
SEED = 20261019
SAMPLE_INDICES = list(range(60))


def sha(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(value).hexdigest()


def nonzero(grid):
    return [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]


def margin(grid, cell):
    r, c, _ = cell
    return min(r, c, len(grid) - 1 - r, len(grid[0]) - 1 - c)


def main():
    root = find_root(__file__)
    generator, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    if source_sha != EXPECTED_GENERATOR_SHA256:
        raise AssertionError(f"unexpected generator source {source_sha}")

    generated = []
    for sample_index in SAMPLE_INDICES:
        grid = generator.generate(SEED, sample_index, difficulty="medium")
        errors = generator.self_check(grid)
        if errors:
            raise AssertionError((sample_index, errors))
        cells = nonzero(grid)
        generated.append({
            "kind": "ordinary_generated",
            "seed": SEED,
            "sample_index": sample_index,
            "difficulty": "medium",
            "input": grid,
            "input_sha256": sha(grid),
            "seed_count": len(cells),
            "minimum_border_margin": min(margin(grid, cell) for cell in cells),
            "self_check": errors,
        })

    canonical = next(
        row
        for row in canonical_pairs(TASK_ID, root=root, labeled_only=True)
        if min(margin(row["input"], cell) for cell in nonzero(row["input"])) < 2
    )
    canonical_row = {
        "kind": "canonical_near_edge",
        "variant": canonical["variant"],
        "split": canonical["split"],
        "pair_index": canonical["pair_index"],
        "input": canonical["input"],
        "input_sha256": sha(canonical["input"]),
        "expected_output": canonical["output"],
        "expected_output_sha256": sha(canonical["output"]),
        "minimum_border_margin": min(
            margin(canonical["input"], cell) for cell in nonzero(canonical["input"])
        ),
        "self_check": generator.self_check(canonical["input"]),
    }

    too_close = [[0] * 9 for _ in range(8)]
    too_close[3][3] = 5
    too_close[3][5] = 6
    too_close_row = {
        "kind": "validator_too_close",
        "input": too_close,
        "input_sha256": sha(too_close),
        "seed_cells": nonzero(too_close),
        "pairwise_manhattan_distance": 2,
        "self_check": generator.self_check(too_close),
    }

    override_grid = generator.generate(
        SEED,
        0,
        difficulty="medium",
        n_seeds=1,
        n_distinct_colors=1,
    )
    override_row = {
        "kind": "ignored_override",
        "seed": SEED,
        "sample_index": 0,
        "difficulty": "medium",
        "overrides": {"n_seeds": 1, "n_distinct_colors": 1},
        "input": override_grid,
        "input_sha256": sha(override_grid),
        "observed_seed_count": len(nonzero(override_grid)),
        "observed_distinct_nonzero_colors": len({v for _, _, v in nonzero(override_grid)}),
        "self_check": generator.self_check(override_grid),
    }

    rows = [*generated, canonical_row, too_close_row, override_row]
    out = Path(__file__).resolve().parent
    (out / "input.json").write_text(
        json.dumps([row["input"] for row in rows], indent=2) + "\n"
    )
    metadata = {
        "schema": "arcpuzzles-audit-inputs-v1",
        "task_id": TASK_ID,
        "generator_path": Path(source_path).relative_to(root).as_posix(),
        "generator_sha256": source_sha,
        "ordinary_sample": {
            "seed": SEED,
            "sample_indices": SAMPLE_INDICES,
            "denominator": len(generated),
        },
        "rows": rows,
    }
    (out / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({
        "generator_sha256": source_sha,
        "rows": len(rows),
        "ordinary": len(generated),
        "ordinary_minimum_margin": min(row["minimum_border_margin"] for row in generated),
        "canonical_minimum_margin": canonical_row["minimum_border_margin"],
        "too_close_self_check": too_close_row["self_check"],
        "override_observed_seed_count": override_row["observed_seed_count"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
