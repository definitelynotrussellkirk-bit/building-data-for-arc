#!/usr/bin/env python3
"""Reproduce the mixed-seed-count teaching gap in generator f7660051ec70."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "f7660051ec70"
HERE = Path(__file__).resolve().parent


def frames(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != 1 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for nr, nc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 1 and (nr,nc) not in seen:
                        seen.add((nr,nc)); stack.append((nr,nc))
            r1 = min(r for r, _ in cells); r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells); c2 = max(c for _, c in cells)
            count = sum(
                grid[r][c] == 2
                for r in range(r1 + 1, r2)
                for c in range(c1 + 1, c2)
            )
            result.append({"r1": r1, "c1": c1, "r2": r2, "c2": c2, "seed_count": count})
    return sorted(result, key=lambda f: (f["r1"], f["c1"]))


def fill_only_first_seed_multiplicity(grid):
    """Rival: fill only frames matching the first seeded frame's seed count."""
    parsed = frames(grid)
    first_count = next(frame["seed_count"] for frame in parsed if frame["seed_count"] > 0)
    out = deepcopy(grid)
    for frame in parsed:
        if frame["seed_count"] != first_count:
            continue
        for r in range(frame["r1"] + 1, frame["r2"]):
            for c in range(frame["c1"] + 1, frame["c2"]):
                if out[r][c] == 0:
                    out[r][c] = 3
    return out


def main():
    gen, source_path, source_sha = load_selected_generator(TASK_ID, root=find_root(HERE.parents[2] / "repo"))
    sampled = 0
    mixed_generated = 0
    for difficulty in (None, "easy", "medium", "hard"):
        for index in range(256):
            grid = gen.generate(200_000 + index, index, difficulty=difficulty)
            errors = gen.self_check(grid)
            assert errors == [], (difficulty, index, errors)
            counts = {frame["seed_count"] for frame in frames(grid) if frame["seed_count"] > 0}
            mixed_generated += len(counts) > 1
            assert len(counts) == 1, (difficulty, index, counts)
            assert fill_only_first_seed_multiplicity(grid) == gen.rule_mirror(grid)
            sampled += 1

    grid = json.loads((HERE / "input.json").read_text(encoding="utf-8"))
    receipt = json.loads((HERE / "racket.json").read_text(encoding="utf-8"))
    expected = receipt["results"][0]["output"]
    rival = fill_only_first_seed_multiplicity(grid)
    facts = gen.observe_overrides(grid)
    assert gen.self_check(grid) == []
    assert facts["seed_count"] == "mixed"
    assert expected == gen.rule_mirror(grid)
    assert rival != expected
    (HERE / "rival.json").write_text(json.dumps(rival, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "task_id": TASK_ID,
        "generator_path": str(source_path),
        "generator_sha256": source_sha,
        "rule_hash": gen.RULE_HASH,
        "sampled_generated_inputs": sampled,
        "sample_spec": "difficulty in [None,easy,medium,hard], index 0..255, seed 200000+index",
        "mixed_seed_count_generated_inputs": mixed_generated,
        "crafted_input_self_check": [],
        "crafted_observed_axes": facts,
        "rival_matches_all_sampled_generated_inputs": True,
        "rival_differs_on_crafted_lawful_input": True,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
