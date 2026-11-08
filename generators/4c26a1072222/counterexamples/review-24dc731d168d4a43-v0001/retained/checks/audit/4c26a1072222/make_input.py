#!/usr/bin/env python3
"""Construct a lawful source-color/transform decoupling counterexample."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared/runtime")]
from reviewer_support import find_root, load_selected_generator

TASK = "4c26a1072222"
gen, source_path, source_sha256 = load_selected_generator(TASK, root=find_root(__file__))

seed = 123
sample_index = 0
grid = gen.generate(
    seed,
    sample_index,
    difficulty="easy",
    n_bands=3,
    first_transform="rotate_cw",
)
original = [row[:] for row in grid]

# The production sampler reserves 3-color A blocks for transpose/anti-transpose.
# The authority and validator do not: this verified pattern selects rotate_cw (4)
# uniquely while using three source colors.
pattern = gen._PATTERN_BANK[(3, 4, "identity")][0]
palette = []
for row in grid:
    for value in row:
        if value and value not in palette:
            palette.append(value)
source_colors = palette[:3]
a_block = [[source_colors[symbol] for symbol in row] for row in pattern]
b_block = gen._transform(a_block, 4)
for row in range(2):
    for col in range(2):
        grid[row][col] = a_block[row][col]
        grid[row][3 + col] = b_block[row][col]

info, errors = gen._analyze(grid)
assert not errors, errors
assert info["bands"][0]["source_color_count"] == 3
assert info["bands"][0]["transform"] == 4
assert gen.observe_overrides(grid) == {"n_bands": 3, "first_transform": "rotate_cw"}
assert len({value for row in grid for value in row if value}) == 8

out_dir = Path(__file__).resolve().parent
(out_dir / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
record = {
    "schema": "4c26a1072222-audit-input-construction-v1",
    "task_id": TASK,
    "generator_path": str(source_path.relative_to(REPO)),
    "generator_sha256": source_sha256,
    "rule_hash": gen.RULE_HASH,
    "seed": seed,
    "sample_index": sample_index,
    "difficulty": "easy",
    "overrides": {"n_bands": 3, "first_transform": "rotate_cw"},
    "mutation": "replace first-band 2-color rotate_cw A/B with an authority-selected 3-color rotate_cw A/B",
    "pattern": pattern,
    "source_colors": source_colors,
    "original_input": original,
    "counterexample_input": grid,
    "self_check": gen.self_check(grid),
    "strict_canonical_like": gen.strict_canonical_like(grid),
    "observed_overrides": gen.observe_overrides(grid),
    "first_band_signature": {
        "source_color_count": info["bands"][0]["source_color_count"],
        "transform_index": info["bands"][0]["transform"],
        "transform_name": gen.TRANSFORM_NAMES[info["bands"][0]["transform"]],
        "mapping": sorted(info["bands"][0]["mapping"].items()),
    },
    "input_sha256": hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest(),
}
(out_dir / "construction.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "input": str((out_dir / "input.json").relative_to(WORK)),
    "generator_sha256": source_sha256,
    "self_check": record["self_check"],
    "first_band_signature": record["first_band_signature"],
}, sort_keys=True))
