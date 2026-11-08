from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
GEN_PATH = ROOT / "WORK/repo/generators/a4fb12580b3f/generator.py"
spec = importlib.util.spec_from_file_location("audited_a4fb12580b3f", GEN_PATH)
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def selected_rule(grid):
    out = [row[:] for row in grid]
    comps = gen._components(grid)
    anchors = [cells for color, cells in comps if color == 1]
    assert len(anchors) == 1
    anchor = anchors[0]
    for color, cells in comps:
        if color != 1 and gen._touches(anchor, cells):
            gen._paint(out, cells, 4)
    return out


def touches8(left, right):
    return any(max(abs(r - rr), abs(c - cc)) == 1 for r, c in left for rr, cc in right)


def diagonal_rival(grid):
    out = [row[:] for row in grid]
    comps = gen._components(grid)
    anchors = [cells for color, cells in comps if color == 1]
    assert len(anchors) == 1
    anchor = anchors[0]
    for color, cells in comps:
        if color != 1 and touches8(anchor, cells):
            gen._paint(out, cells, 4)
    return out


def diff_cells(left, right):
    return [[r, c, left[r][c], right[r][c]] for r in range(len(left)) for c in range(len(left[0])) if left[r][c] != right[r][c]]


found = None
for seed in range(1, 10000):
    grids = [gen.generate(seed, i, difficulty="medium") for i in range(4)]
    selected = [selected_rule(grid) for grid in grids]
    rival = [diagonal_rival(grid) for grid in grids]
    if all(selected[i] == rival[i] for i in range(3)) and selected[3] != rival[3]:
        found = (seed, grids, selected, rival)
        break

assert found is not None
seed, grids, selected, rival = found
report = {
    "task_id": "a4fb12580b3f",
    "generator_path": str(GEN_PATH.relative_to(ROOT)),
    "episode": {"seed": seed, "difficulty": "medium", "demo_sample_indices": [0, 1, 2], "query_sample_index": 3},
    "demo_rival_fits": [selected[i] == rival[i] for i in range(3)],
    "query_rival_differs": selected[3] != rival[3],
    "query_differing_cells": diff_cells(selected[3], rival[3]),
    "demos": [{"input": grids[i], "output": selected[i]} for i in range(3)],
    "query": {"input": grids[3], "selected_output": selected[3], "diagonal_rival_output": rival[3]},
    "finding": "A plausible 8-neighborhood-touching shortcut fits all three generated demonstrations but recolors a diagonal-only query component that the selected cardinal-touch rule preserves.",
}
print(json.dumps(report, indent=2, sort_keys=True))
assert report["demo_rival_fits"] == [True, True, True]
assert report["query_rival_differs"]
assert all(gen.self_check(grid) == [] for grid in grids)
