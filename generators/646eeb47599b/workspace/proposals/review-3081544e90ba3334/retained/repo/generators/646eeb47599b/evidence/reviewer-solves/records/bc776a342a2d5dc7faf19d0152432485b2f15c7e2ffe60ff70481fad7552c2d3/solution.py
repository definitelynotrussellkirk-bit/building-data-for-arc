"""Visible-example solution: trace branching green rays through the orange field."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    result = [row[:] for row in grid]
    green = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 3]
    if len(green) != 2:
        raise ValueError("Expected the two adjacent green starting cells")
    directions = [(0, -1), (0, 1)] if green[0][0] == green[1][0] else [(-1, 0), (1, 0)]
    pending = [(r, c, dr, dc) for r, c in green for dr, dc in directions]
    visited = set()

    def open_cell(r, c):
        return 0 <= r < height and 0 <= c < width and grid[r][c] != 8

    while pending:
        r, c, dr, dc = pending.pop()
        state = (r, c, dr, dc)
        if state in visited:
            continue
        visited.add(state)
        nr, nc = r + dr, c + dc
        if not (0 <= nr < height and 0 <= nc < width):
            continue
        if grid[nr][nc] == 8:
            for tr, tc in ((-dc, dr), (dc, -dr)):
                if open_cell(r + tr, c + tc):
                    pending.append((r, c, tr, tc))
        else:
            if grid[nr][nc] == 7:
                result[nr][nc] = 3
            pending.append((nr, nc, dr, dc))
    return result
