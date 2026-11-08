from collections import deque


def solve(grid):
    """Complete each same-color 4-connected object's bounding box."""
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    seen = set()

    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue

            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if (0 <= rr < h and 0 <= cc < w and
                            (rr, cc) not in seen and grid[rr][cc] == color):
                        seen.add((rr, cc))
                        queue.append((rr, cc))

            r1 = min(r for r, _ in cells)
            r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            c2 = max(c for _, c in cells)

            for r in range(r1, r2 + 1):
                for c in range(c1, c2 + 1):
                    on_border = r in (r1, r2) or c in (c1, c2)
                    checker_color = ((r - r1 - 1) + (c - c1 - 1)) % 2 == 0
                    if on_border or checker_color:
                        out[r][c] = color

    return out
