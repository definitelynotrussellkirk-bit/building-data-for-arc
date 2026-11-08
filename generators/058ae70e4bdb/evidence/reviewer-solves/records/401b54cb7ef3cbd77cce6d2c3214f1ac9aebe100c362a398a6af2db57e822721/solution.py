from copy import deepcopy


def solve(grid):
    """Flood each 4-connected non-8 region iff it contains one nonzero color."""
    out = deepcopy(grid)
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] == 8 or (start_r, start_c) in seen:
                continue

            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells = []
            colors = set()

            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                if grid[r][c] not in (0, 8):
                    colors.add(grid[r][c])
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and grid[rr][cc] != 8
                        and (rr, cc) not in seen
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))

            if len(colors) == 1:
                fill = next(iter(colors))
                for r, c in cells:
                    out[r][c] = fill

    return out
