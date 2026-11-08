def solve(grid):
    """Replace each same-colour horizontal endpoint pair by its midpoint."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]

    for row_index, row in enumerate(grid):
        positions_by_colour = {}
        for column_index, colour in enumerate(row):
            if colour != 0:
                positions_by_colour.setdefault(colour, []).append(column_index)

        for colour, positions in positions_by_colour.items():
            if len(positions) != 2:
                raise ValueError(
                    f"row {row_index}, colour {colour}: expected two endpoints, "
                    f"found {len(positions)}"
                )
            left, right = positions
            if (right - left) % 2:
                raise ValueError(
                    f"row {row_index}, colour {colour}: endpoints lack an integer midpoint"
                )
            output[row_index][(left + right) // 2] = colour

    return output
