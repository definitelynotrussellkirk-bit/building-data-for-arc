from __future__ import annotations

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _panel_ranges(grid: list[list[int]]) -> list[tuple[int, int]]:
    height = len(grid)
    width = len(grid[0])
    dividers = [
        col
        for col in range(width)
        if all(grid[row][col] == 9 for row in range(height))
    ]
    cuts = [-1, *dividers, width]
    return [(left + 1, right) for left, right in zip(cuts, cuts[1:])]


def _peel_depth(cells: set[tuple[int, int]]) -> int:
    """Count cardinal boundary-removal rounds until the object vanishes."""
    remaining = set(cells)
    depth = 0
    while remaining:
        boundary = {
            (row, col)
            for row, col in remaining
            if any((row + dr, col + dc) not in remaining for dr, dc in _CARDINAL)
        }
        if not boundary:
            raise ValueError("finite object has no boundary")
        remaining.difference_update(boundary)
        depth += 1
    return depth


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Compare panel objects by their cardinal onion-peel thickness."""
    if not grid or not grid[0]:
        return []
    depths: list[int] = []
    for left, right in _panel_ranges(grid):
        cells = {
            (row, col - left)
            for row in range(len(grid))
            for col in range(left, right)
            if grid[row][col] not in (0, 9)
        }
        if not cells:
            raise ValueError("panel contains no object")
        depths.append(_peel_depth(cells))
    return [
        [8 if left_depth == right_depth else 0 for right_depth in depths]
        for left_depth in depths
    ]
