"""Infer the transformation only from the public examples."""


def solve(grid):
    result = [list(row) for row in grid]
    height = len(result)
    width = len(result[0]) if height else 0
    marker = next(
        ((r, c, value) for r, row in enumerate(grid)
         for c, value in enumerate(row) if value not in (0, 5)),
        None,
    )
    if marker is None:
        return result

    start_r, start_c, color = marker
    pending = [(start_r, start_c)]
    visited = {(start_r, start_c)}
    while pending:
        r, c = pending.pop()
        result[r][c] = color
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if (0 <= nr < height and 0 <= nc < width
                    and (nr, nc) not in visited
                    and grid[nr][nc] in (0, color)):
                visited.add((nr, nc))
                pending.append((nr, nc))
    return result
