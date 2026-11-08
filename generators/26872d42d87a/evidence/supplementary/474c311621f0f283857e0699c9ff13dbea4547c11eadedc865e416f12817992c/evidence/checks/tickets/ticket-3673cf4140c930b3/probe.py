#!/usr/bin/env python3
"""Bounded source-bound probe for ticket-3673cf4140c930b3."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, load_selected_generator

TASK_ID = "26872d42d87a"
EXPECTED_SOURCE_SHA256 = "50a1cff760fcb53d4ae76279ca83fe5a54f270903cd2f467bd9eed2195b879c6"
EXPECTED_RULE_HASH = "bc262329ef0d"


def rival_ignore_center_color(grid):
    """Fill every cell bracketed horizontally by 6, even when it is not 0."""
    output = deepcopy(grid)
    for row in range(len(grid)):
        for col in range(1, len(grid[0]) - 1):
            if grid[row][col - 1] == 6 and grid[row][col + 1] == 6:
                output[row][col] = 6
    return output


def make_witness(module):
    seed = 731
    sample_index = 0
    difficulty = "easy"
    profile = "h8_w10"
    grid = module.generate(
        seed, sample_index, difficulty=difficulty, scene_profile=profile
    )
    # Preserve the generated teaching scene, but relocate its decoration into a
    # lawful border 6,5,6 pattern. The authority must preserve the 5 because the
    # center is not background; the shortcut overwrites it.
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == 5:
                grid[row][col] = 0
    width = len(grid[0])
    chosen = None
    for row in (0, len(grid) - 1):
        for center in range(2, width - 2):
            if grid[row][center - 2 : center + 3] == [0, 0, 0, 0, 0]:
                chosen = (row, center)
                break
        if chosen:
            break
    if chosen is None:
        raise AssertionError("could not find a clean border slot for 6,5,6 witness")
    row, center = chosen
    grid[row][center - 1 : center + 2] = [6, 5, 6]
    return {
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "overrides": {"scene_profile": profile},
        "edited_cells": [
            {"row": row, "col": center - 1, "value": 6},
            {"row": row, "col": center, "value": 5},
            {"row": row, "col": center + 1, "value": 6},
        ],
        "distinguishing_cell": {"row": row, "col": center},
        "input": grid,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    module, source_path, source_sha256 = load_selected_generator(TASK_ID)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise ValueError(
            f"peer source differs from ticket: {source_sha256} != {EXPECTED_SOURCE_SHA256}"
        )
    if module.RULE_HASH != EXPECTED_RULE_HASH:
        raise ValueError(
            f"peer rule differs from ticket: {module.RULE_HASH} != {EXPECTED_RULE_HASH}"
        )

    root = Path.cwd()
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_fit = [
        rival_ignore_center_color(pair["input"]) == pair["output"] for pair in pairs
    ]

    generated = []
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for sample_index in range(20):
            grid = module.generate(8700 + band_index, sample_index, difficulty=band)
            expected = module.rule_mirror(grid)
            generated.append(
                {
                    "difficulty": band,
                    "sample_index": sample_index,
                    "self_check": module.self_check(grid),
                    "rival_matches": rival_ignore_center_color(grid) == expected,
                    "has_6_5_6": any(
                        row[col - 1 : col + 2] == [6, 5, 6]
                        for row in grid
                        for col in range(1, len(row) - 1)
                    ),
                }
            )

    witness = make_witness(module)
    grid = witness["input"]
    witness_errors = module.self_check(grid)
    python_output = module.rule_mirror(grid)
    rival_output = rival_ignore_center_color(grid)
    receipt = Catalog(root).apply(
        TASK_ID, [grid], reference="canonical", timeout=120
    )
    result = receipt["results"][0]
    racket_output = result["output"]
    differing_cells = [
        {"row": row, "col": col, "authority": racket_output[row][col], "rival": rival_output[row][col]}
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if racket_output[row][col] != rival_output[row][col]
    ]

    report = {
        "schema": "arcpuzzles-adversarial-witness-ticket-v1",
        "ticket_id": "ticket-3673cf4140c930b3",
        "task_id": TASK_ID,
        "status": "finding",
        "source": {
            "path": str(source_path.relative_to(root)),
            "sha256": source_sha256,
            "version": module.VERSION,
            "rule_hash": module.RULE_HASH,
        },
        "shortcut": {
            "name": "ignore_center_color",
            "description": "Change any cell horizontally bracketed by color 6 to 6, without requiring that the center was 0.",
            "canonical_fit": {
                "matched": sum(canonical_fit),
                "total": len(canonical_fit),
                "all_match": all(canonical_fit),
            },
            "bounded_generated_probe": {
                "cases": len(generated),
                "matched": sum(row["rival_matches"] for row in generated),
                "self_check_failures": sum(bool(row["self_check"]) for row in generated),
                "inputs_with_6_5_6": sum(row["has_6_5_6"] for row in generated),
                "scope": "20 default samples in each of easy, medium, and hard; finite evidence only",
            },
            "source_reason": "Generated 5s are border decorations; horizontal teaching rows are interior, and the single border 6 endpoint has no same-row partner, so ordinary samples do not expose a 6,5,6 center-color case.",
        },
        "witness": {
            **witness,
            "self_check": witness_errors,
            "python_rule_output": python_output,
            "racket_output": racket_output,
            "rival_output": rival_output,
            "differing_cells": differing_cells,
            "racket": {
                "executed_rule_hash": receipt["executed_rule_hash"],
                "rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
                "error": result["error"],
                "input_sha256": result["input_sha256"],
                "output_sha256": result["output_sha256"],
                "matches_python_rule_output": racket_output == python_output,
            },
        },
        "conclusion": "The source-bound rival fits all five labeled canonical pairs and all 60 bounded default draws, but disagrees on a lawful self_check-passing input. Add a generated 6,5,6 non-trigger or an equivalent nonzero-center witness and declare the rival.",
    }

    assert report["shortcut"]["canonical_fit"]["all_match"]
    assert report["shortcut"]["bounded_generated_probe"]["matched"] == 60
    assert report["shortcut"]["bounded_generated_probe"]["inputs_with_6_5_6"] == 0
    assert witness_errors == []
    assert receipt["rule_hash_matches_catalog"]
    assert receipt["executed_rule_hash"] == EXPECTED_RULE_HASH
    assert result["error"] is None
    assert racket_output == python_output
    assert differing_cells == [
        {
            "row": witness["distinguishing_cell"]["row"],
            "col": witness["distinguishing_cell"]["col"],
            "authority": 5,
            "rival": 6,
        }
    ]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "canonical_fit": report["shortcut"]["canonical_fit"],
        "generated_probe": report["shortcut"]["bounded_generated_probe"],
        "differing_cells": differing_cells,
        "report": str(args.out),
    }, indent=2))


if __name__ == "__main__":
    main()
