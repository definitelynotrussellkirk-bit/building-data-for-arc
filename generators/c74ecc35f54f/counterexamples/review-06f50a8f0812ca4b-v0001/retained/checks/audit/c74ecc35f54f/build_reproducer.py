from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "c74ecc35f54f"
ROOT = find_root(__file__)
OUT = ROOT.parent / "checks" / "audit" / TASK_ID
gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)


def nonzero_cells(grid):
    return [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v]


def first_color(grid):
    cells = nonzero_cells(grid)
    return cells[0][2] if cells else None


def component_count_ignoring_color(grid):
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    count = 0
    while remaining:
        count += 1
        start = min(remaining)
        remaining.remove(start)
        todo = [start]
        while todo:
            r, c = todo.pop()
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in remaining:
                    remaining.remove(p)
                    todo.append(p)
    return count


def count_rival(grid):
    color = first_color(grid)
    return [[color] * component_count_ignoring_color(grid)] if color is not None else []


def case(label, seed, sample_index, difficulty="easy", **overrides):
    grid = gen.generate(seed, sample_index, difficulty=difficulty, **overrides)
    cells = nonzero_cells(grid)
    return {
        "label": label,
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "overrides": overrides,
        "input": grid,
        "self_check": gen.self_check(grid, difficulty=difficulty, meta={"overrides": overrides}),
        "nonzero_count": len(cells),
        "component_count_ignoring_color": component_count_ignoring_color(grid),
        "first_row_major_nonzero_color": first_color(grid),
        "observed_distinct_nonzero_colors": sorted({v for _r, _c, v in cells}),
        "component_count_rival_output": count_rival(grid),
    }


valid = [
    case("ignored_first_color_override", 0, 0, first_color="9"),
    *[case(f"lesson_index_{i}", 27, i) for i in range(4)],
]
invalid = case("advertised_monocolor_texture", 0, 0, texture="monocolor_grid")

(OUT / "valid-inputs.json").write_text(
    json.dumps({"inputs": [row["input"] for row in valid]}, indent=2) + "\n"
)
(OUT / "monocolor-input.json").write_text(
    json.dumps({"input": invalid["input"]}, indent=2) + "\n"
)
pre = {
    "schema": "arcpuzzles-audit-c74ecc35f54f-pre-v1",
    "task_id": TASK_ID,
    "generator_path": str(source_path.relative_to(ROOT)),
    "generator_sha256": source_sha256,
    "valid_cases": valid,
    "invalid_output_case": invalid,
}
(OUT / "pre-evidence.json").write_text(json.dumps(pre, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "generator_sha256": source_sha256,
    "first_color_requested": 9,
    "first_color_observed": valid[0]["first_row_major_nonzero_color"],
    "lesson_counts": [x["nonzero_count"] for x in valid[1:]],
    "lesson_components": [x["component_count_ignoring_color"] for x in valid[1:]],
    "monocolor_nonzero_count": invalid["nonzero_count"],
    "monocolor_self_check": invalid["self_check"],
}, indent=2))
