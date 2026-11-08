from collections import deque


def _components_of_color(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
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
            components.append(cells)
    return components


def solve(grid):
    """Fill the framed object(s) containing the most gray (8) markers."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    h, w = len(grid), len(grid[0])
    frames = []

    # Gray (8) is the marker color, even when it happens to outline a decoy.
    for color in range(1, 10):
        if color == 8:
            continue
        for cells in _components_of_color(grid, color):
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            r0, r1 = min(rows), max(rows)
            c0, c1 = min(cols), max(cols)
            if r1 - r0 < 2 or c1 - c0 < 2:
                continue

            # Keep only components that form the complete perimeter of a rectangle.
            perimeter = {
                (r, c)
                for r in range(r0, r1 + 1)
                for c in range(c0, c1 + 1)
                if r in (r0, r1) or c in (c0, c1)
            }
            if not perimeter.issubset(set(cells)):
                continue

            markers = sum(
                grid[r][c] == 8
                for r in range(r0 + 1, r1)
                for c in range(c0 + 1, c1)
            )
            frames.append((markers, color, r0, r1, c0, c1))

    out = [[0 if value == 8 else value for value in row] for row in grid]
    if not frames:
        return out

    max_markers = max(item[0] for item in frames)
    for markers, color, r0, r1, c0, c1 in frames:
        if markers == max_markers:
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    out[r][c] = color
    return out
