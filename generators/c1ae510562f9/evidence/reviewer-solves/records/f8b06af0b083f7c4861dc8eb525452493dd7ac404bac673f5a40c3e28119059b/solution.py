def solve(grid):
    gray = [(r, c) for r, row in enumerate(grid)
            for c, value in enumerate(row) if value == 5]
    top = min(r for r, c in gray)
    bottom = max(r for r, c in gray)
    left = min(c for r, c in gray)
    right = max(c for r, c in gray)
    empty_rows = sum(
        all(grid[r][c] == 0 for c in range(left + 1, right))
        for r in range(top, bottom)
    )
    output = [[0] * 3 for _ in range(3)]
    directions = ((0, 1), (1, 0), (0, -1), (-1, 0))
    r = c = direction = 0
    for _ in range(min(empty_rows, 9)):
        output[r][c] = 8
        dr, dc = directions[direction]
        nr, nc = r + dr, c + dc
        if not (0 <= nr < 3 and 0 <= nc < 3) or output[nr][nc] != 0:
            direction = (direction + 1) % 4
            dr, dc = directions[direction]
            nr, nc = r + dr, c + dc
        r, c = nr, nc
    return output
