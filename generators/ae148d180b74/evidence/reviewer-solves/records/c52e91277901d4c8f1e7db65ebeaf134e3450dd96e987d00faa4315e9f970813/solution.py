from collections import deque


def solve(grid):
    """Color every background cell lying on a shortest 2-to-3 path with 8."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    endpoints = {}
    for row in range(height):
        for col in range(width):
            if grid[row][col] in (2, 3):
                endpoints[grid[row][col]] = (row, col)

    if 2 not in endpoints or 3 not in endpoints:
        return [row[:] for row in grid]

    def distances(start):
        result = [[-1] * width for _ in range(height)]
        result[start[0]][start[1]] = 0
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            next_distance = result[row][col] + 1
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                new_row, new_col = row + drow, col + dcol
                if not (0 <= new_row < height and 0 <= new_col < width):
                    continue
                if grid[new_row][new_col] == 5 or result[new_row][new_col] != -1:
                    continue
                result[new_row][new_col] = next_distance
                queue.append((new_row, new_col))
        return result

    from_two = distances(endpoints[2])
    from_three = distances(endpoints[3])
    shortest = from_two[endpoints[3][0]][endpoints[3][1]]
    answer = [row[:] for row in grid]
    if shortest < 0:
        return answer

    for row in range(height):
        for col in range(width):
            if (
                grid[row][col] == 0
                and from_two[row][col] >= 0
                and from_three[row][col] >= 0
                and from_two[row][col] + from_three[row][col] == shortest
            ):
                answer[row][col] = 8
    return answer
