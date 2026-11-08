"""Independent Python claim oracle for the native tie-break family.

Protected Racket remains the label authority during qualification.  This module
keeps generation deterministic and provides finite-rival auditing without
importing the production generator's private solver helpers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

Grid = list[list[int]]
Cell = tuple[int, int]


@dataclass(frozen=True)
class Component:
    cells: tuple[Cell, ...]
    color: int
    r1: int
    c1: int
    r2: int
    c2: int

    @property
    def area(self) -> int:
        return len(self.cells)

    @property
    def height(self) -> int:
        return self.r2 - self.r1 + 1

    @property
    def width(self) -> int:
        return self.c2 - self.c1 + 1

    @property
    def perimeter(self) -> int:
        occupied = set(self.cells)
        return sum(
            (row + dr, column + dc) not in occupied
            for row, column in self.cells
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        )

    @property
    def normalized(self) -> tuple[Cell, ...]:
        return tuple(sorted((row - self.r1, column - self.c1) for row, column in self.cells))

    @property
    def bbox_perimeter(self) -> int:
        return 2 * (self.height + self.width)


def validate_grid(grid: Grid) -> None:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must be a nonempty 1..30 by 1..30 list")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer ARC colors")


def components(grid: Grid) -> list[Component]:
    validate_grid(grid)
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    result: list[Component] = []
    for start_row in range(height):
        for start_column in range(width):
            color = grid[start_row][start_column]
            if color == 0 or (start_row, start_column) in seen:
                continue
            stack = [(start_row, start_column)]
            seen.add((start_row, start_column))
            cells: list[Cell] = []
            while stack:
                row, column = stack.pop()
                cells.append((row, column))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = row + dr, column + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [row for row, _ in cells]
            columns = [column for _, column in cells]
            result.append(
                Component(
                    cells=tuple(sorted(cells)),
                    color=color,
                    r1=min(rows),
                    c1=min(columns),
                    r2=max(rows),
                    c2=max(columns),
                )
            )
    return result


def ordering(grid: Grid, tie_break: str) -> list[Component]:
    items = components(grid)
    if tie_break == "source_position":
        key: Callable[[Component], tuple[int, ...]] = lambda item: (
            item.perimeter,
            item.r1,
            item.c1,
        )
    elif tie_break == "smaller_area":
        key = lambda item: (item.perimeter, item.area, item.r1, item.c1)
    else:
        raise ValueError("tie_break must be source_position or smaller_area")
    return sorted(items, key=key)


def pack(
    ordered: Iterable[Component],
    *,
    gap: int = 1,
    alignment: str = "top",
    fill_bbox: bool = False,
) -> Grid:
    items = list(ordered)
    if not items:
        return []
    height = max(item.height for item in items)
    width = sum(item.width for item in items) + gap * (len(items) - 1)
    output = [[0] * width for _ in range(height)]
    left = 0
    for item in items:
        if alignment == "top":
            top = 0
        elif alignment == "bottom":
            top = height - item.height
        else:
            raise ValueError(f"unknown alignment {alignment!r}")
        if fill_bbox:
            for row in range(item.height):
                for column in range(item.width):
                    output[top + row][left + column] = item.color
        else:
            for row, column in item.normalized:
                output[top + row][left + column] = item.color
        left += item.width + gap
    return output


def solve(grid: Grid, tie_break: str) -> Grid:
    return pack(ordering(grid, tie_break))


def ordered_colors(grid: Grid, tie_break: str) -> list[int]:
    return [item.color for item in ordering(grid, tie_break)]
