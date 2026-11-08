from collections import deque


def solve(grid):
    """Fill each 5-bounded chamber from its count of marker cells.

    The colors displayed above the first full separator row form a cyclic
    palette.  A chamber with n cells of color 1 receives palette[(n - 1) mod k].
    Thus one marker selects the first color, two the second, and zero or three
    select the third in the visible examples.
    """
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    if not height or not width:
        return out

    separator = next(
        (r for r, row in enumerate(grid) if all(value == 5 for value in row)),
        None,
    )
    if separator is None:
        return out

    palette = []
    for row in grid[:separator]:
        for value in row:
            if value not in (0, 1, 5) and value not in palette:
                palette.append(value)
    if not palette:
        return out

    seen = set()
    for start_r in range(separator + 1, height):
        for start_c in range(width):
            if grid[start_r][start_c] == 5 or (start_r, start_c) in seen:
                continue

            queue = deque([(start_r, start_c)])
            seen.add((start_r, start_c))
            component = []
            marker_count = 0

            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                marker_count += grid[r][c] == 1

                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if nr <= separator or nr >= height or nc < 0 or nc >= width:
                        continue
                    if grid[nr][nc] == 5 or (nr, nc) in seen:
                        continue
                    seen.add((nr, nc))
                    queue.append((nr, nc))

            fill = palette[(marker_count - 1) % len(palette)]
            for r, c in component:
                out[r][c] = fill

    return out
