"""Visible-example solution for the prepared ARC puzzle.

The input contains distractor noise plus solid monochromatic rectangles.  The
rectangles form spatial rows of three; the output records each row's colors
from left to right, with rows ordered from top to bottom.
"""

from __future__ import annotations

from typing import Iterable, Sequence


Grid = list[list[int]]


class Rectangle:
    """Small dependency-free record (the solve harness loads modules unusually)."""

    __slots__ = ("color", "top", "left", "bottom", "right", "size")

    def __init__(
        self, color: int, top: int, left: int, bottom: int, right: int, size: int
    ) -> None:
        self.color = color
        self.top = top
        self.left = left
        self.bottom = bottom
        self.right = right
        self.size = size

    @property
    def center_row(self) -> float:
        return (self.top + self.bottom) / 2.0

    @property
    def center_col(self) -> float:
        return (self.left + self.right) / 2.0


_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _solid_rectangles(grid: Sequence[Sequence[int]]) -> list[Rectangle]:
    """Return non-background components that are filled 2-D rectangles.

    Visible examples show that distractors are sparse/irregular, while every
    symbol to read is a solid rectangle at least 3x3.  Requiring the component
    to fill its bounding box also excludes long runs and compact noise blobs.
    """

    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    rectangles: list[Rectangle] = []

    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue

            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: list[tuple[int, int]] = []

            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for delta_row, delta_col in _NEIGHBORS:
                    next_row = row + delta_row
                    next_col = col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    point = (next_row, next_col)
                    if point in seen or grid[next_row][next_col] != color:
                        continue
                    seen.add(point)
                    stack.append(point)

            rows = [row for row, _ in cells]
            cols = [col for _, col in cells]
            top, bottom = min(rows), max(rows)
            left, right = min(cols), max(cols)
            box_height = bottom - top + 1
            box_width = right - left + 1
            box_area = box_height * box_width

            if box_height < 3 or box_width < 3:
                continue
            if len(cells) != box_area:
                continue

            rectangles.append(
                Rectangle(
                    color=color,
                    top=top,
                    left=left,
                    bottom=bottom,
                    right=right,
                    size=len(cells),
                )
            )

    return rectangles


def _group_into_rows(rectangles: Iterable[Rectangle]) -> list[list[Rectangle]]:
    """Cluster rectangle centers into horizontal rows.

    Within a visible row, differing rectangle heights move centers by at most
    1.5 cells; separate rows are much farther apart.  A four-cell tolerance
    leaves a clear margin in all demonstrations.
    """

    ordered = sorted(rectangles, key=lambda rectangle: rectangle.center_row)
    groups: list[list[Rectangle]] = []

    for rectangle in ordered:
        if not groups:
            groups.append([rectangle])
            continue

        current = groups[-1]
        mean_center = sum(item.center_row for item in current) / len(current)
        if abs(rectangle.center_row - mean_center) <= 4.0:
            current.append(rectangle)
        else:
            groups.append([rectangle])

    # Every demonstrated output row has exactly three entries.  This also
    # makes the solution robust to an isolated accidental solid noise block.
    return [group for group in groups if len(group) == 3]


def solve(grid: Grid) -> Grid:
    rectangles = _solid_rectangles(grid)
    rows = _group_into_rows(rectangles)
    rows.sort(key=lambda group: sum(item.center_row for item in group) / len(group))
    return [
        [rectangle.color for rectangle in sorted(group, key=lambda item: item.center_col)]
        for group in rows
    ]
