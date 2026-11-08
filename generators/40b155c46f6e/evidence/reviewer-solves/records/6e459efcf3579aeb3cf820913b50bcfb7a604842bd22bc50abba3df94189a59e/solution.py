"""Row-local singleton cleanup inferred from this episode's visible examples."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid:
        return []
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError('expected a rectangular grid')
    result = [list(row) for row in grid]
    for index, row in enumerate(grid):
        counts: dict[int, int] = {}
        for color in row:
            if color != 0:
                counts[color] = counts.get(color, 0) + 1
        if len(counts) != 2:
            continue
        singleton = [color for color, count in counts.items() if count == 1]
        repeated = [color for color, count in counts.items() if count > 1]
        if len(singleton) == 1 and len(repeated) == 1:
            odd, majority = singleton[0], repeated[0]
            result[index] = [majority if color == odd else color for color in row]
    return result
