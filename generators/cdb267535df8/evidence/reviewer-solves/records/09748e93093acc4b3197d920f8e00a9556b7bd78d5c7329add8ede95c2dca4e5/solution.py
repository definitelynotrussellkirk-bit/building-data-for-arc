from collections import deque


def solve(grid):
    """Fill each non-wall cell from its uniquely nearest colored source.

    Color 5 cells are impassable walls.  Every other nonzero cell is a source.
    Distances are four-neighbour shortest-path distances through non-wall cells.
    A cell keeps the source color when all nearest sources have that color;
    cells tied between different colors stay 0.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    sources = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 5)
    ]

    distances = []
    for source_row, source_col, color in sources:
        distance = [[-1] * width for _ in range(height)]
        distance[source_row][source_col] = 0
        queue = deque([(source_row, source_col)])

        while queue:
            row, col = queue.popleft()
            next_distance = distance[row][col] + 1
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                new_row = row + drow
                new_col = col + dcol
                if not (0 <= new_row < height and 0 <= new_col < width):
                    continue
                if grid[new_row][new_col] == 5:
                    continue
                if distance[new_row][new_col] != -1:
                    continue
                distance[new_row][new_col] = next_distance
                queue.append((new_row, new_col))

        distances.append((color, distance))

    output = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 5:
                continue

            reachable = [
                (distance[row][col], color)
                for color, distance in distances
                if distance[row][col] >= 0
            ]
            if not reachable:
                output[row][col] = 0
                continue

            nearest_distance = min(distance for distance, _ in reachable)
            nearest_colors = {
                color
                for distance, color in reachable
                if distance == nearest_distance
            }
            output[row][col] = (
                next(iter(nearest_colors)) if len(nearest_colors) == 1 else 0
            )

    return output
