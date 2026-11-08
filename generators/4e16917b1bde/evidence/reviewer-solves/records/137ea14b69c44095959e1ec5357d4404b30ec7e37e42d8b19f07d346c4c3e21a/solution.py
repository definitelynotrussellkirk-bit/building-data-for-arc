"""ARC solver inferred only from WORK/solve/challenge.json.

The input contains a unique full-height, constant, non-zero vertical divider.
Every other non-zero cell is copied to its horizontal reflection across that
column; the original cell and divider are retained.
"""


def _divider_column(grid):
    if not grid or not grid[0]:
        raise ValueError("grid must be a non-empty rectangle")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    candidates = []
    for col in range(width):
        color = grid[0][col]
        if color != 0 and all(row[col] == color for row in grid):
            candidates.append(col)
    if len(candidates) != 1:
        raise ValueError(
            f"expected exactly one full-height non-zero divider, got {candidates}"
        )
    return candidates[0]


def solve(grid):
    divider = _divider_column(grid)
    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]

    # Read exclusively from the original grid, so newly copied cells cannot
    # cascade into further edits.
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or col == divider:
                continue
            reflected = 2 * divider - col
            if 0 <= reflected < width:
                output[row][reflected] = color
    return output
