"""Native parametric adapter for transform analogy task 99e7ba062bec.

The default is the exact canonical program: infer the first transform mapping
A to B and apply it to C.  The alternate carries that inferred command through
an inverse-command mapping before applying it to C.  Inputs are shared across
settings and include dense arbitrary-canvas scenes up to 30x30.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

_HOME = Path(__file__).resolve().parent
_PROGRAM_FILES = {
    "forward": _HOME / "canonical.rkt",
    "inverse": _HOME / "inverse.rkt",
}
_CODES = tuple(range(1, 8))

# height, width, command, A dimensions, C dimensions, occupancy probability
_DEMO_SPECS = (
    (5, 17, 2, (3, 4), (3, 4), 0.55),
    (5, 17, 4, (3, 4), (3, 4), 0.55),
    (7, 20, 3, (4, 5), (4, 4), 0.50),
    (8, 22, 5, (5, 5), (4, 5), 0.50),
    (10, 24, 6, (5, 6), (5, 5), 0.52),
    (12, 26, 7, (5, 6), (5, 6), 0.50),
)
_QUERY_SPECS = (
    (8, 20, 2, (4, 5), (4, 5), 0.54),
    (12, 24, 7, (5, 6), (5, 6), 0.52),
    (16, 28, 4, (6, 7), (6, 7), 0.54),
    (30, 30, 2, (8, 7), (8, 7), 0.62),
)


def _validate_settings(settings: Any) -> str:
    if not isinstance(settings, dict) or set(settings) != {"application"}:
        raise ValueError("settings must contain exactly application")
    value = settings["application"]
    if type(value) is not str or value not in _PROGRAM_FILES:
        raise ValueError("application must be forward or inverse")
    return value


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def program(settings: Any) -> str:
    """Return exact Racket source for one declared private setting."""
    return _PROGRAM_FILES[_validate_settings(settings)].read_text(encoding="utf-8")


def _mix_seed(seed: int, role: str, index: int, stream: str) -> int:
    payload = f"99e7ba062bec|{seed}|{role}|{index}|{stream}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _apply(grid: list[list[int]], code: int) -> list[list[int]]:
    if code == 1:
        return [row[:] for row in grid]
    if code == 2:
        return [list(column) for column in zip(*grid[::-1])]
    if code == 3:
        return [row[::-1] for row in grid[::-1]]
    if code == 4:
        return [list(column) for column in zip(*grid)][::-1]
    if code == 5:
        return [row[::-1] for row in grid]
    if code == 6:
        return [row[:] for row in grid[::-1]]
    if code == 7:
        return [list(column) for column in zip(*grid)]
    raise ValueError(f"unknown transform code: {code!r}")


def _crop(grid: list[list[int]]) -> list[list[int]]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        return []
    row0 = min(row for row, _ in cells)
    row1 = max(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    col1 = max(col for _, col in cells)
    return [values[col0 : col1 + 1] for values in grid[row0 : row1 + 1]]


def _key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in _crop(grid))


def _orbit(mask: list[list[int]]) -> set[tuple[tuple[int, ...], ...]]:
    return {_key(_apply(mask, code)) for code in _CODES}


def _sample_mask(
    rng: random.Random,
    height: int,
    width: int,
    probability: float,
    *,
    forbidden_orbit: set[tuple[tuple[int, ...], ...]] | None = None,
    minimum_active: int = 0,
) -> list[list[int]]:
    for _ in range(4096):
        mask = [
            [int(rng.random() < probability) for _ in range(width)]
            for _ in range(height)
        ]
        # Full row/column support keeps the declared panel dimensions observable.
        for row in range(height):
            if not any(mask[row]):
                mask[row][rng.randrange(width)] = 1
        for col in range(width):
            if not any(mask[row][col] for row in range(height)):
                mask[rng.randrange(height)][col] = 1
        active = sum(sum(row) for row in mask)
        if active < max(height, width, minimum_active) or active == height * width:
            continue
        orbit = _orbit(mask)
        if len(orbit) != len(_CODES):
            continue
        if forbidden_orbit is not None and orbit & forbidden_orbit:
            continue
        return mask
    raise RuntimeError(f"could not construct transform-discriminative {height}x{width} mask")


def _colorize(mask: list[list[int]], color: int) -> list[list[int]]:
    return [[color if value else 0 for value in row] for row in mask]


def _assemble(
    height: int,
    width: int,
    panels: tuple[list[list[int]], list[list[int]], list[list[int]]],
    rng: random.Random,
) -> list[list[int]]:
    panel_heights = [len(panel) for panel in panels]
    panel_widths = [len(panel[0]) for panel in panels]
    if max(panel_heights) > height:
        raise RuntimeError("panel does not fit canvas height")
    slots = [0, 1, 1, 0]
    extra = width - sum(panel_widths) - sum(slots)
    if extra < 0:
        raise RuntimeError(f"panels do not fit {height}x{width} canvas")
    for _ in range(extra):
        slots[rng.randrange(4)] += 1

    if height >= 24:
        row_offsets = [0, (height - panel_heights[1]) // 2, height - panel_heights[2]]
        shift = rng.randrange(3)
        row_offsets = row_offsets[shift:] + row_offsets[:shift]
    else:
        row_offsets = [rng.randint(0, height - panel_height) for panel_height in panel_heights]

    grid = [[0 for _ in range(width)] for _ in range(height)]
    column = slots[0]
    for index, panel in enumerate(panels):
        row0 = row_offsets[index]
        for row, values in enumerate(panel):
            for col, value in enumerate(values):
                if value:
                    grid[row0 + row][column + col] = value
        column += panel_widths[index]
        if index < 2:
            column += slots[index + 1]
    if column + slots[3] != width:
        raise RuntimeError("layout width mismatch")
    return grid


def _build_input(
    seed: int,
    role: str,
    index: int,
    spec: tuple[int, int, int, tuple[int, int], tuple[int, int], float],
) -> tuple[list[list[int]], int]:
    height, width, command, a_dims, c_dims, probability = spec
    shape_rng = random.Random(_mix_seed(seed, role, index, "shapes"))
    minimum_active = 30 if (height, width) == (30, 30) else 0
    a_mask = _sample_mask(
        shape_rng,
        *a_dims,
        probability,
        minimum_active=minimum_active,
    )
    a_orbit = _orbit(a_mask)
    c_mask = _sample_mask(
        shape_rng,
        *c_dims,
        probability,
        forbidden_orbit=a_orbit,
        minimum_active=minimum_active,
    )
    b_mask = _apply(a_mask, command)

    color_rng = random.Random(_mix_seed(seed, role, index, "colors"))
    ab_color, c_color = color_rng.sample(range(1, 10), 2)
    panels = (
        _colorize(a_mask, ab_color),
        _colorize(b_mask, ab_color),
        _colorize(c_mask, c_color),
    )
    layout_rng = random.Random(_mix_seed(seed, role, index, "layout"))
    return _assemble(height, width, panels, layout_rng), command


def _output(c_panel: list[list[int]], command: int, application: str) -> list[list[int]]:
    effective = {2: 4, 4: 2}.get(command, command) if application == "inverse" else command
    return _crop(_apply(c_panel, effective))


def _content_bands(grid: list[list[int]]) -> list[tuple[int, int]]:
    bands: list[tuple[int, int]] = []
    column = 0
    width = len(grid[0])
    while column < width:
        while column < width and all(row[column] == 0 for row in grid):
            column += 1
        if column >= width:
            break
        start = column
        while column < width and any(row[column] != 0 for row in grid):
            column += 1
        bands.append((start, column))
    return bands


def _panels(grid: list[list[int]]) -> list[list[list[int]]]:
    return [
        _crop([row[start:stop] for row in grid])
        for start, stop in _content_bands(grid)
    ]


def _pair(grid: list[list[int]], command: int, application: str) -> dict[str, list[list[int]]]:
    panels = _panels(grid)
    if len(panels) != 3:
        raise RuntimeError("constructed input does not contain exactly three panels")
    return {"input": deepcopy(grid), "output": _output(panels[2], command, application)}


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    """Generate one setting-neutral, count-prefix-stable transform episode."""
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    application = _validate_settings(settings)

    demo_items = [
        _build_input(seed, "demo", index, spec)
        for index, spec in enumerate(_DEMO_SPECS[:demos])
    ]
    query_bank = [
        _build_input(seed, "query", index, spec)
        for index, spec in enumerate(_QUERY_SPECS)
    ]
    query_items = query_bank[:queries]
    all_inputs = [grid for grid, _ in demo_items + query_items]
    if len({repr(grid) for grid in all_inputs}) != len(all_inputs):
        raise RuntimeError("episode inputs are not distinct")

    return {
        "train": [_pair(grid, command, application) for grid, command in demo_items],
        "test": [_pair(grid, command, application) for grid, command in query_items],
        "program_solution": program(settings),
    }
