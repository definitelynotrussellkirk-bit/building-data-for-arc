from collections import deque


DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid):
    """Return nonzero 4-connected monochrome components."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []
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
                cr, cc = current
                for dr, dc in DIR4:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append((color, cells))
    return result


def _enclosed_zeros(grid, cells):
    """Find zero regions inside a component bbox that cannot reach its edge."""
    row0 = min(row for row, _ in cells)
    row1 = max(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    col1 = max(col for _, col in cells)
    zeros = {
        (row, col)
        for row in range(row0, row1 + 1)
        for col in range(col0, col1 + 1)
        if grid[row][col] == 0
    }
    exterior = set()
    queue = deque()
    for cell in zeros:
        row, col = cell
        if row in (row0, row1) or col in (col0, col1):
            exterior.add(cell)
            queue.append(cell)
    while queue:
        row, col = queue.popleft()
        for dr, dc in DIR4:
            neighbor = (row + dr, col + dc)
            if neighbor in zeros and neighbor not in exterior:
                exterior.add(neighbor)
                queue.append(neighbor)
    return zeros - exterior


def solve(grid):
    output = [row[:] for row in grid]
    for color, cells in _components(grid):
        for row, col in _enclosed_zeros(grid, cells):
            output[row][col] = color
    return output
