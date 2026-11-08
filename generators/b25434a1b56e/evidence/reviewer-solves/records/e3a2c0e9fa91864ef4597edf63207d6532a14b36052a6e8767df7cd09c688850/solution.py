from collections import Counter


def solve(grid):
    """Reduce each of the four equal quadrants to its dominant nonzero color."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    if height == 0 or width == 0 or height % 2 or width % 2:
        raise ValueError("expected a non-empty grid with even height and width")
    if any(len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")

    half_h = height // 2
    half_w = width // 2
    result = []

    for row_start in (0, half_h):
        output_row = []
        for col_start in (0, half_w):
            values = [
                grid[row][col]
                for row in range(row_start, row_start + half_h)
                for col in range(col_start, col_start + half_w)
                if grid[row][col] != 0
            ]
            if not values:
                output_row.append(0)
                continue

            counts = Counter(values)
            # Generated lessons appear to make the winner unique.  The first-seen
            # tie break keeps behavior deterministic without assuming color order.
            output_row.append(max(values, key=lambda value: counts[value]))
        result.append(output_row)

    return result
