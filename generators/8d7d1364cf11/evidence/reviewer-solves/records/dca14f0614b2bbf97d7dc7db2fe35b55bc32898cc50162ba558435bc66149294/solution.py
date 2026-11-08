"""Visible-example solution for the exposed post-repair episode."""


def _components(grid, background=4):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] == background or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col, grid[row][col]))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == dc == 0:
                            continue
                        nr, nc = row + dr, col + dc
                        if (
                            0 <= nr < height
                            and 0 <= nc < width
                            and grid[nr][nc] != background
                            and (nr, nc) not in seen
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            components.append(tuple(sorted(cells)))
    return components


def solve(grid):
    """Stamp the uniquely color-matched source component at each matching dot."""
    height, width = len(grid), len(grid[0])
    components = _components(grid)
    shapes = [component for component in components if len(component) > 1]
    dots = [component[0] for component in components if len(component) == 1]

    matches = {}
    for shape_index, shape in enumerate(shapes):
        for row, col, color in shape:
            matches.setdefault(color, []).append((shape_index, row, col))

    output = [[4 for _ in range(width)] for _ in range(height)]
    for dot_r, dot_c, color in dots:
        found = matches.get(color, [])
        if not found:
            continue
        shape_index, anchor_r, anchor_c = found[0]
        for row, col, value in shapes[shape_index]:
            nr = dot_r + row - anchor_r
            nc = dot_c + col - anchor_c
            if 0 <= nr < height and 0 <= nc < width:
                output[nr][nc] = value
    return output
