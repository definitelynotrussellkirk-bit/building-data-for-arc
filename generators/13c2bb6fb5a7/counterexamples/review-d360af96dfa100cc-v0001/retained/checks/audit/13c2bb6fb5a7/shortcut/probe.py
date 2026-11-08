from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, load_selected_generator

TASK = "13c2bb6fb5a7"
ROOT = Path.cwd()
gen, source_path, source_sha256 = load_selected_generator(TASK, root=ROOT)


def crop_to_content(grid):
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    if not points:
        return []
    r0 = min(r for r, _ in points)
    r1 = max(r for r, _ in points)
    c0 = min(c for _, c in points)
    c1 = max(c for _, c in points)
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def border_strip_rival(grid):
    stripped = [list(row) for row in grid]
    h, w = len(stripped), len(stripped[0])
    for c in range(w):
        stripped[0][c] = 0
        stripped[h - 1][c] = 0
    for r in range(h):
        stripped[r][0] = 0
        stripped[r][w - 1] = 0
    return crop_to_content(stripped)


def diffs(expected, actual):
    out = []
    h = max(len(expected), len(actual))
    for r in range(h):
        erow = expected[r] if r < len(expected) else []
        arow = actual[r] if r < len(actual) else []
        for c in range(max(len(erow), len(arow))):
            ev = erow[c] if c < len(erow) else None
            av = arow[c] if c < len(arow) else None
            if ev != av:
                out.append({"row": r, "col": c, "expected": ev, "rival": av})
    return out

canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
canonical_fit = [border_strip_rival(pair["input"]) == pair["output"] for pair in canonical]
assert all(canonical_fit)

generated = 0
edge_touching = 0
rival_matches = 0
for difficulty in ("easy", "medium", "hard"):
    for seed in range(100):
        for sample_index in range(20):
            grid = gen.generate(seed, sample_index, difficulty=difficulty)
            generated += 1
            h, w = len(grid), len(grid[0])
            touches = any(grid[0][c] or grid[h - 1][c] for c in range(w)) or any(
                grid[r][0] or grid[r][w - 1] for r in range(h)
            )
            edge_touching += int(touches)
            rival_matches += int(border_strip_rival(grid) == crop_to_content(grid))
assert edge_touching == 0
assert rival_matches == generated

counterexample = [
    [1, 1, 0, 0, 0, 0],
    [1, 0, 0, 0, 0, 0],
    [0, 0, 0, 2, 2, 0],
    [0, 0, 0, 2, 0, 0],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
]
self_check = gen.self_check(counterexample)
assert self_check == []
true_output = crop_to_content(counterexample)
rival_output = border_strip_rival(counterexample)
assert true_output != rival_output

out_dir = ROOT.parent / "checks" / "audit" / TASK / "shortcut"
(out_dir / "input.json").write_text(json.dumps(counterexample, indent=2) + "\n")
report = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK,
    "generator_path": str(source_path.relative_to(ROOT)),
    "generator_sha256": source_sha256,
    "rule_hash": "88475e062f41",
    "rival": "erase the outermost input border, then crop to the remaining nonzero bounding box",
    "canonical_labeled_pairs": len(canonical),
    "canonical_rival_fit": canonical_fit,
    "generated_draws": generated,
    "generated_seed_range": [0, 99],
    "generated_sample_index_range": [0, 19],
    "difficulties": ["easy", "medium", "hard"],
    "generated_edge_touching_inputs": edge_touching,
    "generated_rival_matches": rival_matches,
    "counterexample": {
        "input": counterexample,
        "self_check_errors": self_check,
        "true_output": true_output,
        "rival_output": rival_output,
        "differing_cells": diffs(true_output, rival_output),
    },
    "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}
(out_dir / "comparison.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: report[k] for k in ("task_id", "generator_sha256", "canonical_labeled_pairs", "generated_draws", "generated_edge_touching_inputs", "generated_rival_matches")}, indent=2))
