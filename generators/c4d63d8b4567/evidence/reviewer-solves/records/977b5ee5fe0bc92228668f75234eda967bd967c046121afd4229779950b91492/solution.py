from collections import defaultdict


def solve(grid):
    """Connect unobstructed same-colour markers along rows and columns."""
    out = [row[:] for row in grid]
    positions = defaultdict(list)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                positions[color].append((r, c))

    for color, cells in positions.items():
        for i, (r1, c1) in enumerate(cells):
            for r2, c2 in cells[i + 1 :]:
                if r1 == r2:
                    lo, hi = sorted((c1, c2))
                    span = [(r1, c) for c in range(lo, hi + 1)]
                elif c1 == c2:
                    lo, hi = sorted((r1, r2))
                    span = [(r, c1) for r in range(lo, hi + 1)]
                else:
                    continue

                # A different-colour marker in the original input blocks the line.
                if any(grid[r][c] not in (0, color) for r, c in span):
                    continue
                for r, c in span:
                    out[r][c] = color
    return out
