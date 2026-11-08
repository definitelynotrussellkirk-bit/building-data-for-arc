"""Complete each colored domino into a 2-by-2 square.

Inferred only from the visible challenge examples.
"""


def solve(grid):
    """Return a copy with horizontal pairs expanded down, vertical pairs right."""
    if not grid:
        return []
    height, width = len(grid), len(grid[0])
    result = [list(row) for row in grid]
    seen = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            component = []
            pending = [(row, col)]
            seen.add((row, col))
            while pending:
                r, c = pending.pop()
                component.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c),
                               (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        pending.append((nr, nc))

            # All observed foreground objects are adjacent two-cell pairs.
            if len(component) != 2:
                continue
            (r1, c1), (r2, c2) = component
            dr, dc = (1, 0) if r1 == r2 else (0, 1)
            for r, c in component:
                nr, nc = r + dr, c + dc
                if 0 <= nr < height and 0 <= nc < width:
                    result[nr][nc] = color

    return result
