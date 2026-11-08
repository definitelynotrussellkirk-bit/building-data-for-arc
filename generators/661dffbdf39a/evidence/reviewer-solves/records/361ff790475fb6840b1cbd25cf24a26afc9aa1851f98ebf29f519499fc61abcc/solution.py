from collections import Counter


def solve(grid):
    """Recover the hidden full-line lattice and mark every crossing."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    counts = Counter(cell for row in grid for cell in row)
    background = counts.most_common(1)[0][0]

    non_background = [color for color in counts if color != background]
    if len(non_background) != 2:
        raise ValueError("expected background, line, and marker colors")

    line_color = max(non_background, key=counts.__getitem__)
    marker_color = next(color for color in non_background if color != line_color)

    horizontal = {r for r, row in enumerate(grid) if background not in row}
    vertical = {
        c
        for c in range(width)
        if all(grid[r][c] != background for r in range(height))
    }

    out = [[background for _ in range(width)] for _ in range(height)]
    for r in horizontal:
        for c in range(width):
            out[r][c] = line_color
    for c in vertical:
        for r in range(height):
            out[r][c] = line_color
    for r in horizontal:
        for c in vertical:
            out[r][c] = marker_color
    return out
