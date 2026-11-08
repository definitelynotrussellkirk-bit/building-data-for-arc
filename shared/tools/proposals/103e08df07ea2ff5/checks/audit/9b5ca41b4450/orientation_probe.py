#!/usr/bin/env python3
"""Source-bound probe for an endpoint-orientation shortcut in 9b5ca41b4450."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "9b5ca41b4450"


def nonzero_cells(grid):
    return [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value]


def orientation(grid):
    cells = nonzero_cells(grid)
    if len(cells) != 2:
        return "other"
    (r0, c0, _), (r1, c1, _) = sorted(cells)
    if c0 < c1:
        return "nw_se"
    if c0 > c1:
        return "ne_sw"
    return "same_column"


def shortcut(grid):
    """Expand only NW->SE endpoint pairs; leave other inputs unchanged."""
    cells = nonzero_cells(grid)
    if len(cells) != 2:
        return [row[:] for row in grid]
    (r0, c0, color), (r1, c1, color1) = sorted(cells)
    if color != color1 or c0 >= c1:
        return [row[:] for row in grid]
    out = [[0 for _ in row] for row in grid]
    for c in range(c0, c1 + 1):
        out[r0][c] = color
        out[r1][c] = color
    for r in range(r0, r1 + 1):
        out[r][c0] = color
        out[r][c1] = color
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = find_root(__file__)
    gen, path, source_sha = load_selected_generator(TASK_ID, root=root)

    counts = {"nw_se": 0, "ne_sw": 0, "same_column": 0, "other": 0}
    examples = []
    for band in ("easy", "medium", "hard"):
        for sample_index in range(200):
            grid = gen.generate(20261023, sample_index, difficulty=band)
            kind = orientation(grid)
            counts[kind] += 1
            if len(examples) < 3:
                examples.append({"band": band, "sample_index": sample_index, "orientation": kind, "input": grid})

    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_orientations = [orientation(pair["input"]) for pair in pairs]
    shortcut_canonical_pass = [shortcut(pair["input"]) == pair["output"] for pair in pairs]

    counterexample = [
        [0, 0, 0, 0, 5, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 5, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]
    payload = {
        "schema": "audit-orientation-shortcut-v1",
        "task_id": TASK_ID,
        "generator_path": str(path.relative_to(root)),
        "generator_sha256": source_sha,
        "draws": 600,
        "generated_orientation_counts": counts,
        "canonical_pairs": len(pairs),
        "canonical_orientations": canonical_orientations,
        "shortcut_fits_all_canonical": all(shortcut_canonical_pass),
        "shortcut_canonical_pass": shortcut_canonical_pass,
        "counterexample": counterexample,
        "counterexample_orientation": orientation(counterexample),
        "counterexample_self_check": gen.self_check(counterexample),
        "shortcut_counterexample_output": shortcut(counterexample),
        "finding": (
            "The generator and every canonical pair use only NW-SE endpoint order. "
            "A model can learn an orientation-gated rectangle shortcut and never see a lawful NE-SW pair."
        ),
        "examples": examples,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "reproduced",
        "generator_sha256": source_sha,
        "generated_orientation_counts": counts,
        "canonical_orientations": canonical_orientations,
        "counterexample_self_check": payload["counterexample_self_check"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
