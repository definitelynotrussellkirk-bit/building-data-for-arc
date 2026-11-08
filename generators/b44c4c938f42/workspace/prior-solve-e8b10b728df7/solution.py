"""Visible-example solution for the reviewer episode."""

CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
SHIFTS = (
    (0, 0), (0, -1), (0, 1), (-1, 0), (1, 0),
    (-1, -1), (-1, 1), (1, -1), (1, 1),
    (0, -2), (0, 2), (-2, 0), (2, 0),
)


def _panels(grid):
    h, w = len(grid), len(grid[0])
    separators = [c for c in range(w) if all(grid[r][c] == 0 for r in range(h))]
    starts = [0] + [c + 1 for c in separators]
    ends = separators + [w]
    return [[row[a:b] for row in grid] for a, b in zip(starts, ends) if a < b]


def _components(panel):
    h, w = len(panel), len(panel[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = panel[r][c]
            if color == 8 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and panel[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((len(cells), color, tuple(cells)))
    return result


def solve(grid):
    panels = _panels(grid)
    h, out_w = len(grid), len(panels[0][0])
    selected = [max(_components(panel), key=lambda item: item[0]) for panel in panels]
    occupied = {}
    for size, color, cells in sorted(selected, key=lambda item: item[0], reverse=True):
        for dr, dc in SHIFTS:
            shifted = [(r + dr, c + dc) for r, c in cells]
            if all(0 <= r < h and 0 <= c < out_w and (r, c) not in occupied
                   for r, c in shifted):
                for cell in shifted:
                    occupied[cell] = color
                break
    return [[occupied.get((r, c), 8) for c in range(out_w)] for r in range(h)]
