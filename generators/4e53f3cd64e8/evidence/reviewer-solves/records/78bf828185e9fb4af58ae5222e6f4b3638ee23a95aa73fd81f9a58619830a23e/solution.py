from __future__ import annotations


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            pending = [(row, col)]
            seen.add((row, col))
            cells = []
            while pending:
                rr, cc = pending.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] != 0
                    ):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            components.append(cells)
    return components


def _crop(grid, cells):
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    member = set(cells)
    return [
        [grid[row][col] if (row, col) in member else 0 for col in range(left, right + 1)]
        for row in range(top, bottom + 1)
    ]


def solve(grid):
    legend = [value for value in grid[0] if value != 0]
    body = grid[2:]
    by_color = {}
    for cells in _components(body):
        color = body[cells[0][0]][cells[0][1]]
        by_color[color] = cells

    crops = [_crop(body, by_color[color]) for color in legend]
    height = max(len(crop) for crop in crops)
    width = sum(len(crop[0]) for crop in crops) + len(crops) - 1
    output = [[0] * width for _ in range(height)]

    cursor = 0
    for crop in crops:
        for row, values in enumerate(crop):
            output[row][cursor : cursor + len(values)] = values
        cursor += len(crop[0]) + 1
    return output
