from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

repo = Path.cwd()
sys.path.insert(0, str(repo / "shared" / "runtime"))
source_path = repo / "generators" / "3fcea70c3acf" / "generator.py"
spec = importlib.util.spec_from_file_location("audit_3fc_generator", source_path)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {source_path}")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def components(grid):
    unseen = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    result = []
    while unseen:
        start = unseen.pop()
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            color = grid[r][c]
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                rr, cc = point
                if point in unseen and grid[rr][cc] == color:
                    unseen.remove(point)
                    cells.add(point)
                    stack.append(point)
        result.append(cells)
    return result


def stats(grid):
    comps = components(grid)
    colors = sorted({value for row in grid for value in row if value})
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "object_count": len(comps),
        "object_sizes": sorted((len(cells) for cells in comps), reverse=True),
        "nonzero_colors": colors,
        "self_check": gen.self_check(grid),
    }


seed = 18016
sample_index = 18016
requested = {"n_objs": 4}
grid = gen.generate(seed, sample_index, difficulty="hard", **requested)
repeat = gen.generate(seed, sample_index, difficulty="hard", **requested)

inert_seed = 2718
inert_index = 1
baseline = gen.generate(inert_seed, inert_index, n_objs=2)
inert = gen.generate(
    inert_seed,
    inert_index,
    n_objs=2,
    palette_size=4,
    n_distinct_colors=4,
)
unknown = gen.generate(inert_seed, inert_index, n_objs=2, typo_axis=1)
equal_sizes = gen.generate(inert_seed, inert_index, texture="equal_sizes")

result = {
    "schema": "audit-probe-v1",
    "task_id": gen.TASK_ID,
    "generator_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
    "silent_shortening": {
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": "hard",
        "requested_overrides": requested,
        "deterministic_repeat": repeat == grid,
        "stats": stats(grid),
        "grid": grid,
    },
    "inert_count_aliases": {
        "seed": inert_seed,
        "sample_index": inert_index,
        "baseline_overrides": {"n_objs": 2},
        "requested_overrides": {
            "n_objs": 2,
            "palette_size": 4,
            "n_distinct_colors": 4,
        },
        "same_grid": inert == baseline,
        "stats": stats(inert),
    },
    "unknown_override": {
        "request": {"typo_axis": 1},
        "accepted": True,
        "same_as_baseline": unknown == baseline,
    },
    "equal_sizes_texture": {
        "stats": stats(equal_sizes),
        "grid": equal_sizes,
    },
}
Path("../checks/audit/3fcea70c3acf/reproducer.json").write_text(
    json.dumps(result, indent=2) + "\n"
)
Path("../checks/audit/3fcea70c3acf/input.json").write_text(
    json.dumps(grid, indent=2) + "\n"
)
print(json.dumps({
    "task_id": result["task_id"],
    "generator_sha256": result["generator_sha256"],
    "silent_shortening": result["silent_shortening"],
    "inert_count_aliases": result["inert_count_aliases"],
    "unknown_override": result["unknown_override"],
    "equal_sizes_stats": result["equal_sizes_texture"]["stats"],
}, indent=2))
