"""Visible-example solver for the post-repair cfadc43e5098 challenge."""
from __future__ import annotations

from collections import deque
from copy import deepcopy


def _components(grid: list[list[int]]) -> list[dict[str, object]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, object]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            components.append(
                {
                    "color": color,
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return components


def _intersects(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    ar0, ac0, ar1, ac1 = a
    br0, bc0, br1, bc1 = b
    return not (ar1 < br0 or br1 < ar0 or ac1 < bc0 or bc1 < ac0)


def _bridge_box(
    first: tuple[int, int, int, int],
    second: tuple[int, int, int, int],
) -> tuple[int, int, int, int] | None:
    a_top, a_left, a_bottom, a_right = first
    b_top, b_left, b_bottom, b_right = second

    # Equal doubled row centers: join horizontally.  The bridge uses the
    # overlap of the boxes after removing their one-cell outer rims.
    if a_top + a_bottom == b_top + b_bottom:
        if a_right < b_left:
            left, right = a_right + 1, b_left - 1
        elif b_right < a_left:
            left, right = b_right + 1, a_left - 1
        else:
            return None
        top = max(a_top + 1, b_top + 1)
        bottom = min(a_bottom - 1, b_bottom - 1)
        if top <= bottom and left <= right:
            return top, left, bottom, right

    # Equal doubled column centers: join vertically, using the analogous
    # overlap of the rim-trimmed horizontal spans.
    if a_left + a_right == b_left + b_right:
        if a_bottom < b_top:
            top, bottom = a_bottom + 1, b_top - 1
        elif b_bottom < a_top:
            top, bottom = b_bottom + 1, a_top - 1
        else:
            return None
        left = max(a_left + 1, b_left + 1)
        right = min(a_right - 1, b_right - 1)
        if top <= bottom and left <= right:
            return top, left, bottom, right

    return None


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Draw cyan bridges between aligned same-colored component boxes.

    A third component of that same color blocks a candidate bridge when its
    bounding box intersects the bridge rectangle.  Other colors do not block;
    cells inside the full bridge rectangle are overwritten with cyan.
    """
    if not grid:
        return []
    result = deepcopy(grid)
    components = _components(grid)

    for first_index, first in enumerate(components):
        for second_index in range(first_index + 1, len(components)):
            second = components[second_index]
            if first["color"] != second["color"]:
                continue
            bridge = _bridge_box(first["bbox"], second["bbox"])
            if bridge is None:
                continue
            blocked = any(
                other_index not in (first_index, second_index)
                and other["color"] == first["color"]
                and _intersects(other["bbox"], bridge)
                for other_index, other in enumerate(components)
            )
            if blocked:
                continue
            top, left, bottom, right = bridge
            for row in range(top, bottom + 1):
                for col in range(left, right + 1):
                    result[row][col] = 8
    return result
