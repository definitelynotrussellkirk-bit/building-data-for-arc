"""Infer the enlarged grid and corner diagonals from the visible examples."""


def solve(grid):
    """Scale by foreground-color count and mark otherwise empty corners."""
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    scale = len({value for row in grid for value in row if value != 0})
    if scale == 0:
        return [row[:] for row in grid]

    output = [
        [value for value in row for _ in range(scale)]
        for row in grid
        for _ in range(scale)
    ]

    for row in range(height - 1):
        for col in range(width - 1):
            occupied = [
                (dy, dx)
                for dy in range(2)
                for dx in range(2)
                if grid[row + dy][col + dx] != 0
            ]
            if len(occupied) != 1:
                continue
            source_dy, source_dx = occupied[0]
            target_row = row + 1 - source_dy
            target_col = col + 1 - source_dx
            main_diagonal = source_dy == source_dx
            for offset in range(scale):
                local_col = offset if main_diagonal else scale - 1 - offset
                output[target_row * scale + offset][
                    target_col * scale + local_col
                ] = 2

    return output
