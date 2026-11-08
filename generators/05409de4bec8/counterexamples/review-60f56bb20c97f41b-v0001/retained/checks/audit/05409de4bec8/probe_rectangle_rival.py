#!/usr/bin/env python3
"""Audit whether four-demo lessons teach the rectangle long-axis exception."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
GEN = REPO / "generators/05409de4bec8/generator.py"

spec = importlib.util.spec_from_file_location("audit_054", GEN)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def target_points(grid):
    by_color: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value:
                by_color.setdefault(value, []).append((row, col))
    candidates = [
        (color, tuple(sorted(points)))
        for color, points in by_color.items()
        if len(points) == 4
        and len({row for row, _ in points}) <= 3
        and len({col for _, col in points}) <= 3
    ]
    if len(candidates) != 1:
        raise ValueError(f"expected one target candidate, got {len(candidates)}")
    return candidates[0]


def draw_all_exact_pair_axes(grid):
    """Plausible rival that omits only the rectangle longer-axis exception."""
    color, points = target_points(grid)
    row_counts = Counter(row for row, _ in points)
    col_counts = Counter(col for _, col in points)
    rows = [row for row, count in row_counts.items() if count == 2]
    cols = [col for col, count in col_counts.items() if count == 2]
    out = [[0 for _ in grid[0]] for _ in grid]
    for row in rows:
        out[row] = [color for _ in grid[0]]
    for col in cols:
        for row in range(len(grid)):
            out[row][col] = color
    return out


bands = ("easy", "medium", "hard")
lessons_per_band = 300
production_ambiguous = 0
rotation_ambiguous = 0
production_by_band = {band: 0 for band in bands}
rotation_by_band = {band: 0 for band in bands}
rectangles_by_band = {band: 0 for band in bands}
representative = None

for band in bands:
    for lesson_index in range(lessons_per_band):
        seed = 730000 + lesson_index
        start = lesson_index * 7
        grids = [module.generate(seed, start + offset, difficulty=band) for offset in range(5)]
        intended = [module.rule_mirror(deepcopy(grid)) for grid in grids]
        rival = [draw_all_exact_pair_axes(grid) for grid in grids]
        differs = [candidate != answer for candidate, answer in zip(rival, intended)]
        rectangles_by_band[band] += sum(differs)

        production_fits = all(not differs[index] for index in range(4))
        production_changes_query = differs[4]
        if production_fits and production_changes_query:
            production_ambiguous += 1
            production_by_band[band] += 1
            if representative is None:
                representative = {
                    "band": band,
                    "lesson_index": lesson_index,
                    "seed": seed,
                    "sample_indices": list(range(start, start + 5)),
                    "inputs": grids,
                    "intended_python_mirror": intended,
                    "rival_outputs": rival,
                    "rival_differs": differs,
                    "self_check_errors": [module.self_check(grid) for grid in grids],
                    "observed_axes": [module.observe_overrides(grid) for grid in grids],
                }

        for query_index in range(5):
            fits_demos = all(not differs[index] for index in range(5) if index != query_index)
            changes_query = differs[query_index]
            if fits_demos and changes_query:
                rotation_ambiguous += 1
                rotation_by_band[band] += 1

assert representative is not None
report = {
    "schema": "arc-audit-rectangle-rival-v1",
    "task_id": module.TASK_ID,
    "generator_sha256": hashlib.sha256(GEN.read_bytes()).hexdigest(),
    "rule_hash": module.RULE_HASH,
    "claim": (
        "The production sampler can make four demonstrations with no rectangle, then hold out "
        "a rectangle. A rival that draws every exact-pair row and column fits all demos but "
        "misses the canonical longer-axis-only rectangle exception."
    ),
    "rival": "draw_all_exact_pair_axes_without_rectangle_long_axis_exception",
    "assembly_tested": "five consecutive sample indices with one fixed seed; four demos plus one query",
    "bands": list(bands),
    "lessons_per_band": lessons_per_band,
    "lessons_total": lessons_per_band * len(bands),
    "production_queries_total": lessons_per_band * len(bands),
    "production_ambiguous": production_ambiguous,
    "production_ambiguous_by_band": production_by_band,
    "query_rotations_total": lessons_per_band * len(bands) * 5,
    "query_rotations_ambiguous": rotation_ambiguous,
    "query_rotations_ambiguous_by_band": rotation_by_band,
    "rectangle_scenes_by_band": rectangles_by_band,
    "representative_lesson": representative,
}

(ROOT / "checks/audit/05409de4bec8/inputs.json").write_text(
    json.dumps({"inputs": representative["inputs"]}, indent=2) + "\n"
)
(ROOT / "checks/audit/05409de4bec8/probe.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n"
)
print(json.dumps({
    "lessons": report["lessons_total"],
    "production_ambiguous": production_ambiguous,
    "production_by_band": production_by_band,
    "rotations": report["query_rotations_total"],
    "rotation_ambiguous": rotation_ambiguous,
    "rotation_by_band": rotation_by_band,
    "representative": {
        "band": representative["band"],
        "seed": representative["seed"],
        "sample_indices": representative["sample_indices"],
        "rival_differs": representative["rival_differs"],
        "self_check_errors": representative["self_check_errors"],
    },
}, indent=2))
