from collections import deque


def _components(grid):
    """Return monochrome 4-connected non-background components."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    found = []

    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue

            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            top = min(r for r, _ in cells)
            bottom = max(r for r, _ in cells)
            left = min(c for _, c in cells)
            right = max(c for _, c in cells)
            crop = [row[left : right + 1] for row in grid[top : bottom + 1]]
            found.append((left, top, crop))

    return found


def solve(grid):
    """Stack colored objects top-to-bottom in their original left-to-right order."""
    objects = sorted(_components(grid), key=lambda item: (item[0], item[1]))
    if not objects:
        return []

    width = max(len(crop[0]) for _, _, crop in objects)
    output = []
    for index, (_, _, crop) in enumerate(objects):
        if index:
            output.append([0] * width)
        output.extend(row + [0] * (width - len(row)) for row in crop)
    return output
