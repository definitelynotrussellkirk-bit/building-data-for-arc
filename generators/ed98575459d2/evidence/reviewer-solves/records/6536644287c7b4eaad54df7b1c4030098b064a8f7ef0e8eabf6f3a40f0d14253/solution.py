from collections import defaultdict, deque


def solve(grid):
    """Compact nonzero cells upward per column inside each non-8 chamber."""
    h = len(grid)
    w = len(grid[0])
    out = [row[:] for row in grid]
    seen = set()

    for start_r in range(h):
        for start_c in range(w):
            start = (start_r, start_c)
            if start in seen or grid[start_r][start_c] == 8:
                continue

            queue = deque([start])
            seen.add(start)
            room = []
            while queue:
                r, c = queue.popleft()
                room.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if not (0 <= rr < h and 0 <= cc < w):
                        continue
                    if (rr, cc) in seen or grid[rr][cc] == 8:
                        continue
                    seen.add((rr, cc))
                    queue.append((rr, cc))

            rows_by_col = defaultdict(list)
            for r, c in room:
                out[r][c] = 0
                rows_by_col[c].append(r)

            for c, rows in rows_by_col.items():
                rows.sort()
                values = [grid[r][c] for r in rows if grid[r][c] != 0]
                for r, value in zip(rows, values):
                    out[r][c] = value

    return out
