"""Matched-input reflection family for 588ee22f3c4f.

The alternative first performs the exact selected full-grid reflection.  It
then uses the reflected partner cells created by Stage A to determine each
source-to-partner span and fills the background strictly between the pair.
"""
from __future__ import annotations

from typing import Any
from puzzle_generators.base import stable_rng

Grid = list[list[int]]
MODES = ("canonical", "mirror_bridge")
PROFILES = (
    (8, 10), (9, 11), (10, 12), (11, 13), (12, 14),
    (14, 16), (16, 20), (20, 24), (24, 28), (30, 30),
)
COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


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


def _orientation(source: Grid) -> tuple[bool, list[tuple[int, int]]]:
    guides = [(r, c) for r, row in enumerate(source) for c, cell in enumerate(row) if cell == 5]
    if len(guides) != 2:
        raise ValueError("scene needs exactly two color-5 guides")
    same_row = guides[0][0] == guides[1][0]
    same_col = guides[0][1] == guides[1][1]
    if same_row == same_col:
        raise ValueError("guides must share exactly one row or one column")
    return same_row, guides


def canonical_mirror(value: Any) -> Grid:
    source = _grid(value)
    same_row, guides = _orientation(source)
    height, width = len(source), len(source[0])
    work = [[source[r][c] if source[r][c] not in (0, 5) else 0 for c in range(width)] for r in range(height)]
    output = [row[:] for row in work]
    for r in range(height):
        for c in range(width):
            value = work[r][c]
            if value == 0:
                continue
            if same_row:
                output[height - 1 - r][c] = value
            else:
                output[r][width - 1 - c] = value
    for r, c in guides:
        output[r][c] = 5
    return output


def bridge_intermediate(value: Any) -> dict[str, Any]:
    source = _grid(value)
    same_row, _ = _orientation(source)
    stage = canonical_mirror(source)
    height, width = len(source), len(source[0])
    spans = []
    for r in range(height):
        for c in range(width):
            color = source[r][c]
            if color in (0, 5):
                continue
            mirror = (height - 1 - r, c) if same_row else (r, width - 1 - c)
            if source[mirror[0]][mirror[1]] != 0 or stage[mirror[0]][mirror[1]] != color:
                raise ValueError("Stage A must create an empty partner with the source color")
            if same_row and not r < mirror[0]:
                raise ValueError("same-row scenes must originate in the top half")
            if not same_row and not c < mirror[1]:
                raise ValueError("same-column scenes must originate in the left half")
            spans.append({"source": [r, c], "mirror": list(mirror), "color": color})
    if not spans:
        raise ValueError("scene needs motif cells")
    return {"orientation": "row_flip" if same_row else "column_flip", "spans": spans}


def _bridge(stage: Grid, intermediate: dict[str, Any], *, one_step: bool) -> Grid:
    output = [row[:] for row in stage]
    for span in intermediate["spans"]:
        r, c = span["source"]
        mr, mc = span["mirror"]
        color = span["color"]
        if r != mr:
            cells = [(rr, c) for rr in range(r + 1, mr)]
        else:
            cells = [(r, cc) for cc in range(c + 1, mc)]
        if one_step:
            cells = cells[:1]
        for rr, cc in cells:
            if output[rr][cc] == 0:
                output[rr][cc] = color
    return output


def solve(value: Any, followup: str = "canonical") -> Grid:
    if type(followup) is not str or followup not in MODES:
        raise ValueError("followup must be canonical or mirror_bridge")
    source = _grid(value)
    stage = canonical_mirror(source)
    if followup == "canonical":
        return stage
    return _bridge(stage, bridge_intermediate(source), one_step=False)


def solve_wrong_one_step(value: Any) -> Grid:
    source = _grid(value)
    return _bridge(canonical_mirror(source), bridge_intermediate(source), one_step=True)


def scene(seed: int, index: int) -> Grid:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(index, 0, len(PROFILES) - 1, "index")
    height, width = PROFILES[index]
    rng = stable_rng(seed, f"588ee-parametric-scene-{index}", "1.0.0")
    same_row = index % 2 == 0
    grid = [[0] * width for _ in range(height)]
    count = 8 if index >= 8 else min(8, max(3, 3 + index % 6))

    if same_row:
        grid[height - 1][0] = 5
        grid[height - 1][width - 1] = 5
        columns = list(range(1, width - 1))
        rng.shuffle(columns)
        rows = list(range(0, max(1, height // 2)))
        for i, c in enumerate(columns[:count]):
            r = rows[(i * 2 + index) % len(rows)]
            grid[r][c] = COLORS[(i + rng.randrange(len(COLORS))) % len(COLORS)]
    else:
        grid[0][width - 1] = 5
        grid[height - 1][width - 1] = 5
        rows = list(range(1, height - 1))
        rng.shuffle(rows)
        columns = list(range(0, max(1, width // 2)))
        for i, r in enumerate(rows[:count]):
            c = columns[(i * 2 + index) % len(columns)]
            grid[r][c] = COLORS[(i + rng.randrange(len(COLORS))) % len(COLORS)]
    bridge_intermediate(grid)
    return grid
