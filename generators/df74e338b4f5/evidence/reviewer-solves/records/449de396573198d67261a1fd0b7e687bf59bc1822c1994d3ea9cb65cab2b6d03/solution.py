from copy import deepcopy


def _components_of_nine(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != 9 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 9
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def solve(grid):
    if not grid or not grid[0]:
        return deepcopy(grid)

    frames = []
    for cells in _components_of_nine(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        frames.append((min(rows), min(cols), max(rows), max(cols)))

    output = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in (0, 9):
                output[r][c] = sum(
                    r0 < r < r1 and c0 < c < c1
                    for r0, c0, r1, c1 in frames
                )
    return output
