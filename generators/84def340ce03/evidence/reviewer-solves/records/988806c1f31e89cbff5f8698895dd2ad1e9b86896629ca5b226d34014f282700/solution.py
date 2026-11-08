def solve(grid):
    """Expand row-major 2x2 tiles into nested, four-colored square rings."""
    h = len(grid)
    w = len(grid[0])
    if h % 2 or w % 2 or any(len(row) != w for row in grid):
        raise ValueError("expected a nonempty rectangular grid with even dimensions")

    blocks = []
    for r in range(0, h, 2):
        for c in range(0, w, 2):
            blocks.append((
                grid[r][c],       # top-left sector
                grid[r][c + 1],   # top-right sector
                grid[r + 1][c],   # bottom-left sector
                grid[r + 1][c + 1],  # bottom-right sector
            ))

    rings = len(blocks)
    size = 2 * rings
    out = [[0 for _ in range(size)] for _ in range(size)]

    # The first input tile is the innermost ring; later tiles grow outward.
    for k, (tl, tr, bl, br) in enumerate(blocks):
        lo = rings - 1 - k
        hi = rings + k
        half = k + 1

        for offset in range(half):
            out[lo][lo + offset] = tl
            out[lo][rings + offset] = tr
            out[hi][lo + offset] = bl
            out[hi][rings + offset] = br

            out[lo + offset][lo] = tl
            out[rings + offset][lo] = bl
            out[lo + offset][hi] = tr
            out[rings + offset][hi] = br

    return out
