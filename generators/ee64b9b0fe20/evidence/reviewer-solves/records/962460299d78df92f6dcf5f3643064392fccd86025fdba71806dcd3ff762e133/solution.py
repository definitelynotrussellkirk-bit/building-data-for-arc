"""Visible-example solution for the post-repair reviewer episode."""
from collections import Counter, deque


def solve(grid):
    """Bottom-pack non-background monochrome objects by increasing cell count."""
    h = len(grid)
    w = len(grid[0])

    # The demonstrations use a nonzero field color; zero may itself be an object.
    nonzero = Counter(value for row in grid for value in row if value != 0)
    if not nonzero:
        return [row[:] for row in grid]
    background = max(nonzero, key=nonzero.get)

    seen = set()
    objects = []
    for sr in range(h):
        for sc in range(w):
            if (sr, sc) in seen or grid[sr][sc] == background:
                continue
            color = grid[sr][sc]
            queue = deque([(sr, sc)])
            seen.add((sr, sc))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            top = min(r for r, _ in cells)
            left = min(c for _, c in cells)
            bottom = max(r for r, _ in cells)
            right = max(c for _, c in cells)

            # A surrounding border has a whole-canvas bounding box and is removed.
            if (top, left, bottom, right) == (0, 0, h - 1, w - 1):
                continue
            normalized = [(r - top, c - left) for r, c in cells]
            objects.append((len(cells), color, bottom - top + 1,
                            right - left + 1, normalized))

    objects.sort(key=lambda item: item[0])
    output = [[background for _ in range(w)] for _ in range(h)]
    cursor = 0
    for _, color, obj_h, obj_w, cells in objects:
        row0 = h - obj_h
        for r, c in cells:
            output[row0 + r][cursor + c] = color
        cursor += obj_w
    return output
