"""Visible-example solution for the repaired chamber-gravity lesson."""


def solve(grid):
    h = len(grid)
    w = len(grid[0])
    out = [[5 if grid[r][c] == 5 else 0 for c in range(w)] for r in range(h)]

    seen = set()
    for start_r in range(h):
        for start_c in range(w):
            if grid[start_r][start_c] == 5 or (start_r, start_c) in seen:
                continue
            room = []
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            while stack:
                r, c = stack.pop()
                room.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < h and 0 <= nc < w and
                            grid[nr][nc] != 5 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            for c in sorted({c for _, c in room}):
                column_cells = sorted(r for r, cc in room if cc == c)
                values = [grid[r][c] for r in column_cells if grid[r][c] != 0]
                for r, value in zip(column_cells[-len(values):] if values else (), values):
                    out[r][c] = value
    return out
