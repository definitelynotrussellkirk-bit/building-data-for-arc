from collections import deque


def solve(grid):
    """Fill each zero-region reachable from a 1..4 seed with that seed color."""
    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    if not source or not source[0]:
        return output

    height = len(source)
    width = len(source[0])
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    for start_row in range(height):
        for start_col in range(width):
            color = source[start_row][start_col]
            if color not in (1, 2, 3, 4):
                continue

            queue = deque([(start_row, start_col)])
            seen = {(start_row, start_col)}
            while queue:
                row, col = queue.popleft()
                for dr, dc in directions:
                    nr, nc = row + dr, col + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if (nr, nc) in seen:
                        continue
                    if source[nr][nc] not in (0, color):
                        continue
                    seen.add((nr, nc))
                    queue.append((nr, nc))

            for row, col in seen:
                if source[row][col] == 0:
                    output[row][col] = color

    return output
