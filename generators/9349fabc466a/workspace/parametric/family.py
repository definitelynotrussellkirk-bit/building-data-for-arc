"""Deterministic matched-input family for 9349fabc466a.

The alternative setting first performs the canonical same-color axis completion.
It then selects the color that gained the most cells and draws a one-cell outer
frame around that completion-derived set.  The sampler includes a larger
original-marker bounding-box decoy, so the second stage cannot be replaced by a
cheap "frame the largest input bbox" shortcut.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Any

from puzzle_generators.base import stable_rng

Grid = list[list[int]]
Point = tuple[int, int]
MODES = ("canonical", "completion_frame")

_PROFILES = (
    (9, 9),
    (9, 11),
    (11, 9),
    (12, 14),
    (14, 12),
    (16, 18),
    (18, 16),
    (20, 22),
    (24, 26),
    (30, 30),
)


def _grid(value: Any) -> Grid:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer ARC colors")
    return [row[:] for row in value]


def _positions(grid: Grid) -> dict[int, list[Point]]:
    result: dict[int, list[Point]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                result[value].append((r, c))
    return dict(result)


def _spans(points: list[Point]):
    rows: dict[int, list[int]] = defaultdict(list)
    cols: dict[int, list[int]] = defaultdict(list)
    for r, c in points:
        rows[r].append(c)
        cols[c].append(r)
    return (
        {r: (min(cs), max(cs)) for r, cs in rows.items() if len(cs) >= 2},
        {c: (min(rs), max(rs)) for c, rs in cols.items() if len(rs) >= 2},
    )


def canonical_complete(value: Any) -> Grid:
    grid = _grid(value)
    positions = _positions(grid)
    colors = sorted(positions)
    spans = {color: _spans(points) for color, points in positions.items()}
    output = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell != 0:
                continue
            for color in colors:
                row_spans, col_spans = spans[color]
                horizontal = r in row_spans and row_spans[r][0] <= c <= row_spans[r][1]
                vertical = c in col_spans and col_spans[c][0] <= r <= col_spans[c][1]
                if horizontal or vertical:
                    output[r][c] = color
                    break
    return output


def _bbox(points: list[Point]) -> list[int]:
    return [
        min(r for r, _ in points),
        max(r for r, _ in points),
        min(c for _, c in points),
        max(c for _, c in points),
    ]


def completion_intermediate(value: Any) -> dict[str, Any]:
    grid = _grid(value)
    stage = canonical_complete(grid)
    gained: dict[int, list[Point]] = {}
    for color in sorted(_positions(grid)):
        gained[color] = [
            (r, c)
            for r, row in enumerate(grid)
            for c, cell in enumerate(row)
            if cell == 0 and stage[r][c] == color
        ]
    eligible = [color for color, points in gained.items() if points]
    if not eligible:
        raise ValueError("completion-frame inputs need at least one newly completed cell")
    winner = min(eligible, key=lambda color: (-len(gained[color]), color))
    points = gained[winner]
    return {
        "winner_color": winner,
        "new_cell_count": len(points),
        "new_cells_bbox": _bbox(points),
    }


def wrong_marker_bbox_intermediate(value: Any) -> dict[str, Any]:
    """Plausible but wrong shortcut used by the protected counterfactual."""
    grid = _grid(value)
    positions = _positions(grid)
    ranked = []
    for color, points in positions.items():
        box = _bbox(points)
        area = (box[1] - box[0] + 1) * (box[3] - box[2] + 1)
        ranked.append((-area, color, box))
    _, winner, box = min(ranked)
    return {"winner_color": winner, "marker_bbox": box}


def _paint_outer_frame(stage: Grid, box: list[int]) -> Grid:
    output = [row[:] for row in stage]
    height, width = len(output), len(output[0])
    top = max(0, box[0] - 1)
    bottom = min(height - 1, box[1] + 1)
    left = max(0, box[2] - 1)
    right = min(width - 1, box[3] + 1)
    for r in range(top, bottom + 1):
        for c in range(left, right + 1):
            on_border = r in (top, bottom) or c in (left, right)
            if on_border and output[r][c] == 0:
                output[r][c] = 9
    return output


def solve(value: Any, postprocess: str = "canonical") -> Grid:
    if type(postprocess) is not str or postprocess not in MODES:
        raise ValueError("postprocess must be canonical or completion_frame")
    grid = _grid(value)
    stage = canonical_complete(grid)
    if postprocess == "canonical":
        return stage
    return _paint_outer_frame(stage, completion_intermediate(grid)["new_cells_bbox"])


def solve_wrong_marker_bbox(value: Any) -> Grid:
    grid = _grid(value)
    stage = canonical_complete(grid)
    return _paint_outer_frame(stage, wrong_marker_bbox_intermediate(grid)["marker_bbox"])


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def scene(seed: int, index: int) -> Grid:
    """Construct one fresh source-reasoning scene without reading corpus answers."""
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(index, 0, len(_PROFILES) - 1, "index")
    height, width = _PROFILES[index]
    rng = stable_rng(seed, f"9349-parametric-scene-{index}", "1.0.0")
    palette = rng.sample(list(range(1, 9)), 4)
    winner, decoy, cross, controls = palette

    # The completion winner is an inner rectangle.  The diagonal decoy has a
    # strictly larger original marker bbox but produces no canonical fill.
    r0, r1 = 2, height - 3
    c0, c1 = 2, width - 3
    grid = [[0] * width for _ in range(height)]
    for r, c in ((r0, c0), (r0, c1), (r1, c0), (r1, c1)):
        grid[r][c] = winner
    grid[1][1] = decoy
    grid[height - 2][width - 2] = decoy

    # Two opposite-corner controls make every scene substantive while staying
    # diagonal to one another, so they create no canonical span of their own.
    grid[1][width - 2] = controls
    grid[height - 2][1] = controls

    if index % 2 == 0:
        row = (r0 + r1) // 2
        grid[row][c0 + 1] = cross
        grid[row][c1 - 1] = cross
    else:
        col = (c0 + c1) // 2
        grid[r0 + 1][col] = cross
        grid[r1 - 1][col] = cross

    # A seed-dependent harmless marker perturbation varies content without
    # changing the decisive completion geometry.
    if index >= 3 and rng.randrange(2):
        if index % 2 == 0:
            grid[(r0 + r1) // 2][c0 + 2] = cross
        else:
            grid[r0 + 2][(c0 + c1) // 2] = cross

    intermediate = completion_intermediate(grid)
    if intermediate["winner_color"] != winner:
        raise RuntimeError("constructed scene lost its completion-derived winner")
    if solve(grid, "completion_frame") == solve_wrong_marker_bbox(grid):
        raise RuntimeError("constructed scene failed to separate the bbox shortcut")
    return [row[:] for row in grid]
