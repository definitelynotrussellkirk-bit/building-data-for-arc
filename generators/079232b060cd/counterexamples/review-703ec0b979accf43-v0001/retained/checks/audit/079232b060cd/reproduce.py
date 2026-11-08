from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK = "079232b060cd"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)
OUT = ROOT.parent / "checks" / "audit" / TASK
kwargs = {
    "difficulty": None,
    "texture": "crossing",
    "grid_h": 9,
    "grid_w": 10,
    "seed_count": 2,
}
grid = GEN.generate(23, 0, **kwargs)
mirror = GEN._mirror(grid)
# These are deterministic for the source hash above and expose the failed branch.
top = {"row": 0, "column": 6, "color": grid[0][6]}
side = {"row": 6, "column": 9, "color": grid[6][9]}
intersection = (side["row"], top["column"])
row, col = intersection
# Trace source-grid walls, because walls stop beams even if another beam paints the crossing.
top_reaches = all(grid[r][col] != 8 for r in range(1, row + 1))
horizontal_cols = range(col, side["column"]) if side["column"] == len(grid[0]) - 1 else range(side["column"] + 1, col + 1)
side_reaches = all(grid[row][c] != 8 for c in horizontal_cols)
report = {
    "schema": "audit-crossing-texture-v2",
    "task_id": TASK,
    "generator_path": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA256,
    "seed": 23,
    "sample_index": 0,
    "difficulty": None,
    "overrides": {k: v for k, v in kwargs.items() if k != "difficulty"},
    "self_check": GEN.self_check(grid),
    "top_seed": top,
    "side_seed": side,
    "intersection": {
        "row": row,
        "column": col,
        "input": grid[row][col],
        "mirror_output": mirror[row][col],
        "top_beam_reaches": top_reaches,
        "side_beam_reaches": side_reaches,
    },
    "blocking_wall": {"row": 4, "column": 6, "color": grid[4][6]},
    "input": grid,
    "mirror_output": mirror,
}
assert report["self_check"] == []
assert grid[4][6] == 8
assert not top_reaches and side_reaches
assert mirror[row][col] == side["color"] != top["color"]
(OUT / "crossing_witness.json").write_text(json.dumps(report, indent=2) + "\n")
(OUT / "input.json").write_text(json.dumps({"input": grid}, indent=2) + "\n")
print(json.dumps({k: report[k] for k in ("task_id", "generator_sha256", "intersection", "blocking_wall")}, indent=2))
