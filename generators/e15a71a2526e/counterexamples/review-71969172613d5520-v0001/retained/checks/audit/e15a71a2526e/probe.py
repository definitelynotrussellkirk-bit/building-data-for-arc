from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "e15a71a2526e"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK_ID, root=ROOT)
SEED = 812
SAMPLE_INDEX = 4
DIFFICULTY = "easy"
OVERRIDES = {
    "grid_h": 5,
    "grid_w": 6,
    "frame_size_kind": "small",
    "n_interior_8s": 5,
}

grid = GEN.generate(SEED, SAMPLE_INDEX, difficulty=DIFFICULTY, **OVERRIDES)
eights = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
rmin = min(r for r, _ in eights)
rmax = max(r for r, _ in eights)
cmin = min(c for _, c in eights)
cmax = max(c for _, c in eights)
interior_eights = sum(
    grid[r][c] == 8
    for r in range(rmin + 1, rmax)
    for c in range(cmin + 1, cmax)
)
report = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK_ID,
    "generator_path": str(SOURCE),
    "generator_sha256": SOURCE_SHA,
    "seed": SEED,
    "sample_index": SAMPLE_INDEX,
    "difficulty": DIFFICULTY,
    "overrides": OVERRIDES,
    "shape": [len(grid), len(grid[0])],
    "bbox": [rmin, cmin, rmax, cmax],
    "requested_n_interior_8s": OVERRIDES["n_interior_8s"],
    "observed_n_interior_8s": interior_eights,
    "self_check": GEN.self_check(grid),
    "finding": "explicit n_interior_8s=5 is silently clamped to the 4x4 frame's capacity-minus-two value 2",
}
outdir = Path(__file__).resolve().parent
(outdir / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
(outdir / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
