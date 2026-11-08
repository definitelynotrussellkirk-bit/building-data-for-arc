from collections import Counter


def solve(grid):
    """Absorb sparse dots with >=2 orthogonal rectangle-color neighbors."""
    counts = Counter(value for row in grid for value in row if value != 0)
    if len(counts) != 2:
        raise ValueError(f"expected exactly two nonzero colors, found {sorted(counts)}")
    rect_color, dot_color = [color for color, _ in counts.most_common()]
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != dot_color:
                continue
            adjacent = 0
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == rect_color:
                    adjacent += 1
            out[r][c] = rect_color if adjacent >= 2 else 0
    return out
