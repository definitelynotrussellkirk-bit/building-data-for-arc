from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK = "0d85790c3f38"
ROOT = find_root(__file__)
module, source_path, source_sha256 = load_selected_generator(TASK, root=ROOT)


def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def run(overrides):
    grid = module.generate(20261011, 7, difficulty="medium", **overrides)
    return {
        "overrides": overrides,
        "sha256": digest(grid),
        "shape": [len(grid), len(grid[0])],
        "nonzero_colors": sorted({v for row in grid for v in row if v}),
        "nonzero_count": sum(v != 0 for row in grid for v in row),
        "self_check": module.self_check(grid, difficulty="medium"),
        "grid": grid,
    }


cases = {
    "texture_default": run({"texture": "default"}),
    "texture_rainbow": run({"texture": "rainbow"}),
    "distinct_1": run({"n_distinct_colors": 1}),
    "distinct_9": run({"n_distinct_colors": 9}),
    "palette_sparse": run({"palette_kind": "sparse"}),
    "palette_dense": run({"palette_kind": "dense"}),
}
report = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK,
    "source_path": source_path.relative_to(ROOT).as_posix(),
    "source_sha256": source_sha256,
    "seed": 20261011,
    "sample_index": 7,
    "difficulty": "medium",
    "cases": cases,
    "comparisons": {
        "helpful_texture_identical": cases["texture_default"]["sha256"] == cases["texture_rainbow"]["sha256"],
        "distinct_color_extremes_identical": cases["distinct_1"]["sha256"] == cases["distinct_9"]["sha256"],
        "palette_kinds_identical": cases["palette_sparse"]["sha256"] == cases["palette_dense"]["sha256"],
        "requested_one_color_actual_count": len(cases["distinct_1"]["nonzero_colors"]),
    },
    "finding": (
        "Advertised helpful texture, palette_kind, and n_distinct_colors controls "
        "do not affect ordinary generation; exact override opposites return the same grid."
    ),
}
out = Path(__file__).with_name("evidence.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({"out": str(out), "source_sha256": source_sha256, **report["comparisons"]}, indent=2))
assert report["comparisons"]["helpful_texture_identical"]
assert report["comparisons"]["distinct_color_extremes_identical"]
assert report["comparisons"]["palette_kinds_identical"]
assert report["comparisons"]["requested_one_color_actual_count"] != 1
