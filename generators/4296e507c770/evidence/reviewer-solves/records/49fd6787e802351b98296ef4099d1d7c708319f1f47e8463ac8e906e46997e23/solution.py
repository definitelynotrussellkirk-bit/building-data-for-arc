def solve(grid):
    """Copy the red template at each colored marker, transformed by its color."""
    height, width = len(grid), len(grid[0])
    red = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if not red:
        raise ValueError("The visible rule requires a red template")
    top = min(r for r, c in red)
    left = min(c for r, c in red)
    shape = [(r - top, c - left) for r, c in red]
    sh = max(r for r, c in shape) + 1
    sw = max(c for r, c in shape) + 1
    variants = {
        3: shape,
        4: [(r, sw - 1 - c) for r, c in shape],
        5: [(sh - 1 - r, c) for r, c in shape],
        6: [(c, sh - 1 - r) for r, c in shape],
    }
    result = [[0] * width for _ in range(height)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            for dr, dc in variants.get(value, ()):
                rr, cc = r + dr, c + dc
                if 0 <= rr < height and 0 <= cc < width:
                    result[rr][cc] = 8
    return result
