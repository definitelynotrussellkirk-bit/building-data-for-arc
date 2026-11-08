#!/usr/bin/env python3
"""Source-bound minimal override-contract witness for 67702540cb95."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from reviewer_support import find_root, load_selected_generator, normalize_grid

TASK_ID = "67702540cb95"
SEED = 0
SAMPLE_INDEX = 3
DIFFICULTY = "easy"


def shape(grid: list[list[int]]) -> list[int]:
    return [len(grid), len(grid[0]) if grid else 0]


def blue_components(grid: list[list[int]]) -> int:
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1}
    count = 0
    while unseen:
        count += 1
        start = unseen.pop()
        stack = [start]
        while stack:
            r, c = stack.pop()
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in unseen:
                    unseen.remove(nxt)
                    stack.append(nxt)
    return count


def main(argv=None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    root = find_root(__file__)
    generator, source, generator_sha = load_selected_generator(TASK_ID, root=root)
    cases = {
        "default": {},
        "grid_h_min": {"grid_h": 9},
        "grid_h_max": {"grid_h": 28},
        "grid_w_min": {"grid_w": 9},
        "grid_w_max": {"grid_w": 28},
        "shape_count_min": {"shape_count": 1},
        "shape_count_max": {"shape_count": 16},
        "anchor_corner_false": {"anchor_corner": False},
        "anchor_corner_true": {"anchor_corner": True},
        "asymmetry_force_false": {"asymmetry_force": False},
        "asymmetry_force_true": {"asymmetry_force": True},
        "unknown_key": {"__override_contract_unknown_axis__": 123},
    }

    rows = {}
    for name, overrides in cases.items():
        grid = normalize_grid(
            generator.generate(
                SEED,
                SAMPLE_INDEX,
                difficulty=DIFFICULTY,
                **overrides,
            )
        )
        rows[name] = {
            "overrides": overrides,
            "shape": shape(grid),
            "blue_cells": sum(value == 1 for row in grid for value in row),
            "blue_components": blue_components(grid),
            "self_check": generator.self_check(grid, difficulty=DIFFICULTY),
            "grid": grid,
        }

    default_grid = rows["default"]["grid"]
    for row in rows.values():
        row["identical_to_default"] = row["grid"] == default_grid

    assertions = {
        "grid_h_9_not_honored": rows["grid_h_min"]["shape"][0] != 9,
        "grid_h_28_not_honored": rows["grid_h_max"]["shape"][0] != 28,
        "grid_w_9_not_honored": rows["grid_w_min"]["shape"][1] != 9,
        "grid_w_28_not_honored": rows["grid_w_max"]["shape"][1] != 28,
        "grid_h_extremes_identical": rows["grid_h_min"]["grid"] == rows["grid_h_max"]["grid"],
        "grid_w_extremes_identical": rows["grid_w_min"]["grid"] == rows["grid_w_max"]["grid"],
        "shape_count_extremes_identical": rows["shape_count_min"]["grid"] == rows["shape_count_max"]["grid"],
        "anchor_corner_values_identical": rows["anchor_corner_false"]["grid"] == rows["anchor_corner_true"]["grid"],
        "asymmetry_force_values_identical": rows["asymmetry_force_false"]["grid"] == rows["asymmetry_force_true"]["grid"],
        "unknown_key_silently_accepted": "unknown_key" in rows,
        "all_outputs_pass_self_check": all(not row["self_check"] for row in rows.values()),
    }
    if not all(assertions.values()):
        failed = [name for name, value in assertions.items() if not value]
        raise AssertionError(f"minimal override witness assumptions failed: {failed}")

    report = {
        "schema": "arcpuzzles-adversarial-audit-v1",
        "task_id": TASK_ID,
        "finding": (
            "advertised override axes are accepted but ignored; even opposite endpoint values "
            "produce identical grids, requested grid dimensions are not realized, and an unknown key is accepted"
        ),
        "classification": "reproduced_override_contract_defect",
        "generator_path": str(source.relative_to(root)),
        "generator_sha256": generator_sha,
        "generator_version": generator.VERSION,
        "command": [sys.executable, *sys.argv],
        "cwd": str(Path.cwd()),
        "fixed_draw": {
            "seed": SEED,
            "sample_index": SAMPLE_INDEX,
            "difficulty": DIFFICULTY,
        },
        "advertised_axes": {
            key: generator.AXES[key]
            for key in ("grid_h", "grid_w", "shape_count", "anchor_corner", "asymmetry_force")
        },
        "assertions": assertions,
        "cases": rows,
        "root_cause": (
            "generate() passes **overrides into gen_ctx but never draws or reads the advertised "
            "grid_h, grid_w, shape_count, anchor_corner, or asymmetry_force axes. It instead draws "
            "internal n_rbands/n_cbands and derives shape count from fill_frac. The catch-all **overrides "
            "also accepts unknown keys without rejecting them."
        ),
        "corroborating_battery": {
            "result": "../67702540cb95-override/result.json",
            "override_results": "../67702540cb95-override/checks/67702540cb95_audit_override_results.json",
            "finding_count": 11925,
            "warning_count": 2,
            "notable_counts": {
                "grid_h_override_mismatch": 5670,
                "grid_w_override_mismatch": 5670,
            },
        },
        "limitations": [
            "This minimal witness fixes one seed/sample/band; the override battery supplies the broad sweep.",
            "This audit does not modify the assigned audit target.",
            "The earlier parity-erasure hypothesis was tested on 120 generated inputs and was not reproduced.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "out": str(args.out),
        "generator_sha256": generator_sha,
        "default_shape": rows["default"]["shape"],
        "assertions": assertions,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
