"""Visible-only solution for blind task 691d467ddb4d."""


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            cells = set()
            while stack:
                rr, cc = stack.pop()
                if not (0 <= rr < h and 0 <= cc < w):
                    continue
                if (rr, cc) in seen or grid[rr][cc] != color:
                    continue
                seen.add((rr, cc))
                cells.add((rr, cc))
                stack.extend(((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)))
            result.append(cells)
    return result


def solve(grid):
    """Recolor the uniquely leftmost non-background object from 4 to 3."""
    out = [row[:] for row in grid]
    objects = _components(grid)
    if not objects:
        return out
    target = min(objects, key=lambda cells: (min(c for _, c in cells), min(r for r, _ in cells)))
    for r, c in target:
        out[r][c] = 3
    return out
