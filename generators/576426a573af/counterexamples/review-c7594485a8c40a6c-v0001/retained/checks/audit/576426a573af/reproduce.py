#!/usr/bin/env python3
"""Reproduce the multi-conflict teaching gap in generator 576426a573af."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "576426a573af"
HERE = Path(__file__).resolve().parent


def conflict_orbits(grid):
    h, w = len(grid), len(grid[0])
    return [
        (r, h - 1 - r, c)
        for r in range(h // 2)
        for c in range(w)
        if grid[r][c] != 0
        and grid[h - 1 - r][c] != 0
        and grid[r][c] != grid[h - 1 - r][c]
    ]


def preserve_first_conflict_only(grid):
    """Plausible count-limited rival: true overlay except later conflicts swap."""
    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)
    conflict_index = 0
    for r in range(h // 2):
        mirror = h - 1 - r
        for c in range(w):
            top, bottom = grid[r][c], grid[mirror][c]
            if top == 0 and bottom != 0:
                out[r][c] = bottom
            elif bottom == 0 and top != 0:
                out[mirror][c] = top
            elif top != 0 and bottom != 0 and top != bottom:
                if conflict_index > 0:
                    out[r][c], out[mirror][c] = bottom, top
                conflict_index += 1
    return out


def main():
    gen, source_path, source_sha = load_selected_generator(TASK_ID, root=find_root(HERE.parents[2] / "repo"))
    sampled = 0
    maximum_conflicts = 0
    profile_counts = {"none": 0, "easy": 0, "medium": 0, "hard": 0}
    for difficulty in (None, "easy", "medium", "hard"):
        key = "none" if difficulty is None else difficulty
        for index in range(256):
            grid = gen.generate(100_000 + index, index, difficulty=difficulty)
            errors = gen.self_check(grid)
            assert errors == [], (difficulty, index, errors)
            count = len(conflict_orbits(grid))
            maximum_conflicts = max(maximum_conflicts, count)
            profile_counts[key] += count
            assert count <= 1, (difficulty, index, count)
            assert preserve_first_conflict_only(grid) == gen.rule_mirror(grid)
            sampled += 1

    grid = json.loads((HERE / "input.json").read_text(encoding="utf-8"))
    receipt = json.loads((HERE / "racket.json").read_text(encoding="utf-8"))
    expected = receipt["results"][0]["output"]
    rival = preserve_first_conflict_only(grid)
    assert gen.self_check(grid) == []
    assert len(conflict_orbits(grid)) == 2
    assert expected == gen.rule_mirror(grid)
    assert rival != expected
    (HERE / "rival.json").write_text(json.dumps(rival, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "task_id": TASK_ID,
        "generator_path": str(source_path),
        "generator_sha256": source_sha,
        "rule_hash": gen.RULE_HASH,
        "sampled_generated_inputs": sampled,
        "sample_spec": "difficulty in [None,easy,medium,hard], index 0..255, seed 100000+index",
        "maximum_conflicting_orbits_observed": maximum_conflicts,
        "total_conflicting_orbits_by_band": profile_counts,
        "crafted_input_self_check": [],
        "crafted_conflicting_orbits": 2,
        "rival_matches_all_sampled_generated_inputs": True,
        "rival_differs_on_crafted_lawful_input": True,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
