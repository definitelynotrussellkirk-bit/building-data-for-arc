from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GENERATOR = ROOT / "repo/generators/39e5f1c25127/generator.py"
CANONICAL = ROOT / "repo/shared/data/canonical/puzzles.jsonl"
OUT = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("audit_39e5f1c25127", GENERATOR)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def color_cells(grid, color):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]


def bbox_center(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return ((min(rows) + max(rows)) / 2, (min(cols) + max(cols)) / 2)


def anchor_and_satellite(grid):
    colors = sorted({value for row in grid for value in row if value != 0})
    assert len(colors) == 2, colors
    gr = (len(grid) - 1) / 2
    gc = (len(grid[0]) - 1) / 2
    ranked = sorted(
        colors,
        key=lambda color: (
            (bbox_center(color_cells(grid, color))[0] - gr) ** 2
            + (bbox_center(color_cells(grid, color))[1] - gc) ** 2,
            color,
        ),
    )
    return ranked[0], ranked[1]


def mirror_output(grid, *, global_center=False):
    h, w = len(grid), len(grid[0])
    anchor, satellite = anchor_and_satellite(grid)
    if global_center:
        row_sum, col_sum = h - 1, w - 1
    else:
        acells = color_cells(grid, anchor)
        rows = [r for r, _ in acells]
        cols = [c for _, c in acells]
        row_sum = min(rows) + max(rows)
        col_sum = min(cols) + max(cols)
    out = [row[:] for row in grid]
    for r, c in color_cells(grid, satellite):
        for rr, cc in ((r, col_sum - c), (row_sum - r, c), (row_sum - r, col_sum - c)):
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = satellite
    return out


def load_canonical():
    with CANONICAL.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == "39e5f1c25127":
                return row
    raise RuntimeError("canonical task not found")


def main():
    generated_count = 1000
    center_aligned = 0
    rival_equal = 0
    self_check_failures = []
    generated_example = None
    for i in range(generated_count):
        seed = 6000 + i
        difficulty = ("easy", "medium", "hard")[i % 3]
        grid = mod.generate(seed, i, difficulty=difficulty)
        errors = mod.self_check(grid, difficulty=difficulty)
        if errors:
            self_check_failures.append({"seed": seed, "sample_index": i, "errors": errors})
        anchor, _ = anchor_and_satellite(grid)
        center = bbox_center(color_cells(grid, anchor))
        global_center = ((len(grid) - 1) / 2, (len(grid[0]) - 1) / 2)
        if center == global_center:
            center_aligned += 1
        if mirror_output(grid) == mirror_output(grid, global_center=True):
            rival_equal += 1
        if generated_example is None:
            generated_example = {
                "seed": seed,
                "sample_index": i,
                "difficulty": difficulty,
                "input": grid,
                "true_output": mirror_output(grid),
                "global_center_rival": mirror_output(grid, global_center=True),
            }

    canonical = load_canonical()
    canonical_pairs = canonical["train"] + canonical["test"]
    true_matches = 0
    rival_matches = 0
    differing = 0
    counterexample = None
    for pair_index, pair in enumerate(canonical_pairs):
        truth = mirror_output(pair["input"])
        rival = mirror_output(pair["input"], global_center=True)
        true_matches += truth == pair["output"]
        rival_matches += rival == pair["output"]
        differing += truth != rival
        if counterexample is None and truth == pair["output"] and rival != pair["output"]:
            counterexample = {
                "pair_index": pair_index,
                "input": pair["input"],
                "canonical_output": pair["output"],
                "true_oracle_output": truth,
                "global_center_rival_output": rival,
                "mismatch_cells": [
                    [r, c, truth[r][c], rival[r][c]]
                    for r in range(len(truth))
                    for c in range(len(truth[0]))
                    if truth[r][c] != rival[r][c]
                ],
            }

    assert counterexample is not None
    summary = {
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "generated_sampling": {
            "samples": generated_count,
            "seed_formula": "6000 + i",
            "sample_index": "i",
            "difficulty": "cycles easy, medium, hard",
            "self_check_failures": len(self_check_failures),
            "anchor_bbox_center_equals_global_center": center_aligned,
            "global_center_rival_equals_anchor_center_oracle": rival_equal,
        },
        "canonical": {
            "pairs": len(canonical_pairs),
            "anchor_center_oracle_matches_saved_output": true_matches,
            "global_center_rival_matches_saved_output": rival_matches,
            "oracle_and_rival_differ": differing,
            "counterexample_pair_index": counterexample["pair_index"],
            "counterexample_mismatch_cells": len(counterexample["mismatch_cells"]),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (OUT / "generated_example.json").write_text(json.dumps(generated_example, indent=2) + "\n")
    (OUT / "canonical_counterexample.json").write_text(json.dumps(counterexample, indent=2) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
