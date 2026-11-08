"""Visible-example solver. Earlier rule exposure is declared in SOLVE_NOTES.md."""

def solve(grid):
    if not grid or not grid[0]:
        raise ValueError('expected a nonempty rectangular grid')
    height, width = len(grid), len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError('expected a rectangular grid')
    result = [list(row) for row in grid]
    for r in range(1, height - 1):
        for c in range(1, width - 1):
            if grid[r][c] != 0:
                continue
            matching = set()
            for dc in (-1, 1):
                first = grid[r - 1][c - dc]
                second = grid[r + 1][c + dc]
                if first != 0 and first == second:
                    matching.add(first)
            if len(matching) > 1:
                raise ValueError('visible examples do not specify competing midpoint colors')
            if matching:
                result[r][c] = next(iter(matching))
    return result
