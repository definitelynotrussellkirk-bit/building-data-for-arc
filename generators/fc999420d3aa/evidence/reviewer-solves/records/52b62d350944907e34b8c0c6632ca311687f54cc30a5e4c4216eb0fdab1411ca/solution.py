from collections import deque


def solve(grid):
    """Complete every four-cell T tetromino into a five-cell plus."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            component = []
            while queue:
                current = queue.popleft()
                component.append(current)
                current_row, current_col = current
                for delta_row, delta_col in directions:
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            if len(component) != 4:
                continue

            cells = set(component)
            center = None
            for candidate_row, candidate_col in component:
                occupied_neighbors = sum(
                    (candidate_row + delta_row, candidate_col + delta_col) in cells
                    for delta_row, delta_col in directions
                )
                if occupied_neighbors == 3:
                    center = (candidate_row, candidate_col)
                    break

            if center is None:
                continue

            center_row, center_col = center
            missing = []
            for delta_row, delta_col in directions:
                next_row = center_row + delta_row
                next_col = center_col + delta_col
                if not (0 <= next_row < height and 0 <= next_col < width):
                    continue
                if (next_row, next_col) not in cells:
                    missing.append((next_row, next_col))

            if len(missing) == 1 and grid[missing[0][0]][missing[0][1]] == 0:
                out[missing[0][0]][missing[0][1]] = color

    return out
