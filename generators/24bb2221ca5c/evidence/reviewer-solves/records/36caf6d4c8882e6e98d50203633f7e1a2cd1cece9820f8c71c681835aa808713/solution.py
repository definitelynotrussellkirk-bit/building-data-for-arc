from collections import deque


def solve(grid):
    """Fill 4-connected background holes enclosed by each colored object."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = [row[:] for row in grid]
    seen = set()

    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue

            # Collect one 4-connected monochromatic object.
            component = set()
            q = deque([(r0, c0)])
            seen.add((r0, c0))
            while q:
                r, c = q.popleft()
                component.add((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))

            min_r = min(r for r, _ in component)
            max_r = max(r for r, _ in component)
            min_c = min(c for _, c in component)
            max_c = max(c for _, c in component)

            # In the object's bounding box, mark every non-object cell that can
            # escape through the box boundary.  Any remaining background cell is
            # a 4-connected hole, even when the outline is missing a corner.
            exterior = set()
            q = deque()

            def seed(r, c):
                if (r, c) not in component and (r, c) not in exterior:
                    exterior.add((r, c))
                    q.append((r, c))

            for c in range(min_c, max_c + 1):
                seed(min_r, c)
                seed(max_r, c)
            for r in range(min_r, max_r + 1):
                seed(r, min_c)
                seed(r, max_c)

            while q:
                r, c = q.popleft()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        min_r <= nr <= max_r
                        and min_c <= nc <= max_c
                        and (nr, nc) not in component
                        and (nr, nc) not in exterior
                    ):
                        exterior.add((nr, nc))
                        q.append((nr, nc))

            for r in range(min_r, max_r + 1):
                for c in range(min_c, max_c + 1):
                    if grid[r][c] == 0 and (r, c) not in exterior:
                        out[r][c] = color

    return out
