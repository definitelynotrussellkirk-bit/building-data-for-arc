from collections import deque


_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _same_color_components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            cells = set()
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                current = queue.popleft()
                cells.add(current)
                r, c = current
                for dr, dc in _DIR4:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            yield color, cells


def _enclosed_bbox_cells(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    row_min, row_max = min(rows), max(rows)
    col_min, col_max = min(cols), max(cols)

    empty = {
        (row, col)
        for row in range(row_min, row_max + 1)
        for col in range(col_min, col_max + 1)
        if (row, col) not in cells
    }
    exterior = {
        (row, col)
        for row, col in empty
        if row in (row_min, row_max) or col in (col_min, col_max)
    }
    queue = deque(exterior)
    while queue:
        row, col = queue.popleft()
        for dr, dc in _DIR4:
            neighbor = (row + dr, col + dc)
            if neighbor in empty and neighbor not in exterior:
                exterior.add(neighbor)
                queue.append(neighbor)
    return empty - exterior


def solve(grid):
    output = [row[:] for row in grid]
    for color, cells in _same_color_components(grid):
        for row, col in _enclosed_bbox_cells(cells):
            if output[row][col] == 0:
                output[row][col] = color
    return output
