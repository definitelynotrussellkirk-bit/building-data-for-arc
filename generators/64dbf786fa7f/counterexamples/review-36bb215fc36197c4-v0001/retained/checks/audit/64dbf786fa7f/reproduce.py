from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "64dbf786fa7f"
ROOT = find_root(__file__)
gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)


def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def stats(grid):
    shape_colors = sorted({v for row in grid for v in row if v >= 3})
    return {
        "sha256": digest(grid),
        "dims": [len(grid), len(grid[0])],
        "nonzero_colors": sorted({v for row in grid for v in row if v != 0}),
        "shape_colors": shape_colors,
        "n_shape_colors": len(shape_colors),
        "self_check": gen.self_check(grid),
    }


seed, sample_index, difficulty = 12345, 7, "medium"
base = gen.generate(seed, sample_index, difficulty=difficulty)
cases = {
    "default": base,
    "palette_kind_warm": gen.generate(seed, sample_index, difficulty=difficulty, palette_kind="warm"),
    "position_bias": gen.generate(seed, sample_index, difficulty=difficulty, position_bias="vector_plus_shapes"),
    "n_distinct_colors_9": gen.generate(seed, sample_index, difficulty=difficulty, n_distinct_colors=9),
    "unknown_axis": gen.generate(seed, sample_index, difficulty=difficulty, invented_axis=42),
}
errors = {}
try:
    gen.generate(seed, sample_index, difficulty="hard", grid_h=23)
except Exception as exc:
    errors["declared_grid_h_23_hard"] = {"type": type(exc).__name__, "message": str(exc)}

report = {
    "task_id": TASK_ID,
    "generator_path": str(Path(source_path).relative_to(ROOT)),
    "generator_sha256": source_sha256,
    "reproducer": {"seed": seed, "sample_index": sample_index, "difficulty": difficulty},
    "cases": {
        name: {**stats(grid), "equals_default": grid == base}
        for name, grid in cases.items()
    },
    "errors": errors,
    "findings": {
        "ignored_or_unknown_axes_equal_default": [
            name for name, grid in cases.items() if name != "default" and grid == base
        ],
        "requested_n_distinct_colors": 9,
        "observed_shape_colors": stats(cases["n_distinct_colors_9"])["n_shape_colors"],
        "declared_grid_h_23_rejected_in_hard": "declared_grid_h_23_hard" in errors,
    },
}
Path(__file__).with_name("report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report["findings"], indent=2, sort_keys=True))
