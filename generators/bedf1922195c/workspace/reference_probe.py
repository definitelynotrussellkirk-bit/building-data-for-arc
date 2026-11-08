"""Independent geometry oracle and rival probes for bedf1922195c.

This module is test-only.  It intentionally does not import the production
implementation or the Racket authority.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import sys
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "bedf1922195c"


def load_generator(path: str | Path):
    source = Path(path)
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    # Dataclasses and some annotation resolvers consult sys.modules while a
    # module body executes.  Mirror normal import semantics for robust probes.
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


def components(grid: list[list[int]], color: int | None = None):
    """Return monochrome 4-connected components as (color, frozenset(cells))."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, frozenset[tuple[int, int]]]] = []
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 0 or (color is not None and value != color) or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: set[tuple[int, int]] = set()
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    point = (r + dr, c + dc)
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and point not in seen
                        and grid[point[0]][point[1]] == value
                    ):
                        seen.add(point)
                        stack.append(point)
            result.append((value, frozenset(cells)))
    return result


def is_straight(cells: Iterable[tuple[int, int]]) -> bool:
    cells = tuple(cells)
    return len({r for r, _ in cells}) == 1 or len({c for _, c in cells}) == 1


def midpoint(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    ordered = sorted(cells)
    if len({r for r, _ in ordered}) == 1:
        ordered.sort(key=lambda point: point[1])
    else:
        ordered.sort(key=lambda point: point[0])
    return ordered[len(ordered) // 2]


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for color, cells in components(grid, 1):
        if color == 1 and len(cells) >= 3 and len(cells) % 2 == 1 and is_straight(cells):
            row, col = midpoint(cells)
            out[row][col] = 2
    return out


def any_color_odd_straight_rival(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: ignore that the selected color must be blue."""
    out = deepcopy(grid)
    for color, cells in components(grid):
        if color != 2 and len(cells) >= 3 and len(cells) % 2 == 1 and is_straight(cells):
            row, col = midpoint(cells)
            out[row][col] = 2
    return out


def ignore_parity_rival(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: mark the upper/left middle of even blue lines too."""
    out = deepcopy(grid)
    for _, cells in components(grid, 1):
        if len(cells) >= 2 and is_straight(cells):
            row, col = midpoint(cells)
            out[row][col] = 2
    return out


def ignore_straightness_rival(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: mark the row-major middle of any odd blue object."""
    out = deepcopy(grid)
    for _, cells in components(grid, 1):
        if len(cells) >= 3 and len(cells) % 2 == 1:
            row, col = sorted(cells)[len(cells) // 2]
            out[row][col] = 2
    return out


def only_lengths_3_or_5_rival(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: transform only observed lengths 3 and 5."""
    out = deepcopy(grid)
    for _, cells in components(grid, 1):
        if len(cells) in (3, 5) and is_straight(cells):
            row, col = midpoint(cells)
            out[row][col] = 2
    return out


def qualifying_blue_segments(grid: list[list[int]]):
    return [
        cells
        for _, cells in components(grid, 1)
        if len(cells) >= 3 and len(cells) % 2 == 1 and is_straight(cells)
    ]


def has_even_blue_segment(grid: list[list[int]]) -> bool:
    return any(len(cells) >= 2 and len(cells) % 2 == 0 and is_straight(cells)
               for _, cells in components(grid, 1))


def has_bent_odd_blue(grid: list[list[int]]) -> bool:
    return any(len(cells) >= 3 and len(cells) % 2 == 1 and not is_straight(cells)
               for _, cells in components(grid, 1))


def has_nonblue_odd_segment(grid: list[list[int]]) -> bool:
    return any(color not in (0, 1, 2) and len(cells) >= 3 and len(cells) % 2 == 1
               and is_straight(cells) for color, cells in components(grid))


def has_length_seven_blue_segment(grid: list[list[int]]) -> bool:
    return any(len(cells) == 7 and is_straight(cells)
               for _, cells in components(grid, 1))


def branch_signature(grid: list[list[int]]) -> tuple[bool, bool, bool]:
    return has_even_blue_segment(grid), has_bent_odd_blue(grid), has_nonblue_odd_segment(grid)


def palette_size(grid: list[list[int]]) -> int:
    return len({value for row in grid for value in row})
