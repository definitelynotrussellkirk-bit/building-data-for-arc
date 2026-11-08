#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

PACKET = Path(__file__).resolve().parents[1]
REPO = PACKET / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def span_rival(module, grid):
    analysis = module._analysis(grid)
    if analysis["errors"]:
        raise ValueError(analysis["errors"])
    rows = analysis["floor_rows"]
    colors = analysis["floor_colors"]
    counts = []
    for i, color in enumerate(colors[:3]):
        start, stop = rows[i] + 1, rows[i + 1]
        occupied_rows = sum(any(v == color for v in grid[r]) for r in range(start, stop))
        counts.append(occupied_rows // 2)
    positive = [(count, i) for i, count in enumerate(counts) if count > 0]
    gray_idx = min(positive, key=lambda pair: (pair[0], -pair[1]))[1] if positive else 0
    return [
        [
            colors[r] if c < counts[r] else 9 if c == 3 else 5 if c == 4 and r == gray_idx else 0
            for c in range(5)
        ]
        for r in range(3)
    ]


def main():
    d06 = load("d06e81a85b9e")
    requested = {"grid_h": 8, "grid_w": 10, "n2": 5, "n3": 1}
    d06_grid = d06.generate(1, 0, difficulty="medium", **requested)
    observed = {
        "grid_h": len(d06_grid),
        "grid_w": len(d06_grid[0]),
        "n2": sum(v == 2 for row in d06_grid for v in row),
        "n3": sum(v == 3 for row in d06_grid for v in row),
    }
    hard_dims = []
    outside = 0
    for seed in range(1, 201):
        grid = d06.generate(seed, 0, difficulty="hard")
        dims = (len(grid), len(grid[0]))
        hard_dims.append(dims)
        if not (6 <= dims[0] <= 12 and 7 <= dims[1] <= 14):
            outside += 1

    ladder = load("7b088f161470")
    canonical_span_matches = {
        name: span_rival(ladder, grid) == ladder.rule_mirror(grid)
        for name, grid in ladder._PUBLIC_INPUTS.items()
    }
    counterexample = [row[:] for row in ladder._PUBLIC_INPUTS["public_train_1"]]
    for row in (2, 3, 4):
        counterexample[row][9] = 4
        counterexample[row][11] = 4
    intended = ladder.rule_mirror(counterexample)
    rival = span_rival(ladder, counterexample)

    generated_matches = 0
    generated_draws = 0
    generated_disagreements = []
    for band in ("easy", "medium", "hard"):
        for sample_index in range(200):
            grid = ladder.generate(8675309, sample_index, difficulty=band)
            generated_draws += 1
            if span_rival(ladder, grid) == ladder.rule_mirror(grid):
                generated_matches += 1
            elif len(generated_disagreements) < 5:
                generated_disagreements.append({"band": band, "sample_index": sample_index})

    report = {
        "schema": "review-a484b45ff0084d8c-audit-probes/1",
        "d06e81a85b9e": {
            "classification": "reproduced contract defect",
            "override_request": requested,
            "override_observed": observed,
            "self_check": d06.self_check(d06_grid, difficulty="medium"),
            "hard_draws": 200,
            "hard_dimensions_outside_declared_axis_range": outside,
            "hard_dimension_examples": [list(x) for x in hard_dims[:10]],
            "declared_grid_h_valid": d06.AXES["grid_h"]["valid"],
            "declared_grid_w_valid": d06.AXES["grid_w"]["valid"],
            "declared_n3_valid": d06.AXES["n3"]["valid"],
        },
        "7b088f161470": {
            "classification": "reproduced shortcut",
            "shortcut": "infer rung count as floor(number of ladder-colored rows / 2), without checking for full contiguous rungs",
            "canonical_span_matches": canonical_span_matches,
            "counterexample_input": counterexample,
            "counterexample_self_check": ladder.self_check(counterexample),
            "intended_output": intended,
            "shortcut_output": rival,
            "outputs_disagree": intended != rival,
            "generated_draws": generated_draws,
            "generated_shortcut_matches": generated_matches,
            "generated_disagreements": generated_disagreements,
        },
    }
    out = PACKET / "checks" / "audit_probes.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
