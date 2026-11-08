from collections import deque


def solve(grid):
    """Fill each non-wall component by wall-aware nearest colored seed."""
    height, width = len(grid), len(grid[0])
    infinity = height * width + 1
    seeds = [
        (value, row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 5)
    ]

    distance_maps = []
    for color, start_row, start_col in seeds:
        distance = [[infinity] * width for _ in range(height)]
        distance[start_row][start_col] = 0
        queue = deque([(start_row, start_col)])
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = row + dr, col + dc
                if (
                    0 <= nr < height
                    and 0 <= nc < width
                    and grid[nr][nc] != 5
                    and distance[nr][nc] == infinity
                ):
                    distance[nr][nc] = distance[row][col] + 1
                    queue.append((nr, nc))
        distance_maps.append((color, distance))

    output = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 5:
                continue
            candidates = [
                (distance[row][col], color)
                for color, distance in distance_maps
                if distance[row][col] < infinity
            ]
            output[row][col] = min(candidates)[1] if candidates else 0
    return output
