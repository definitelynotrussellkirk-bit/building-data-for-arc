"""Infer the route between marker regions 1 and 2 from visible examples."""
from collections import deque


def solve(grid):
    height = len(grid)
    if height == 0:
        return []
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("Expected a rectangular grid")

    region_at = [[-1] * width for _ in range(height)]
    regions = []
    colors = []
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or region_at[row][col] >= 0:
                continue
            region_id = len(regions)
            cells = [(row, col)]
            region_at[row][col] = region_id
            for r, c in cells:
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < height and 0 <= nc < width and
                            region_at[nr][nc] < 0 and grid[nr][nc] == color):
                        region_at[nr][nc] = region_id
                        cells.append((nr, nc))
            regions.append(cells)
            colors.append(color)

    neighbors = [set() for _ in regions]
    for region_id, cells in enumerate(regions):
        for row, col in cells:
            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                if 0 <= nr < height and 0 <= nc < width:
                    other = region_at[nr][nc]
                    if other >= 0 and other != region_id:
                        neighbors[region_id].add(other)

    starts = [index for index, color in enumerate(colors) if color == 1]
    ends = [index for index, color in enumerate(colors) if color == 2]
    if len(starts) != 1 or len(ends) != 1:
        raise ValueError("Visible hypothesis requires one region of each marker color 1 and 2")
    start, end = starts[0], ends[0]
    parent = {start: None}
    queue = deque([start])
    while queue and end not in parent:
        current = queue.popleft()
        for other in sorted(neighbors[current]):
            if other not in parent:
                parent[other] = current
                queue.append(other)
    if end not in parent:
        raise ValueError("Marker regions are disconnected under the visible hypothesis")

    output = [[0] * width for _ in range(height)]
    current = end
    while current is not None:
        for row, col in regions[current]:
            output[row][col] = 8
        current = parent[current]
    return output
