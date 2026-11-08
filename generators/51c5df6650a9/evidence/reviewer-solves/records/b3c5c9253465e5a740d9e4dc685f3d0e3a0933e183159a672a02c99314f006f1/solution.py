from collections import Counter


def solve(grid):
    """Pack the keyed colored objects beneath the first row.

    The non-background cells in row 0 form an ordered color key.  For each key
    color, remove the key cell, crop the remaining same-colored object, and
    place the cropped shape top-aligned at row 1.  Consecutive objects are
    separated by one background column.
    """
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    counts = Counter(value for row in grid for value in row)
    background = max(counts, key=counts.get)

    order = []
    seen = set()
    for value in grid[0]:
        if value != background and value not in seen:
            seen.add(value)
            order.append(value)

    output = [[background for _ in range(width)] for _ in range(height)]
    out_col = 0

    for color in order:
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if r != 0 and value == color
        ]
        if not cells:
            continue

        min_r = min(r for r, _ in cells)
        max_r = max(r for r, _ in cells)
        min_c = min(c for _, c in cells)
        max_c = max(c for _, c in cells)

        for r, c in cells:
            target_r = 1 + (r - min_r)
            target_c = out_col + (c - min_c)
            if 0 <= target_r < height and 0 <= target_c < width:
                output[target_r][target_c] = color

        out_col += (max_c - min_c + 1) + 1

    return output
