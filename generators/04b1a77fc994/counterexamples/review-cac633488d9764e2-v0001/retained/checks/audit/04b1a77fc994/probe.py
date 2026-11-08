#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "04b1a77fc994"
ROOT = Path.cwd()
OUT = ROOT.parent / "checks" / "audit" / TASK_ID
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK_ID, root=ROOT)


def components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    rows = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        todo = [start]
        unseen.remove(start)
        cells = []
        while todo:
            r, c = todo.pop()
            cells.append((r, c))
            for nr, nc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if (nr, nc) in unseen and grid[nr][nc] == color:
                    unseen.remove((nr, nc)); todo.append((nr, nc))
        touches = sum((
            any(r == 0 for r, _ in cells),
            any(r == h - 1 for r, _ in cells),
            any(c == 0 for _, c in cells),
            any(c == w - 1 for _, c in cells),
        ))
        rows.append((cells, touches))
    return rows


def rival(grid):
    out = [[0 for _ in row] for row in grid]
    for cells, touches in components(grid):
        for r, c in cells:
            out[r][c] = touches + 1
    return out

records = []
inputs = []
for sample_index in range(1, 6):
    grid = GEN.generate(0, sample_index, difficulty="medium")
    inputs.append(grid)
    records.append({
        "seed": 0,
        "sample_index": sample_index,
        "difficulty": "medium",
        "profile": GEN.observe_overrides(grid).get("scene_profile"),
        "touch_counts": sorted(t for _, t in components(grid)),
        "self_check": GEN.self_check(grid, difficulty="medium", meta={}),
        "mirror_output": GEN.rule_mirror(grid),
        "rival_output": rival(grid),
    })
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "input.json").write_text(json.dumps(inputs, indent=2) + "\n")
(OUT / "prepared.json").write_text(json.dumps({
    "task_id": TASK_ID,
    "generator_path": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA,
    "rule_hash": getattr(GEN, "RULE_HASH", None),
    "records": records,
}, indent=2, sort_keys=True) + "\n")
print(json.dumps({"task_id": TASK_ID, "source_sha256": SOURCE_SHA, "pairs": len(records)}))
