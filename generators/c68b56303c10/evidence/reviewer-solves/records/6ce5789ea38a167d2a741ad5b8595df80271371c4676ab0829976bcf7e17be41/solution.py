def solve(grid):
    """Build a cyan rectangle from the shared row and column bbox spans."""
    spans = []
    for color in (2, 3):
        positions = [(r, c) for r, row in enumerate(grid)
                     for c, value in enumerate(row) if value == color]
        if not positions:
            raise ValueError("both foreground colors must be present")
        rows, columns = zip(*positions)
        spans.append((set(range(min(rows), max(rows) + 1)),
                      set(range(min(columns), max(columns) + 1))))
    height = len(spans[0][0] & spans[1][0])
    width = len(spans[0][1] & spans[1][1])
    return [[8] * width for _ in range(height)]
