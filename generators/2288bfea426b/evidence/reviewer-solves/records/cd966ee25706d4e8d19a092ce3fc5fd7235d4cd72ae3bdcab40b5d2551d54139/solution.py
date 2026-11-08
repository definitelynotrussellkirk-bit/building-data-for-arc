def _normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def _rotate(cells, turns):
    result = list(cells)
    for _ in range(turns % 4):
        result = _normalize((c, -r) for r, c in result)
    return result


def solve(grid):
    """Stamp normalized rotations of the red prototype at coded markers."""
    h, w = len(grid), len(grid[0])
    shape = _normalize(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    )
    turns = {1: 0, 3: 1, 4: 2, 6: 3}
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in turns:
                continue
            for dr, dc in _rotate(shape, turns[value]):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w:
                    out[rr][cc] = 8
    return out
