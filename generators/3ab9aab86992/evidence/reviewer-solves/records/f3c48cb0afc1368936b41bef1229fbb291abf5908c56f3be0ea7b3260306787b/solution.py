from collections import Counter


def solve(grid):
    """Move each tiny L's color to the matching enlarged output corner."""
    h, w = len(grid), len(grid[0])
    bg = Counter(value for row in grid for value in row).most_common(1)[0][0]
    out = [[bg for _ in range(w)] for _ in range(h)]

    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == bg or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, cells))

    shape_to_corner = {
        frozenset({(0, 0), (0, 1), (1, 0)}): (0, 0),
        frozenset({(0, 0), (0, 1), (1, 1)}): (0, w - 1),
        frozenset({(0, 0), (1, 0), (1, 1)}): (h - 1, 0),
        frozenset({(0, 1), (1, 0), (1, 1)}): (h - 1, w - 1),
    }
    arm = (min(h, w) - 1) // 2

    for color, cells in components:
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        shape = frozenset((r - r0, c - c0) for r, c in cells)
        corner_r, corner_c = shape_to_corner[shape]
        row_step = 1 if corner_r == 0 else -1
        col_step = 1 if corner_c == 0 else -1
        for offset in range(arm):
            out[corner_r + row_step * offset][corner_c] = color
            out[corner_r][corner_c + col_step * offset] = color

    return out
