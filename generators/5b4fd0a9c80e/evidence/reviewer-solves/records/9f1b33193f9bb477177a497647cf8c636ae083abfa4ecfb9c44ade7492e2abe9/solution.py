"""Solve the visible stack-crops puzzle without generator/reference imports."""
from collections import deque


def _components(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            top, bottom = min(rows), max(rows)
            left, right = min(cols), max(cols)
            crop = [input_row[left : right + 1] for input_row in grid[top : bottom + 1]]
            result.append((len(cells), top, left, crop))
    return result


def solve(grid):
    """Crop each colored component, order by area/location, and stack centered."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")

    components = sorted(_components(grid), key=lambda item: item[:3])
    if not components:
        raise ValueError("grid must contain at least one nonzero component")

    output_width = max(len(crop[0]) for _, _, _, crop in components)
    output_height = sum(len(crop) for _, _, _, crop in components) + len(components) - 1
    output = [[0] * output_width for _ in range(output_height)]

    output_row = 0
    for _, _, _, crop in components:
        output_col = (output_width - len(crop[0])) // 2
        for row_offset, crop_row in enumerate(crop):
            output[output_row + row_offset][output_col : output_col + len(crop_row)] = crop_row
        output_row += len(crop) + 1
    return output
