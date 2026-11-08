from collections import deque


def solve(grid):
    """Erase every drawn boundary and color only the zero-valued holes it encloses."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = [[0 for _ in range(w)] for _ in range(h)]
    if not h or not w:
        return out

    # Mark background connected to the outside. Remaining zero cells are holes.
    outside = [[False] * w for _ in range(h)]
    q = deque()
    for r in range(h):
        for c in (0, w - 1):
            if grid[r][c] == 0 and not outside[r][c]:
                outside[r][c] = True
                q.append((r, c))
    for c in range(w):
        for r in (0, h - 1):
            if grid[r][c] == 0 and not outside[r][c]:
                outside[r][c] = True
                q.append((r, c))

    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == 0 and not outside[rr][cc]:
                outside[rr][cc] = True
                q.append((rr, cc))

    # For each enclosed zero region, use the (normally unique) color of its wall.
    seen = [[False] * w for _ in range(h)]
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != 0 or outside[sr][sc] or seen[sr][sc]:
                continue
            region = []
            border_colors = []
            seen[sr][sc] = True
            q.append((sr, sc))
            while q:
                r, c = q.popleft()
                region.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    rr, cc = r + dr, c + dc
                    if not (0 <= rr < h and 0 <= cc < w):
                        continue
                    value = grid[rr][cc]
                    if value == 0:
                        if not outside[rr][cc] and not seen[rr][cc]:
                            seen[rr][cc] = True
                            q.append((rr, cc))
                    else:
                        border_colors.append(value)
            if border_colors:
                # Majority is deterministic and handles harmless protrusions or mixed contact.
                color = max(set(border_colors), key=lambda x: (border_colors.count(x), -x))
                for r, c in region:
                    out[r][c] = color
    return out
