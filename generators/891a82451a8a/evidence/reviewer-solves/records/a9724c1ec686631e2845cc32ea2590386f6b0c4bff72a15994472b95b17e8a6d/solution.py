from collections import Counter

CYCLE = (0, 5, 2, 8, 9, 6, 1, 3, 4)


def solve(grid):
    """Fill Manhattan-distance rings from the unique singleton seed."""
    if not grid or not grid[0]:
        return []
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    seeds = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != background
    ]
    if len(seeds) != 1:
        raise ValueError(f"expected exactly one seed, found {len(seeds)}")
    sr, sc, seed_color = seeds[0]
    phase = CYCLE.index(seed_color)
    return [
        [
            CYCLE[(phase + abs(r - sr) + abs(c - sc)) % len(CYCLE)]
            for c in range(len(grid[0]))
        ]
        for r in range(len(grid))
    ]
