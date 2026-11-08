from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import deque
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

TASK_ID = "74d1cf8c8502"
ROOT = Path(__file__).resolve().parents[3] / "repo"
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location("audit_generator_74d1cf8c8502", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def components8(grid):
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 6}
    out = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        comp = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == dc == 0:
                        continue
                    p = (r + dr, c + dc)
                    if p in remaining:
                        remaining.remove(p)
                        comp.add(p)
                        queue.append(p)
        out.append(sorted(comp))
    return out


def bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def rival_8_connected(grid):
    out = [row[:] for row in grid]
    for cells in components8(grid):
        r1, c1, r2, c2 = bbox(cells)
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if r in (r1, r2) or c in (c1, c2):
                    out[r][c] = 2
    return out


def witness():
    grid = [[0] * 12 for _ in range(10)]
    for r, c in ((2, 2), (2, 3), (3, 3), (4, 4), (4, 5), (5, 4)):
        grid[r][c] = 6
    return grid


def sha_grid(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


pairs = canonical_pairs(TASK_ID, root=ROOT)
canonical_records = []
for pair in pairs:
    prediction = rival_8_connected(pair["input"])
    canonical_records.append({
        "variant": pair["variant"],
        "split": pair["split"],
        "pair_index": pair["pair_index"],
        "matches": prediction == pair["output"],
        "input_sha256": sha_grid(pair["input"]),
    })

sample_records = []
for band in ("easy", "medium", "hard"):
    matches = 0
    unique = set()
    for sample_index in range(200):
        grid = GEN.generate(90210, sample_index, difficulty=band)
        unique.add(sha_grid(grid))
        matches += rival_8_connected(grid) == GEN.rule_mirror(grid)
    sample_records.append({
        "difficulty": band,
        "seed": 90210,
        "sample_indices": [0, 199],
        "matches": matches,
        "total": 200,
        "unique_inputs": len(unique),
    })

grid = witness()
intended = GEN.rule_mirror(grid)
rival = rival_8_connected(grid)
diffs = [
    {"row": r, "column": c, "intended": intended[r][c], "rival": rival[r][c]}
    for r in range(len(grid))
    for c in range(len(grid[0]))
    if intended[r][c] != rival[r][c]
]
report = {
    "schema": "74d1cf8c8502-connectivity-audit-v1",
    "task_id": TASK_ID,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "rule_hash": GEN.RULE_HASH,
    "rival": "Treat diagonally touching magenta cells as one 8-connected object, then outline each resulting bounding box.",
    "canonical_fit": {
        "matches": sum(row["matches"] for row in canonical_records),
        "total": len(canonical_records),
        "records": canonical_records,
    },
    "generated_fit": sample_records,
    "witness": {
        "input": grid,
        "input_sha256": sha_grid(grid),
        "current_self_check_errors": GEN.self_check(grid),
        "intended_python": intended,
        "rival_output": rival,
        "differing_cells": diffs,
        "four_connected_components": len(GEN._six_components(grid)),
        "eight_connected_components": len(components8(grid)),
    },
    "limits": [
        "The witness is a lawful input for the selected Racket expression but is intentionally outside the current sampler/validator because its object boxes lack the required moat.",
        "The generated-fit panel covers 200 indices per band at one seed; it is not an exhaustive proof over all seeds.",
    ],
}
out = Path(__file__).with_name("probe-report.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
Path(__file__).with_name("input.json").write_text(json.dumps(grid, indent=2) + "\n")
Path(__file__).with_name("rival.json").write_text(json.dumps(rival, indent=2) + "\n")
print(json.dumps({
    "canonical_fit": f"{report['canonical_fit']['matches']}/{report['canonical_fit']['total']}",
    "generated_fit": {row['difficulty']: f"{row['matches']}/{row['total']}" for row in sample_records},
    "self_check_errors": report['witness']['current_self_check_errors'],
    "four_components": report['witness']['four_connected_components'],
    "eight_components": report['witness']['eight_connected_components'],
    "differing_cell_count": len(diffs),
    "first_difference": diffs[0],
}, indent=2, sort_keys=True))
