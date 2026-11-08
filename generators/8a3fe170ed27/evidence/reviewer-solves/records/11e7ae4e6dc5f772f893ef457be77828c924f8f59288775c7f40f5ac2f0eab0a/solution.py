"""Translate occupied rows using the phase observed in the visible pairs."""

def solve(grid):
    if not grid:
        return []
    height, width = len(grid), len(grid[0])
    occupied = [r for r, row in enumerate(grid) if any(value != 0 for value in row)]
    result = [[0] * width for _ in range(height)]
    if not occupied:
        return result
    bottom = max(occupied)
    for r in occupied:
        shift = (0, -1, 0, 1)[(bottom - r) % 4]
        for c, value in enumerate(grid[r]):
            if value and 0 <= c + shift < width:
                result[r][c + shift] = value
    return result
