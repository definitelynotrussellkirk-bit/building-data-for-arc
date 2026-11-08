from collections import defaultdict, deque


def solve(grid):
    """Fill each empty cell with its uniquely nearest seed color around gray walls.

    Color 5 cells are impassable walls.  Every other nonzero color is a seed;
    repeated seeds of one color are treated as one multi-source region.  Distance
    is four-neighbor shortest-path distance through non-wall cells.  Cells tied
    between colors remain 0.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0

    seeds = defaultdict(list)
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color not in (0, 5):
                seeds[color].append((row, col))

    distances = {}
    unreachable = height * width + 1

    for color, starts in seeds.items():
        distance = [[unreachable] * width for _ in range(height)]
        queue = deque(starts)
        for row, col in starts:
            distance[row][col] = 0

        while queue:
            row, col = queue.popleft()
            next_distance = distance[row][col] + 1
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nrow, ncol = row + drow, col + dcol
                if (
                    0 <= nrow < height
                    and 0 <= ncol < width
                    and grid[nrow][ncol] != 5
                    and distance[nrow][ncol] > next_distance
                ):
                    distance[nrow][ncol] = next_distance
                    queue.append((nrow, ncol))

        distances[color] = distance

    result = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0:
                continue

            best_distance = unreachable
            best_color = 0
            tied = False

            for color, distance in distances.items():
                candidate = distance[row][col]
                if candidate < best_distance:
                    best_distance = candidate
                    best_color = color
                    tied = False
                elif candidate == best_distance:
                    tied = True

            if best_distance < unreachable and not tied:
                result[row][col] = best_color

    return result
