from __future__ import annotations
import hashlib
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

TASK_ID = "f3be696a1ae4"
ROOT = find_root(__file__)
generator, source, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)

def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()

def describe(grid):
    colors = sorted({value for row in grid for value in row})
    axis = [c for c in range(len(grid[0])) if all(row[c] == 9 for row in grid)]
    non_axis = sorted({value for row in grid for value in row if value not in (0, 9)})
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "colors": colors,
        "non_axis_colors": non_axis,
        "axis_columns": axis,
        "sha256": digest(grid),
        "self_check": generator.self_check(grid),
    }

seed = 17
sample_index = 4
requests = {
    "default": {},
    "grid_h_14_grid_w_16": {"grid_h": 14, "grid_w": 16},
    "all_advertised_controls": {
        "grid_h": 14,
        "grid_w": 16,
        "palette_kind": "warm",
        "anchor_corner": True,
        "asymmetry_force": True,
        "palette_size": 1,
        "position_bias": "varied",
        "n_distinct_colors": 1,
        "texture": "warm",
    },
    "cool_texture": {"texture": "cool"},
}
results = {}
for name, overrides in requests.items():
    try:
        grid = generator.generate(seed, sample_index, difficulty="hard", **overrides)
    except Exception as exc:
        results[name] = {
            "overrides": overrides,
            "exception": f"{type(exc).__name__}: {exc}",
        }
    else:
        results[name] = {"overrides": overrides, "observed": describe(grid)}

payload = {
    "schema": "f3be696a1ae4-audit-override-probe-v1",
    "task_id": TASK_ID,
    "source_path": str(source.relative_to(ROOT)),
    "source_sha256": source_sha256,
    "seed": seed,
    "sample_index": sample_index,
    "difficulty": "hard",
    "results": results,
}
out = Path(__file__).with_name("override_probe.json")
out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print(json.dumps(payload, indent=2, sort_keys=True))
