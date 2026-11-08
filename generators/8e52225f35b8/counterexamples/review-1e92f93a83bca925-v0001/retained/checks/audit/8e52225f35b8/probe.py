#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "8e52225f35b8"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
OUT = Path(__file__).resolve().parent


def closures(grid):
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    bounds = []
    left = 0
    for divider in dividers + [w]:
        bounds.append((left, divider))
        left = divider + 1
    result = []
    for left, right in bounds:
        cells = [
            (r, c - left)
            for r in range(h)
            for c in range(left, right)
            if grid[r][c] not in (0, 9)
        ]
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        result.append(
            {
                (r, c)
                for r in range(min(rs), max(rs) + 1)
                for c in range(min(cs), max(cs) + 1)
            }
        )
    return bounds, result


def output_for(grid, *, all_panels: bool):
    bounds, panel_closures = closures(grid)
    h = len(grid)
    panel_w = bounds[0][1] - bounds[0][0]
    counts = Counter(cell for closure in panel_closures for cell in closure)
    if all_panels:
        chosen = {cell for cell, count in counts.items() if count == len(panel_closures)}
    else:
        chosen = {cell for cell, count in counts.items() if count >= 2}
    return [[8 if (r, c) in chosen else 0 for c in range(panel_w)] for r in range(h)]


def canonical_rule_hash():
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            text = row["program_solution"]
            return hashlib.sha256(" ".join(text.split()).encode()).hexdigest(), text
    raise KeyError(TASK_ID)


def main():
    easy = GEN.generate(20261006, 0, difficulty="easy")
    easy_bounds, _ = closures(easy)
    easy_intended = output_for(easy, all_panels=False)
    easy_rival = output_for(easy, all_panels=True)
    assert len(easy_bounds) == 2
    assert easy_intended == easy_rival

    hard = None
    hard_seed = None
    hard_index = None
    for seed in range(100):
        for sample_index in range(5):
            candidate = GEN.generate(seed, sample_index, difficulty="hard")
            bounds, _ = closures(candidate)
            intended = output_for(candidate, all_panels=False)
            rival = output_for(candidate, all_panels=True)
            if len(bounds) >= 3 and intended != rival:
                hard = candidate
                hard_seed = seed
                hard_index = sample_index
                hard_intended = intended
                hard_rival = rival
                break
        if hard is not None:
            break
    assert hard is not None

    rule_sha, rule_source = canonical_rule_hash()
    report = {
        "schema": "audit-probe-v1",
        "task_id": TASK_ID,
        "source_path": str(SOURCE),
        "source_sha256": SOURCE_SHA256,
        "canonical_rule_normalized_sha256": rule_sha,
        "finding": (
            "Every easy draw has exactly two panels, so the rival 'intersection "
            "of all panel closures' is answer-equivalent to the intended "
            "'cells covered by at least two closures' rule on the entire easy band."
        ),
        "easy_counterexample": {
            "seed": 20261006,
            "sample_index": 0,
            "difficulty": "easy",
            "self_check": GEN.self_check(easy, difficulty="easy"),
            "panel_count": len(easy_bounds),
            "input": easy,
            "intended_output": easy_intended,
            "all_panels_intersection_output": easy_rival,
            "outputs_equal": easy_intended == easy_rival,
        },
        "distinguishing_generated_witness": {
            "seed": hard_seed,
            "sample_index": hard_index,
            "difficulty": "hard",
            "self_check": GEN.self_check(hard, difficulty="hard"),
            "panel_count": len(closures(hard)[0]),
            "input": hard,
            "intended_output": hard_intended,
            "all_panels_intersection_output": hard_rival,
            "differing_cells": sum(
                a != b
                for row_a, row_b in zip(hard_intended, hard_rival)
                for a, b in zip(row_a, row_b)
            ),
        },
        "limits": [
            "This finite probe establishes the declared rival on the sampled source hash, not all possible rivals.",
            "The audit does not modify the target generator.",
        ],
    }
    (OUT / "counterexample.json").write_text(json.dumps(report, indent=2) + "\n")
    (OUT / "inputs.json").write_text(
        json.dumps({"inputs": [easy, hard]}, indent=2) + "\n"
    )
    print(json.dumps({
        "source_sha256": SOURCE_SHA256,
        "easy_panel_count": len(easy_bounds),
        "easy_outputs_equal": True,
        "hard_seed": hard_seed,
        "hard_sample_index": hard_index,
        "hard_panel_count": len(closures(hard)[0]),
        "hard_differing_cells": report["distinguishing_generated_witness"]["differing_cells"],
    }))


if __name__ == "__main__":
    main()
