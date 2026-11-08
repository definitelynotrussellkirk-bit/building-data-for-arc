#!/usr/bin/env python3
"""Reproduce distribution/domain defects in generator 89a9a629c544."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "89a9a629c544"
REPO = Path(__file__).resolve().parents[3] / "repo"
GENERATOR = REPO / "generators" / TASK_ID / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def color_cells(grid, color):
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }


def flip_ud(cells):
    if not cells:
        return set()
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    return {(r1 + r2 - r, c) for r, c in cells}


def authority_mirror(grid):
    """Mirror the selected Racket loop: colors sorted, current grid each step."""
    out = [list(row) for row in grid]
    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        cells = color_cells(out, color)
        flipped = flip_ud(cells)
        for r, row in enumerate(out):
            for c, value in enumerate(row):
                if value == color:
                    out[r][c] = 0
        for r, c in flipped:
            out[r][c] = color
    return out


def nonzero_counts(grid):
    return dict(sorted(Counter(v for row in grid for v in row if v).items()))


def main():
    gen = load_generator()
    counts = Counter()
    first = {}
    draws = 1000
    for index in range(draws):
        seed = 100000 + index
        grid = gen.generate(seed, index, difficulty="easy")
        colors = sorted({v for row in grid for v in row if v})
        if len(colors) < 2:
            counts["fewer_than_two_colors"] += 1
            first.setdefault("fewer_than_two_colors", {"seed": seed, "sample_index": index, "input": grid})
        flipped = {color: flip_ud(color_cells(grid, color)) for color in colors}
        if colors and all(flipped[color] == color_cells(grid, color) for color in colors):
            counts["no_ud_asymmetric_layer"] += 1
            first.setdefault("no_ud_asymmetric_layer", {"seed": seed, "sample_index": index, "input": grid})
        collision_cells = set()
        for i, left in enumerate(colors):
            for right in colors[i + 1 :]:
                collision_cells |= flipped[left] & flipped[right]
        if collision_cells:
            counts["independent_flipped_masks_collide"] += 1
            first.setdefault(
                "independent_flipped_masks_collide",
                {
                    "seed": seed,
                    "sample_index": index,
                    "collision_cells": sorted(map(list, collision_cells)),
                    "input": grid,
                },
            )
        mirrored = authority_mirror(grid)
        if nonzero_counts(mirrored) != nonzero_counts(grid):
            counts["authority_mirror_changes_color_counts"] += 1
            first.setdefault(
                "authority_mirror_changes_color_counts",
                {
                    "seed": seed,
                    "sample_index": index,
                    "input_counts": nonzero_counts(grid),
                    "output_counts": nonzero_counts(mirrored),
                    "input": grid,
                    "output": mirrored,
                },
            )

    retained_racket = json.loads((Path(__file__).with_name("racket.json")).read_text())
    exact_input = retained_racket["results"][0]["input"]
    exact_output = retained_racket["results"][0]["output"]
    assert authority_mirror(exact_input) == exact_output

    result = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "rule_hash": retained_racket["executed_rule_hash"],
        "sample": {
            "difficulty": "easy",
            "draws": draws,
            "seed": "100000 + sample_index",
            "sample_index": "0..999",
        },
        "counts": dict(sorted(counts.items())),
        "first_examples": first,
        "exact_racket_case": {
            "seed": 100004,
            "sample_index": 4,
            "input_counts": nonzero_counts(exact_input),
            "output_counts": nonzero_counts(exact_output),
            "mirror_matches_racket": True,
            "racket_evidence": "checks/audit/89a9a629c544/racket.json",
        },
        "interpretation": (
            "Normal draws can violate both declared informative-input invariants and can place "
            "independently flipped color masks on the same cells. The selected sequential Racket "
            "authority then overwrites a not-yet-processed color, changing its cell count."
        ),
    }
    Path(__file__).with_name("probe.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"counts": result["counts"], "exact_racket_case": result["exact_racket_case"]}, indent=2))


if __name__ == "__main__":
    main()
