"""Visible-example solution for blind task 4179e1ac3cf7."""

from collections import deque


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells = set()
            while q:
                rr, cc = q.popleft()
                cells.add((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            out.append(cells)
    return out


def _normalized(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def solve(grid):
    """Select green copies of the blue template and symmetrize them horizontally.

    The blue (1) component is an orientation-sensitive template.  Every green (3)
    4-connected component with exactly the same normalized cells is retained.  A
    retained copy is unioned with its left-right reflection inside its own bounding
    box and painted azure (8); every other cell becomes background (0).
    """
    if not grid or not grid[0]:
        return []

    h, w = len(grid), len(grid[0])
    answer = [[0] * w for _ in range(h)]

    templates = _components(grid, 1)
    if not templates:
        return answer
    # The visible task uses one blue object.  Choosing the largest is a stable
    # fallback if stray blue pixels are ever present.
    template = _normalized(max(templates, key=len))

    for cells in _components(grid, 3):
        normalized = _normalized(cells)
        if normalized != template:
            continue
        c0 = min(c for _, c in cells)
        c1 = max(c for _, c in cells)
        for r, c in cells:
            answer[r][c] = 8
            answer[r][c0 + c1 - c] = 8

    return answer
