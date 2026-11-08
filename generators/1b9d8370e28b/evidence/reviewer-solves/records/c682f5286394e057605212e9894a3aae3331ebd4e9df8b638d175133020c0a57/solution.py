def solve(grid):
    """Compact red cells row-wise toward the side dictated by each region."""
    h = len(grid)
    w = len(grid[0])

    candidates = []
    for split in range(1, h):
        for first in (1, 8):
            second = 1 if first == 8 else 8
            if all(
                value == 2 or value == (first if r < split else second)
                for r, row in enumerate(grid)
                for value in row
            ):
                candidates.append(("h", split, first))
    for split in range(1, w):
        for first in (1, 8):
            second = 1 if first == 8 else 8
            if all(
                value == 2 or value == (first if c < split else second)
                for row in grid
                for c, value in enumerate(row)
            ):
                candidates.append(("v", split, first))

    if len(candidates) != 1:
        raise ValueError(f"ambiguous split: {candidates}")
    axis, split, first = candidates[0]
    second = 1 if first == 8 else 8

    output = [
        [
            first if (r < split if axis == "h" else c < split) else second
            for c in range(w)
        ]
        for r in range(h)
    ]

    for r in range(h):
        regions = ((0, w),) if axis == "h" else ((0, split), (split, w))
        for c0, c1 in regions:
            count = sum(grid[r][c] == 2 for c in range(c0, c1))
            if count == 0:
                continue
            background = output[r][c0]
            if background == 8:
                for c in range(c0, c0 + count):
                    output[r][c] = 2
            else:
                for c in range(c1 - count, c1):
                    output[r][c] = 2
    return output
