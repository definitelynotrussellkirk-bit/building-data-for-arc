def solve(grid):
    """Top-left normalize colors 1 and 2; emit their XOR in color 8."""
    def normalized(color):
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        if not cells:
            return set()
        min_r = min(r for r, _ in cells)
        min_c = min(c for _, c in cells)
        return {(r - min_r, c - min_c) for r, c in cells}

    first = normalized(1)
    second = normalized(2)
    xor = first ^ second
    if not xor:
        return [[0]]
    height = max(
        max((r for r, _ in first), default=-1),
        max((r for r, _ in second), default=-1),
    ) + 1
    width = max(
        max((c for _, c in first), default=-1),
        max((c for _, c in second), default=-1),
    ) + 1
    return [
        [8 if (r, c) in xor else 0 for c in range(width)]
        for r in range(height)
    ]
