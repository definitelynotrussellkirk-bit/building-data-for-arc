from copy import deepcopy


def _components(grid, color=4):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] != color or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def solve(grid):
    """Rank the two color-4 rectangles by area and recolor their interiors."""
    output = deepcopy(grid)
    objects = []
    for cells in _components(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        objects.append((len(cells), min(rows), min(cols), max(rows), max(cols)))
    objects.sort(key=lambda item: item[0])
    for fill_color, (_area, r1, c1, r2, c2) in enumerate(objects, start=1):
        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                if grid[r][c] == 4:
                    output[r][c] = fill_color
    return output
