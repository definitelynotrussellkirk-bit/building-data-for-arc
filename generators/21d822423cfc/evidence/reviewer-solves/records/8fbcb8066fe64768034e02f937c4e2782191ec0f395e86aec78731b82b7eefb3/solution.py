def solve(grid):
    """Fill each wall-bounded room iff all of its markers have one color."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for r0 in range(height):
        for c0 in range(width):
            if grid[r0][c0] == 5 or (r0, c0) in seen:
                continue

            stack = [(r0, c0)]
            seen.add((r0, c0))
            room = []
            marker_colors = set()

            while stack:
                r, c = stack.pop()
                room.append((r, c))
                value = grid[r][c]
                if value not in (0, 5):
                    marker_colors.add(value)

                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 5
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            if len(marker_colors) == 1:
                fill = next(iter(marker_colors))
                for r, c in room:
                    out[r][c] = fill

    return out
