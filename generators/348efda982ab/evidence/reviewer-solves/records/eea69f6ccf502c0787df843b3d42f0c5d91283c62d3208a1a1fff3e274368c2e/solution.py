from collections import deque


def solve(grid):
    """Fill rooms whose green-marker count equals their orange-door count."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]
    seen = [[False] * width for _ in range(height)]

    for start_r in range(height):
        for start_c in range(width):
            if seen[start_r][start_c] or grid[start_r][start_c] in (1, 7):
                continue

            room = []
            green_count = 0
            doors = set()
            queue = deque([(start_r, start_c)])
            seen[start_r][start_c] = True

            while queue:
                r, c = queue.popleft()
                room.append((r, c))
                green_count += grid[r][c] == 3

                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if grid[nr][nc] == 7:
                        doors.add((nr, nc))
                    elif grid[nr][nc] != 1 and not seen[nr][nc]:
                        seen[nr][nc] = True
                        queue.append((nr, nc))

            if green_count == len(doors):
                for r, c in room:
                    result[r][c] = 8
            else:
                for r, c in room:
                    if result[r][c] == 3:
                        result[r][c] = 0

    return result
