from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Keep exactly the cells belonging to a same-colour 4-connected group."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [[0 for _ in row] for row in grid]
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = row + dr, col + dc
                if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] == color:
                    out[row][col] = color
                    break
    return out
