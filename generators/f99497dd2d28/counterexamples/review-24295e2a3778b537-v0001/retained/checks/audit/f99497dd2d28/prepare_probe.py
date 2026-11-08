from __future__ import annotations
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, load_selected_generator

TASK = "f99497dd2d28"
REPO = Path.cwd()
OUT = REPO.parent / "checks/audit" / TASK
GEN, GEN_PATH, GEN_SHA = load_selected_generator(TASK, root=REPO)
PAIRS = canonical_pairs(TASK, root=REPO, labeled_only=True)


def shape_cells(grid):
    counts = {}
    for row in grid:
        for value in row:
            if value:
                counts[value] = counts.get(value, 0) + 1
    color = max(counts, key=counts.get)
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]


def normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return {(r - r0, c - c0) for r, c in cells}


def lr_symmetric(grid):
    cells = normalize(shape_cells(grid))
    width = max(c for _, c in cells) + 1
    return all((r, width - 1 - c) in cells for r, c in cells)


def ud_symmetric(grid):
    cells = normalize(shape_cells(grid))
    height = max(r for r, _ in cells) + 1
    return all((height - 1 - r, c) in cells for r, c in cells)


def bbox_height(grid):
    cells = normalize(shape_cells(grid))
    return max(r for r, _ in cells) + 1


def lr_only_rival(grid):
    output = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    if lr_symmetric(grid):
        row = (h - 1) // 2
        for col in range(w):
            output[row][col] = 3
    else:
        col = (w - 1) // 2
        for row in range(h):
            output[row][col] = 3
    return output


# Canonical pair 3 is the missing branch: LR and UD symmetric with even bbox height.
canonical_index = 3
canonical_grid = PAIRS[canonical_index]["input"]
assert lr_symmetric(canonical_grid)
assert ud_symmetric(canonical_grid)
assert bbox_height(canonical_grid) % 2 == 0
assert GEN.self_check(canonical_grid)

production = []
for band in ("easy", "medium", "hard"):
    for offset in range(10):
        branch = "row" if offset % 2 == 0 else "col"
        grid = GEN.generate(1000 + offset, offset, difficulty=band, branch=branch)
        production.append(
            {
                "difficulty": band,
                "seed": 1000 + offset,
                "sample_index": offset,
                "overrides": {"branch": branch},
                "self_check": GEN.self_check(grid, difficulty=band),
                "input": grid,
                "rival_output": lr_only_rival(grid),
                "lr_symmetric": lr_symmetric(grid),
                "ud_symmetric": ud_symmetric(grid),
                "bbox_height": bbox_height(grid),
            }
        )
assert all(not row["self_check"] for row in production)

inputs = [canonical_grid] + [row["input"] for row in production]
(OUT / "input.json").write_text(json.dumps({"inputs": inputs}, indent=2) + "\n")
(OUT / "probe-pre-racket.json").write_text(
    json.dumps(
        {
            "schema": "arcpuzzles-audit-probe-v1",
            "task_id": TASK,
            "generator_sha256": GEN_SHA,
            "generator_path": str(GEN_PATH.relative_to(REPO)),
            "canonical_index": canonical_index,
            "canonical_input": canonical_grid,
            "canonical_expected": PAIRS[canonical_index]["output"],
            "canonical_self_check": GEN.self_check(canonical_grid),
            "canonical_features": {
                "lr_symmetric": lr_symmetric(canonical_grid),
                "ud_symmetric": ud_symmetric(canonical_grid),
                "bbox_height": bbox_height(canonical_grid),
            },
            "canonical_rival_output": lr_only_rival(canonical_grid),
            "production": production,
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        indent=2,
        sort_keys=True,
    )
    + "\n"
)
print(json.dumps({"inputs": len(inputs), "generator_sha256": GEN_SHA, "canonical_self_check": GEN.self_check(canonical_grid)}, indent=2))
