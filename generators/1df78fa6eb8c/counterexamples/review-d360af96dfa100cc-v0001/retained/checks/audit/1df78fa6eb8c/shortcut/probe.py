from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, load_selected_generator

TASK = "1df78fa6eb8c"
ROOT = Path.cwd()
gen, source_path, source_sha256 = load_selected_generator(TASK, root=ROOT)


def split_panels(grid):
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    boundaries = [-1, *dividers, w]
    return [[row[boundaries[i] + 1:boundaries[i + 1]] for row in grid] for i in range(len(boundaries) - 1)]


def occupied(panel):
    return [(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value not in (0, 9)]


def normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def variants(cells):
    cur = list(normalize(cells))
    result = set()
    for _ in range(4):
        result.add(normalize(cur))
        result.add(normalize([(r, -c) for r, c in cur]))
        max_r = max(r for r, _ in cur)
        cur = [(c, max_r - r) for r, c in cur]
    return result


def recolor(panel):
    return [[8 if value not in (0, 9) else 0 for value in row] for row in panel]


def predict(grid, max_pairs=None):
    panels = split_panels(grid)
    query_variants = variants(occupied(panels[-1]))
    pairs = [(panels[i], panels[i + 1], i // 2) for i in range(0, len(panels) - 1, 2)]
    if max_pairs is not None:
        pairs = pairs[:max_pairs]
    for first, second, pair_index in pairs:
        if normalize(occupied(first)) in query_variants:
            return recolor(second), pair_index
    h, w = len(panels[1]), len(panels[1][0])
    return [[0] * w for _ in range(h)], None


def diff_cells(expected, actual):
    return [
        {"row": r, "col": c, "expected": expected[r][c], "rival": actual[r][c]}
        for r in range(len(expected))
        for c in range(len(expected[0]))
        if expected[r][c] != actual[r][c]
    ]

canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
canonical_rows = []
for pair in canonical:
    intended, intended_pair = predict(pair["input"])
    rival, rival_pair = predict(pair["input"], max_pairs=2)
    assert intended == pair["output"]
    canonical_rows.append({
        "split": pair.get("split"),
        "intended_pair_index": intended_pair,
        "rival_pair_index": rival_pair,
        "rival_matches": rival == pair["output"],
        "self_check_errors": gen.self_check(pair["input"]),
    })
assert all(row["self_check_errors"] for row in canonical_rows)
assert any(row["intended_pair_index"] == 2 for row in canonical_rows)

generated = 0
rival_matches = 0
panel_histogram = {}
for difficulty in ("easy", "medium", "hard"):
    for seed in range(100):
        for sample_index in range(20):
            grid = gen.generate(seed, sample_index, difficulty=difficulty)
            panels = len(split_panels(grid))
            panel_histogram[str(panels)] = panel_histogram.get(str(panels), 0) + 1
            true_output, _ = predict(grid)
            rival_output, _ = predict(grid, max_pairs=2)
            generated += 1
            rival_matches += int(true_output == rival_output)
assert rival_matches == generated
assert set(panel_histogram) <= {"3", "5"}

counterexample_pair = next(
    pair for pair in canonical
    if predict(pair["input"])[1] == 2
)
true_output, true_pair = predict(counterexample_pair["input"])
rival_output, rival_pair = predict(counterexample_pair["input"], max_pairs=2)
assert true_output == counterexample_pair["output"] and true_output != rival_output

out_dir = ROOT.parent / "checks" / "audit" / TASK / "shortcut"
(out_dir / "input.json").write_text(json.dumps(counterexample_pair["input"], indent=2) + "\n")
report = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK,
    "generator_path": str(source_path.relative_to(ROOT)),
    "generator_sha256": source_sha256,
    "rule_hash": "a41328ea3d0a",
    "finding": "generator and self_check cover only one or two lookup pairs, while every canonical input has three pairs",
    "associated_rival": "search only the first two panel pairs; ignore any third pair",
    "canonical_rows": canonical_rows,
    "generated_draws": generated,
    "generated_seed_range": [0, 99],
    "generated_sample_index_range": [0, 19],
    "difficulties": ["easy", "medium", "hard"],
    "generated_panel_histogram": panel_histogram,
    "generated_rival_matches": rival_matches,
    "counterexample": {
        "source": "canonical train pair whose query matches the third lookup pair",
        "input": counterexample_pair["input"],
        "self_check_errors": gen.self_check(counterexample_pair["input"]),
        "intended_pair_index": true_pair,
        "rival_pair_index": rival_pair,
        "true_output": true_output,
        "rival_output": rival_output,
        "differing_cells": diff_cells(true_output, rival_output),
    },
    "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}
(out_dir / "comparison.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "task_id": TASK,
    "generator_sha256": source_sha256,
    "canonical_rows": canonical_rows,
    "generated_draws": generated,
    "generated_panel_histogram": panel_histogram,
    "generated_rival_matches": rival_matches,
}, indent=2))
