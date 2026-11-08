"""Independent Python oracle and inspection helpers for task 3adf11522bf5.

This module is test/reviewer tooling.  The Racket program remains label authority.
The implementation intentionally does not import helpers from generator.py.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class SquareFacts:
    max_side: int
    maximal_origins: tuple[tuple[int, int], ...]
    maximal_cells: frozenset[tuple[int, int]]
    disjoint_smaller_cells: frozenset[tuple[int, int]]
    all_square_cells: frozenset[tuple[int, int]]


def _shape(grid: list[list[int]]) -> tuple[int, int]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    return len(grid), len(grid[0])


def square_table(grid: list[list[int]]) -> list[list[int]]:
    """Largest all-zero square side with each cell as top-left."""
    h, w = _shape(grid)
    table = [[0] * w for _ in range(h)]
    for r in range(h - 1, -1, -1):
        for c in range(w - 1, -1, -1):
            if grid[r][c] != 0:
                continue
            table[r][c] = 1
            if r + 1 < h and c + 1 < w:
                table[r][c] += min(
                    table[r + 1][c],
                    table[r][c + 1],
                    table[r + 1][c + 1],
                )
    return table


def _cells(r: int, c: int, side: int) -> set[tuple[int, int]]:
    return {
        (rr, cc)
        for rr in range(r, r + side)
        for cc in range(c, c + side)
    }


def square_facts(grid: list[list[int]]) -> SquareFacts:
    table = square_table(grid)
    h, w = len(table), len(table[0])
    max_side = max(max(row) for row in table)
    origins = tuple(
        (r, c)
        for r in range(h)
        for c in range(w)
        if table[r][c] == max_side
    )
    maximal: set[tuple[int, int]] = set()
    for r, c in origins:
        maximal.update(_cells(r, c, max_side))

    disjoint: set[tuple[int, int]] = set()
    all_square: set[tuple[int, int]] = set()
    for side in range(2, max_side + 1):
        for r in range(h - side + 1):
            for c in range(w - side + 1):
                if table[r][c] < side:
                    continue
                cells = _cells(r, c, side)
                all_square.update(cells)
                if cells.isdisjoint(maximal):
                    disjoint.update(cells)
    return SquareFacts(
        max_side=max_side,
        maximal_origins=origins,
        maximal_cells=frozenset(maximal),
        disjoint_smaller_cells=frozenset(disjoint),
        all_square_cells=frozenset(all_square),
    )


def _paint(grid: list[list[int]], cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for r, c in cells:
        out[r][c] = 1
    return out


def reference_output(grid: list[list[int]]) -> list[list[int]]:
    facts = square_facts(grid)
    return _paint(grid, facts.maximal_cells | facts.disjoint_smaller_cells)


def largest_only_output(grid: list[list[int]]) -> list[list[int]]:
    return _paint(grid, square_facts(grid).maximal_cells)


def all_square_cells_output(grid: list[list[int]]) -> list[list[int]]:
    return _paint(grid, square_facts(grid).all_square_cells)


def first_largest_only_output(grid: list[list[int]]) -> list[list[int]]:
    facts = square_facts(grid)
    cells: set[tuple[int, int]] = set()
    if facts.maximal_origins:
        r, c = facts.maximal_origins[0]
        cells = _cells(r, c, facts.max_side)
    return _paint(grid, cells)


def color_five_only_output(grid: list[list[int]]) -> list[list[int]]:
    colors = {value for row in grid for value in row if value != 0}
    if colors == {5}:
        return reference_output(grid)
    return deepcopy(grid)


def obstacle_color(grid: list[list[int]]) -> int:
    colors = {value for row in grid for value in row if value != 0}
    if len(colors) != 1:
        raise ValueError(f"expected one nonzero obstacle color, found {sorted(colors)}")
    return next(iter(colors))


def observed(grid: list[list[int]]) -> dict[str, int | str]:
    facts = square_facts(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "obstacle_color": obstacle_color(grid),
        "scene_profile": "canonical2" if facts.max_side == 2 else "teaching",
    }
