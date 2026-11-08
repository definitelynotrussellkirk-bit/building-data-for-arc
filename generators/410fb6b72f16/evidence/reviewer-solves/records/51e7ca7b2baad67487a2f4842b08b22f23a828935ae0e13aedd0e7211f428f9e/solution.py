"""Visible-only solution for the blind ARC challenge."""


def solve(grid):
    """Recolor orthogonally isolated 1-cells to 2; preserve everything else."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1:
                continue
            has_one_neighbor = any(
                0 <= nr < height
                and 0 <= nc < width
                and grid[nr][nc] == 1
                for nr, nc in (
                    (row - 1, col),
                    (row + 1, col),
                    (row, col - 1),
                    (row, col + 1),
                )
            )
            if not has_one_neighbor:
                out[row][col] = 2

    return out
