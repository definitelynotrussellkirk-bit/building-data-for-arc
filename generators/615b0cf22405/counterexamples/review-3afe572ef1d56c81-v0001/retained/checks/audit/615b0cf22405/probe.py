#!/usr/bin/env python3
"""Find and verify a production lesson that omits crossing precedence."""
from __future__ import annotations

from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs

TASK = "615b0cf22405"
ROOT = Path.cwd()
GEN_PATH = ROOT / "generators" / TASK / "generator.py"
OUT = ROOT.parent / "checks" / "audit" / TASK / "evidence.json"

spec = importlib.util.spec_from_file_location("audit_615", GEN_PATH)
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)


def solve_lines(grid, *, vertical_wins):
    height, width = len(grid), len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    by_color = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                by_color[value].append((r, c))
    horizontal = []
    vertical = []
    for color, points in by_color.items():
        for index, first in enumerate(points):
            for second in points[index + 1:]:
                if first[0] == second[0]:
                    horizontal.append((color, first[0], min(first[1], second[1]), max(first[1], second[1])))
                if first[1] == second[1]:
                    vertical.append((color, first[1], min(first[0], second[0]), max(first[0], second[0])))

    def paint_horizontal():
        for color, row, c0, c1 in horizontal:
            for column in range(c0, c1 + 1):
                output[row][column] = color

    def paint_vertical():
        for color, column, r0, r1 in vertical:
            for row in range(r0, r1 + 1):
                output[row][column] = color

    if vertical_wins:
        paint_horizontal()
        paint_vertical()
    else:
        paint_vertical()
        paint_horizontal()
    return output


def differences(left, right):
    return [
        [r, c, left[r][c], right[r][c]]
        for r in range(len(left))
        for c in range(len(left[0]))
        if left[r][c] != right[r][c]
    ]


seed = 0
start = 13
difficulty = None
grids = [gen.generate(seed, start + offset, difficulty=difficulty) for offset in range(4)]
receipt = Catalog(ROOT).apply(TASK, grids, reference="canonical", timeout=180)
authority_outputs = [item["output"] for item in receipt["results"]]
intended_outputs = [solve_lines(grid, vertical_wins=True) for grid in grids]
rival_outputs = [solve_lines(grid, vertical_wins=False) for grid in grids]
assert intended_outputs == authority_outputs
assert rival_outputs[:3] == authority_outputs[:3]
assert rival_outputs[3] != authority_outputs[3]

canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
assert all(solve_lines(pair["input"], vertical_wins=True) == pair["output"] for pair in canonical)
canonical_rival_fit = sum(
    solve_lines(pair["input"], vertical_wins=False) == pair["output"]
    for pair in canonical
)

report = {
    "schema": "arc-audit-reproduction-v1",
    "task_id": TASK,
    "finding": "horizontal-wins rival survives three generated demonstrations and changes query",
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "rule_hash_declared": getattr(gen, "RULE_HASH", None),
    "receipt_rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
    "seed": seed,
    "difficulty": difficulty,
    "sample_indices": list(range(start, start + 4)),
    "self_check": [gen.self_check(grid) for grid in grids],
    "canonical_horizontal_wins_fit": canonical_rival_fit,
    "canonical_pairs_total": len(canonical),
    "rival_fits_demonstrations": [
        rival_outputs[i] == authority_outputs[i] for i in range(3)
    ],
    "query_diff_cells": differences(authority_outputs[3], rival_outputs[3]),
    "semantic_contract_present": any(
        hasattr(gen, name)
        for name in ("lesson_identifiable", "LESSON_COMPETITORS", "SEMANTIC_RIVALS")
    ),
    "lesson": [
        {
            "sample_index": start + i,
            "shape": [len(grids[i]), len(grids[i][0])],
            "input": grids[i],
            "authority_output": authority_outputs[i],
            "horizontal_wins_output": rival_outputs[i],
        }
        for i in range(4)
    ],
}
OUT.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({
    "demo_fit": report["rival_fits_demonstrations"],
    "query_diff_cells": report["query_diff_cells"],
    "canonical_rival_fit": f"{canonical_rival_fit}/{len(canonical)}",
    "semantic_contract_present": report["semantic_contract_present"],
    "out": str(OUT),
}))
