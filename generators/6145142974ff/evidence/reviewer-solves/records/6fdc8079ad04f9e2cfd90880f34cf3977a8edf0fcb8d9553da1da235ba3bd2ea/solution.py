"""Visible-example solution for task 6145142974ff."""

from collections import Counter, deque


def _components(grid, color):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            comp = []
            while q:
                x, y = q.popleft()
                comp.append((x, y))
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if (
                        0 <= nx < h
                        and 0 <= ny < w
                        and grid[nx][ny] == color
                        and (nx, ny) not in seen
                    ):
                        seen.add((nx, ny))
                        q.append((nx, ny))
            out.append(comp)
    return out


def _shape(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def solve(grid):
    """Select exact translated color-3 copies of the color-1 template."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    output = [[0 for _ in range(w)] for _ in range(h)]
    if not h or not w:
        return output

    templates = _components(grid, 1)
    if len(templates) != 1:
        return output
    wanted = _shape(templates[0])

    marker_counts = Counter(
        value
        for row in grid
        for value in row
        if value not in (0, 1, 3)
    )
    if not marker_counts:
        return output
    max_count = max(marker_counts.values())
    winners = [color for color, count in marker_counts.items() if count == max_count]
    if len(winners) != 1:
        return output
    paint = winners[0]

    for comp in _components(grid, 3):
        if _shape(comp) == wanted:
            for r, c in comp:
                output[r][c] = paint
    return output
