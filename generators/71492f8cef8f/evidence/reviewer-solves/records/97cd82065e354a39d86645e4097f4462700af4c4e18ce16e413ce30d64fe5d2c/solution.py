from __future__ import annotations


def solve(grid):
    """Fill each non-5 component only when it contains one nonzero cell."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] == 5 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            component = []
            seeds = []
            while stack:
                row, col = stack.pop()
                if (
                    not 0 <= row < height
                    or not 0 <= col < width
                    or (row, col) in seen
                    or grid[row][col] == 5
                ):
                    continue
                seen.add((row, col))
                component.append((row, col))
                if grid[row][col] != 0:
                    seeds.append((row, col))
                stack.extend(
                    ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
                )
            if len(seeds) == 1:
                seed_row, seed_col = seeds[0]
                color = grid[seed_row][seed_col]
                for row, col in component:
                    if grid[row][col] == 0:
                        out[row][col] = color
    return out
