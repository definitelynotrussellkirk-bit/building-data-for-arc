from collections import Counter


def _divider_rows(grid):
    wall_values = {1, 7, 9}
    return [r for r, row in enumerate(grid) if set(row) <= wall_values]


def _divider_cols(grid):
    wall_values = {1, 7, 9}
    height = len(grid)
    width = len(grid[0])
    return [c for c in range(width) if {grid[r][c] for r in range(height)} <= wall_values]


def _room_signature(grid, top, bottom, left, right):
    """Rotation-invariant summary of one compartment.

    The interior dimensions may swap under a quarter-turn.  The contents are
    represented by the number of blue (2) and green (3) cells, while the frame
    is represented by the number of orange openings (7) on its perimeter.
    Magenta 9s occur only as wall-junction noise in the visible examples.
    """
    height = bottom - top - 1
    width = right - left - 1

    interior = Counter(
        grid[r][c]
        for r in range(top + 1, bottom)
        for c in range(left + 1, right)
    )

    openings = 0
    for c in range(left, right + 1):
        openings += grid[top][c] == 7
        openings += grid[bottom][c] == 7
    for r in range(top + 1, bottom):
        openings += grid[r][left] == 7
        openings += grid[r][right] == 7

    return tuple(sorted((height, width))), interior[2], interior[3], openings


def solve(grid):
    row_walls = _divider_rows(grid)
    col_walls = _divider_cols(grid)

    signatures = []
    for top, bottom in zip(row_walls, row_walls[1:]):
        for left, right in zip(col_walls, col_walls[1:]):
            signatures.append(
                _room_signature(grid, top, bottom, left, right)
            )

    key = signatures[0]
    return [[8 if signature == key else 0 for signature in signatures[1:]]]
