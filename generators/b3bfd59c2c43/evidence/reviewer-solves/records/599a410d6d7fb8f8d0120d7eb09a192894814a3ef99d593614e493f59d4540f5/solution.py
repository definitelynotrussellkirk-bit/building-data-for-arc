"""ARC solver inferred only from the visible examples in challenge.json."""


def solve(grid):
    """Recolor each exposed nonzero cell to 8; preserve enclosed core cells."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0:
                continue

            exposed = False
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = row + dr, col + dc
                if nr < 0 or nr >= height or nc < 0 or nc >= width:
                    exposed = True
                    break
                if grid[nr][nc] == 0:
                    exposed = True
                    break

            if exposed:
                result[row][col] = 8

    return result
