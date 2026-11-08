#!/usr/bin/env python3
from __future__ import annotations

from collections import deque
import json
import os
from pathlib import Path
import sys

from reviewer_support import load_selected_generator

TASK = "22a206f031ef"
GEN_KWARGS = {
    "seed": 0,
    "sample_index": 0,
    "difficulty": "easy",
    "n_walls": 0,
    "n_seeds": 2,
}


def components_without_walls(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 5}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        q = deque([start])
        cells = []
        while q:
            r, c = q.popleft()
            cells.append((r, c))
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in unseen:
                    unseen.remove((nr, nc))
                    q.append((nr, nc))
        result.append(cells)
    return result


def main():
    module, source, digest = load_selected_generator(TASK, root=os.environ["ARCPUZZLES_HOME"])
    grid = module.generate(**GEN_KWARGS)
    components = components_without_walls(grid)
    component_summaries = []
    for cells in components:
        seeds = [
            {"row": r, "col": c, "color": grid[r][c]}
            for r, c in sorted(cells)
            if grid[r][c] not in {0, 5}
        ]
        component_summaries.append({"cell_count": len(cells), "seeds": seeds})
    facts = {
        "task_id": TASK,
        "generator_source": str(source),
        "generator_sha256": digest,
        "generate_kwargs": GEN_KWARGS,
        "grid": grid,
        "self_check": module.self_check(grid, difficulty="easy"),
        "non_wall_components": component_summaries,
        "violates_documented_one_seed_per_room": any(len(row["seeds"]) != 1 for row in component_summaries),
    }
    print(json.dumps(facts, indent=2))


if __name__ == "__main__":
    main()
