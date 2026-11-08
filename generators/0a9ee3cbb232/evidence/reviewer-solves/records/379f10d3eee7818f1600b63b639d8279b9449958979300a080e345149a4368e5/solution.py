from collections import Counter


def solve(grid):
    """Compress each three-cell colored bar into one cell of a 2x3 meter.

    Color 3 units are placed first, then color 2 units, in row-major order.
    Unused cells retain the input background color.  The meter has six cells,
    so later color-2 units are clipped when the input contains more than six
    total units.
    """
    counts = Counter(cell for row in grid for cell in row)
    background = max((color for color in counts if color not in (2, 3)),
                     key=counts.get)

    cells = [3] * (counts.get(3, 0) // 3)
    cells += [2] * (counts.get(2, 0) // 3)
    cells = (cells + [background] * 6)[:6]
    return [cells[:3], cells[3:]]
