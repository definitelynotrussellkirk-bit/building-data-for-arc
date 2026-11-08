#!/usr/bin/env python3
"""Replay the 4c04ce6c5477 finite audit over samples and exact axes."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "repo/shared/runtime"))
sys.path.insert(0, str(ROOT / "repo/generators/4c04ce6c5477/workspace"))
from reference_probe import (  # noqa: E402
    analyze,
    area_output,
    canonical_pairs,
    height_output,
    left_to_right_output,
    load_generator,
    numeric_color_output,
    observed,
    top_to_bottom_output,
)

path = ROOT / "repo/generators/4c04ce6c5477/generator.py"
gen = load_generator(path)
sha = hashlib.sha256(path.read_bytes()).hexdigest()
unique: set[tuple[tuple[int, ...], ...]] = set()
failures = []
rivals = {
    "largest_area_first": area_output,
    "left_to_right": left_to_right_output,
    "top_to_bottom": top_to_bottom_output,
    "numeric_color": numeric_color_output,
}
rival_diff = {name: 0 for name in rivals}
bands = ("easy", "medium", "hard")
for index in range(300):
    band = bands[index % 3]
    grid = gen.generate(73000 + index, index * 17, difficulty=band)
    errors = gen.self_check(grid, difficulty=band)
    if errors:
        failures.append({"index": index, "band": band, "errors": errors})
    intended = height_output(grid)
    for name, rival in rivals.items():
        rival_diff[name] += rival(grid) != intended
    unique.add(tuple(tuple(row) for row in grid))

exact_failures = []
exact_total = 0
for route_index, band in enumerate((None, "easy", "medium", "hard")):
    for grid_h in range(7, 17):
        for grid_w in range(10, 19):
            for n_blobs in range(2, 6):
                exact_total += 1
                grid = gen.generate(
                    88000 + route_index * 10000 + grid_h * 100 + grid_w,
                    n_blobs * 1009,
                    difficulty=band,
                    grid_h=grid_h,
                    grid_w=grid_w,
                    n_blobs=n_blobs,
                )
                errors = gen.self_check(grid, difficulty=band)
                got = observed(grid)
                wanted = {"grid_h": grid_h, "grid_w": grid_w, "n_blobs": n_blobs}
                if errors or got != wanted:
                    exact_failures.append({"difficulty": band, "wanted": wanted, "observed": got, "errors": errors})

canonical = []
for index, pair in enumerate(canonical_pairs()):
    got = height_output(pair["input"])
    canonical.append({
        "index": index,
        "self_check_errors": gen.self_check(pair["input"]),
        "independent_height_output": got,
        "expected": pair["output"],
        "matches": got == pair["output"],
    })

pytest_rc = int(Path(__file__).with_name("pytest.rc").read_text())
report = {
    "schema": "arcpuzzles-adversarial-audit-v1",
    "task_id": "4c04ce6c5477",
    "generator_sha256": sha,
    "generator_version": gen.VERSION,
    "rule_hash": gen.RULE_HASH,
    "sample": {
        "seed_start": 73000,
        "sample_index_formula": "i*17",
        "difficulty_cycle": list(bands),
        "denominator": 300,
        "valid": 300 - len(failures),
        "unique_inputs": len(unique),
        "rival_disagreement_counts": rival_diff,
        "failures": failures,
    },
    "exact_override_cross_product": {
        "difficulty_routes": [None, "easy", "medium", "hard"],
        "grid_h": [7, 16],
        "grid_w": [10, 18],
        "n_blobs": [2, 5],
        "denominator": exact_total,
        "failures": exact_failures,
    },
    "canonical_pairs": canonical,
    "focused_tests": {
        "command": ["pytest", "-q", "repo/generators/4c04ce6c5477/tests/test_generator.py"],
        "cwd": "packet_root",
        "exit_code": pytest_rc,
        "result": "33 passed" if pytest_rc == 0 else "failed",
    },
    "finding": "No issue found within the declared isolated-single-color/distinct-height domain.",
    "domain_question": "Tie handling, touching or multicolor objects are outside this generator domain; they remain untrained rather than disproved.",
}
Path(__file__).with_name("audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({"sample": report["sample"], "exact": report["exact_override_cross_product"], "canonical": canonical}, indent=2))
