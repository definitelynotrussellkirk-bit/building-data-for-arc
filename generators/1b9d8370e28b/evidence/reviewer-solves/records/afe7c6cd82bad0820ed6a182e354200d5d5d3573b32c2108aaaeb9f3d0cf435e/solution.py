def solve(grid):
    """Compact red cells row-wise toward a color-directed region edge."""
    height = len(grid)
    width = len(grid[0])

    def other(color):
        return 1 if color == 8 else 8

    candidates = []
    for split in range(1, height):
        for first in (1, 8):
            second = other(first)
            if all(
                value == 2 or value == (first if row < split else second)
                for row, values in enumerate(grid)
                for value in values
            ):
                candidates.append(("h", split, first))
    for split in range(1, width):
        for first in (1, 8):
            second = other(first)
            if all(
                value == 2 or value == (first if column < split else second)
                for values in grid
                for column, value in enumerate(values)
            ):
                candidates.append(("v", split, first))

    if len(candidates) != 1:
        raise ValueError(f"expected one straight 1/8 split, found {candidates}")
    axis, split, first = candidates[0]
    second = other(first)
    output = [
        [
            first if (row < split if axis == "h" else column < split) else second
            for column in range(width)
        ]
        for row in range(height)
    ]

    for row in range(height):
        regions = ((0, width),) if axis == "h" else ((0, split), (split, width))
        for left, right in regions:
            count = sum(grid[row][column] == 2 for column in range(left, right))
            if count == 0:
                continue
            background = output[row][left]
            start = left if background == 8 else right - count
            for column in range(start, start + count):
                output[row][column] = 2
    return output
