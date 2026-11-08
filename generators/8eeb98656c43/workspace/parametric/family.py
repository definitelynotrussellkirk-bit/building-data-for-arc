"""Deterministic matched-input family for 8eeb98656c43.

The alternative setting first performs the exact canonical red-to-orange
reflection.  A unique color-1 marker on the center axis then reads the first
contiguous orange run to its right and appends an equally long color-1 tail.
The tail length therefore cannot be known until Stage A has created the run.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import stable_rng

Grid = list[list[int]]
MODES = ("canonical", "ray_tail")

_PROFILES = (
    (11, 13),
    (12, 15),
    (13, 17),
    (14, 18),
    (15, 19),
    (16, 21),
    (18, 23),
    (20, 25),
    (24, 27),
    (30, 30),
)
_CONTROL_COLORS = (3, 4, 5, 6, 8, 9)


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


def canonical_mirror(value: Any) -> Grid:
    """Pure Python mirror of the exact selected Racket authority."""
    source = _grid(value)
    output = [row[:] for row in source]
    height, width = len(source), len(source[0])
    axis = width // 2
    for r in range(height):
        for c in range(axis):
            mirror = 2 * axis - c
            if source[r][c] == 2 and 0 <= mirror < width:
                output[r][mirror] = 7
    return output


def ray_intermediate(value: Any) -> dict[str, Any]:
    """Return the Stage-A orange run and the equal-length tail it determines."""
    source = _grid(value)
    stage = canonical_mirror(source)
    height, width = len(stage), len(stage[0])
    axis = width // 2
    markers = [
        (r, c)
        for r, row in enumerate(source)
        for c, cell in enumerate(row)
        if cell == 1
    ]
    if len(markers) != 1:
        raise ValueError("ray-tail inputs need exactly one color-1 marker")
    marker_r, marker_c = markers[0]
    if marker_c != axis:
        raise ValueError("the color-1 marker must lie on the center axis")

    start = next((c for c in range(marker_c + 1, width) if stage[marker_r][c] == 7), None)
    if start is None:
        raise ValueError("Stage A must create an orange run to the marker's right")
    stop = start
    while stop + 1 < width and stage[marker_r][stop + 1] == 7:
        stop += 1
    run_length = stop - start + 1
    tail_start = stop + 1
    tail_stop = tail_start + run_length - 1
    if tail_stop >= width:
        raise ValueError("the completion-derived tail must fit inside the grid")
    if any(stage[marker_r][c] != 0 for c in range(tail_start, tail_stop + 1)):
        raise ValueError("the completion-derived tail must land on background")
    return {
        "marker": [marker_r, marker_c],
        "orange_run": [start, stop],
        "run_length": run_length,
        "tail": [tail_start, tail_stop],
    }


def _paint_tail(stage: Grid, intermediate: dict[str, Any], length: int) -> Grid:
    output = [row[:] for row in stage]
    r = intermediate["marker"][0]
    start = intermediate["tail"][0]
    for c in range(start, start + length):
        if c >= len(output[0]) or output[r][c] != 0:
            raise ValueError("tail paint left its guaranteed background interval")
        output[r][c] = 1
    return output


def solve(value: Any, followup: str = "canonical") -> Grid:
    if type(followup) is not str or followup not in MODES:
        raise ValueError("followup must be canonical or ray_tail")
    source = _grid(value)
    stage = canonical_mirror(source)
    if followup == "canonical":
        return stage
    intermediate = ray_intermediate(source)
    return _paint_tail(stage, intermediate, intermediate["run_length"])


def solve_wrong_fixed_tail(value: Any) -> Grid:
    """Plausible wrong ablation: append one cell regardless of the Stage-A run."""
    source = _grid(value)
    stage = canonical_mirror(source)
    return _paint_tail(stage, ray_intermediate(source), 1)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def scene(seed: int, index: int) -> Grid:
    """Construct one fresh source-reasoning scene without corpus-answer access."""
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(index, 0, len(_PROFILES) - 1, "index")
    height, width = _PROFILES[index]
    axis = width // 2
    rng = stable_rng(seed, f"8eeb-parametric-scene-{index}", "1.0.0")
    control_a, control_b = rng.sample(list(_CONTROL_COLORS), 2)
    max_run = (width - 1 - axis) // 2
    if max_run < 2:
        raise RuntimeError("scene profile cannot fit a nontrivial run and equal tail")
    run_length = rng.randint(2, max_run)
    marker_row = height // 2

    grid = [[0] * width for _ in range(height)]

    # The decisive red run ends immediately left of the axis marker.  Stage A
    # reflects it into an orange run immediately to the marker's right.
    for c in range(axis - run_length, axis):
        grid[marker_row][c] = 2
    grid[marker_row][axis] = 1

    # Additional red objects make the canonical transformation independently
    # visible; non-red controls teach that only red mirrors.
    grid[1][1] = 2
    grid[1][2] = 2
    grid[height - 3][2] = 2
    grid[height - 2][2] = 2
    grid[2][axis - 2] = control_a
    if index % 2 == 0:
        grid[height - 2][axis - 3] = control_b
        grid[height - 2][axis - 2] = control_b
    else:
        grid[height - 3][axis - 2] = control_b
        grid[height - 2][axis - 2] = control_b

    intermediate = ray_intermediate(grid)
    if intermediate["run_length"] != run_length:
        raise RuntimeError("constructed scene lost its Stage-A run length")
    if solve(grid, "ray_tail") == solve_wrong_fixed_tail(grid):
        raise RuntimeError("constructed scene failed to separate fixed-tail shortcut")
    return [row[:] for row in grid]
