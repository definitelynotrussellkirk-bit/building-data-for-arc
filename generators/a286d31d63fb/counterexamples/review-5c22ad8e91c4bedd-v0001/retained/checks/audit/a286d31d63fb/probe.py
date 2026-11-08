#!/usr/bin/env python3
"""Source-bound adversarial probe for a286d31d63fb (no target edits)."""
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "a286d31d63fb"
ROOT = Path.cwd().resolve()
OUT = ROOT.parent / "checks" / "audit" / TASK_ID / "probe.json"


def shape(grid):
    return [len(grid), len(grid[0])]


def component_rows(module, grid):
    rows = []
    for cells in module._components_4conn(grid):
        colors = sorted({grid[r][c] for r, c in cells})
        profile = module._row_profile(cells)
        rows.append({
            "colors": colors,
            "size": len(cells),
            "row_profile": profile,
            "flat": len(set(profile)) == 1,
        })
    return rows


def capture(call):
    try:
        grid = module.generate(**call)
    except Exception as exc:  # evidence must retain exact public-call behavior
        return {
            "call": call,
            "status": "raised",
            "exception_type": type(exc).__name__,
            "exception": str(exc),
        }
    return {
        "call": call,
        "status": "returned",
        "shape": shape(grid),
        "distinct_nonzero_colors": sorted({v for row in grid for v in row if v}),
        "self_check": module.self_check(grid, difficulty=call.get("difficulty")),
        "components": component_rows(module, grid),
        "grid": grid,
    }


module, source, source_sha = load_selected_generator(TASK_ID, root=ROOT)

height_boundary = capture({
    "seed": 0,
    "sample_index": 0,
    "difficulty": "easy",
    "height": 8,
})
degenerate_height = capture({
    "seed": 0,
    "sample_index": 3,
    "difficulty": "easy",
    "texture": "all_flat",
    "height": 10,
})
palette_size = capture({
    "seed": 0,
    "sample_index": 0,
    "difficulty": "easy",
    "palette_size": 2,
})
three_flat = capture({
    "seed": 0,
    "sample_index": 0,
    "difficulty": "hard",
    "flat_component_count": 3,
})

report = {
    "schema": "arc-audit-reproducer-v1",
    "task_id": TASK_ID,
    "generator_source": str(source.relative_to(ROOT)),
    "generator_sha256": source_sha,
    "declared_axes": module.AXES,
    "findings": {
        "declared_height_boundary_rejected": {
            "expected_from_axis": "height=8 is declared valid (8..16)",
            "observed": height_boundary,
            "reproduced": height_boundary["status"] == "raised",
        },
        "degenerate_ignores_exact_height": {
            "expected": 10,
            "observed": degenerate_height,
            "reproduced": (
                degenerate_height["status"] == "returned"
                and degenerate_height["shape"][0] != 10
            ),
        },
        "palette_size_not_honored": {
            "expected": 2,
            "observed": palette_size,
            "reproduced": (
                palette_size["status"] == "returned"
                and len(palette_size["distinct_nonzero_colors"]) != 2
            ),
        },
        "three_flat_leaves_only_one_nonflat": {
            "documented_nonflat_count": 2,
            "observed": three_flat,
            "reproduced": (
                three_flat["status"] == "returned"
                and sum(not row["flat"] for row in three_flat["components"]) == 1
            ),
        },
    },
    "target_modified": False,
}
report["reproduced"] = all(row["reproduced"] for row in report["findings"].values())
OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "task_id": TASK_ID,
    "generator_sha256": source_sha,
    "reproduced": report["reproduced"],
    "finding_results": {k: v["reproduced"] for k, v in report["findings"].items()},
    "out": str(OUT),
}, indent=2))
raise SystemExit(0 if report["reproduced"] else 1)
