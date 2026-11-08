"""Matched-input closed-chamber ray family for 4c331f7e97e6.

The alternative executes the exact canonical four-ray stage, reads the color
that Stage A creates at the initially empty chamber center, then fills every
remaining chamber-background cell with that input-dependent winner color.
"""
from __future__ import annotations

from typing import Any
from puzzle_generators.base import stable_rng

Grid = list[list[int]]
MODES = ("canonical", "center_fill")
PROFILES = (
    (11, 11), (12, 14), (13, 15), (14, 17), (15, 18),
    (18, 20), (20, 23), (22, 25), (26, 28), (30, 30),
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def _grid(value: Any) -> Grid:
    if (
        type(value) is not list or not 1 <= len(value) <= 30
        or type(value[0]) is not list or not 1 <= len(value[0]) <= 30
        or any(type(row) is not list or len(row) != len(value[0])
               or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
               for row in value)
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer ARC colors")
    return [row[:] for row in value]


def wall_box(value: Any) -> tuple[int, int, int, int]:
    grid = _grid(value)
    ones = {(r, c) for r, row in enumerate(grid) for c, cell in enumerate(row) if cell == 1}
    if not ones:
        raise ValueError("closed chamber needs color-1 walls")
    top = min(r for r, _ in ones); bottom = max(r for r, _ in ones)
    left = min(c for _, c in ones); right = max(c for _, c in ones)
    expected = (
        {(top, c) for c in range(left, right + 1)}
        | {(bottom, c) for c in range(left, right + 1)}
        | {(r, left) for r in range(top, bottom + 1)}
        | {(r, right) for r in range(top, bottom + 1)}
    )
    if ones != expected:
        raise ValueError("color-1 walls must be exactly one rectangular perimeter")
    return top, bottom, left, right


def canonical_rays(value: Any) -> Grid:
    source = _grid(value)
    output = [row[:] for row in source]
    height, width = len(source), len(source[0])
    starts = [(r, c, source[r][c]) for r in range(height) for c in range(width)
              if source[r][c] not in (0, 1)]
    for r, c, color in starts:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rr, cc = r + dr, c + dc
            while 0 <= rr < height and 0 <= cc < width:
                if source[rr][cc] == 1:
                    break
                if source[rr][cc] == 0:
                    output[rr][cc] = color
                rr += dr; cc += dc
    return output


def center_intermediate(value: Any) -> dict[str, Any]:
    source = _grid(value)
    top, bottom, left, right = wall_box(source)
    center = (len(source) // 2, len(source[0]) // 2)
    if not (top < center[0] < bottom and left < center[1] < right):
        raise ValueError("grid center must lie inside the chamber")
    if source[center[0]][center[1]] != 0:
        raise ValueError("grid center must be background before Stage A")
    starts = [(r, c, source[r][c]) for r in range(len(source)) for c in range(len(source[0]))
              if source[r][c] not in (0, 1)]
    if not starts:
        raise ValueError("scene needs markers")
    stage = canonical_rays(source)
    center_color = stage[center[0]][center[1]]
    if center_color in (0, 1):
        raise ValueError("Stage A must paint the grid center with a marker color")
    return {
        "center": list(center),
        "center_color": center_color,
        "first_marker_color": starts[0][2],
        "wall_box": [top, bottom, left, right],
    }


def _fill(stage: Grid, intermediate: dict[str, Any], color: int) -> Grid:
    output = [row[:] for row in stage]
    top, bottom, left, right = intermediate["wall_box"]
    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            if output[r][c] == 0:
                output[r][c] = color
    return output


def solve(value: Any, followup: str = "canonical") -> Grid:
    if type(followup) is not str or followup not in MODES:
        raise ValueError("followup must be canonical or center_fill")
    source = _grid(value)
    stage = canonical_rays(source)
    if followup == "canonical":
        return stage
    intermediate = center_intermediate(source)
    return _fill(stage, intermediate, intermediate["center_color"])


def solve_wrong_first_marker(value: Any) -> Grid:
    source = _grid(value)
    intermediate = center_intermediate(source)
    return _fill(canonical_rays(source), intermediate, intermediate["first_marker_color"])


def _perimeter(grid: Grid, top: int, bottom: int, left: int, right: int) -> None:
    for c in range(left, right + 1):
        grid[top][c] = grid[bottom][c] = 1
    for r in range(top, bottom + 1):
        grid[r][left] = grid[r][right] = 1


def scene(seed: int, index: int) -> Grid:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(index, 0, len(PROFILES) - 1, "index")
    height, width = PROFILES[index]
    rng = stable_rng(seed, f"4c331-parametric-scene-{index}", "1.0.0")
    margin_r = 1 if height >= 13 and index % 3 == 1 else 0
    margin_c = 1 if width >= 13 and index % 3 == 2 else 0
    top, bottom = margin_r, height - 1 - margin_r
    left, right = margin_c, width - 1 - margin_c
    center_r, center_c = height // 2, width // 2
    if not (top + 2 < center_r < bottom - 1 and left + 2 < center_c < right - 1):
        top, bottom, left, right = 0, height - 1, 0, width - 1

    grid = [[0] * width for _ in range(height)]
    _perimeter(grid, top, bottom, left, right)
    first_color, winner_color = rng.sample(list(range(2, 10)), 2)
    upper = (max(top + 1, center_r - 2 - index % 2), center_c)
    lateral = (center_r, max(left + 1, center_c - 2 - (index + 1) % 2))
    grid[upper[0]][upper[1]] = first_color
    grid[lateral[0]][lateral[1]] = winner_color

    extra_colors = [c for c in range(2, 10) if c not in (first_color, winner_color)]
    rng.shuffle(extra_colors)
    candidates = [
        (bottom - 2, left + 2),
        (top + 2, right - 2),
        (bottom - 3, right - 3),
    ]
    extra_count = index % 4
    for (r, c), color in zip(candidates[:extra_count], extra_colors, strict=False):
        if r not in (center_r,) and c not in (center_c,) and grid[r][c] == 0:
            grid[r][c] = color
    intermediate = center_intermediate(grid)
    if intermediate["center_color"] == intermediate["first_marker_color"]:
        raise RuntimeError("scene failed to make Stage A center differ from the first marker")
    return grid
