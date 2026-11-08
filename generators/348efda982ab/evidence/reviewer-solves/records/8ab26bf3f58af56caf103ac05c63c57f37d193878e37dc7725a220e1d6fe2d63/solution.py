from collections import deque


def solve(grid):
    """Fill rooms whose marker count equals their number of doors.

    Colors 1 and 9 are walls and color 7 is a door cut into a wall.  Rooms are
    the 4-connected components of all other cells when doors are treated as
    boundaries.  Green marker cells (3) are erased in every room.  A room is
    filled with 8 exactly when its number of markers equals the number of
    distinct adjacent doors.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]
    boundary_colors = {1, 7, 9}
    seen = set()

    for row in range(height):
        for col in range(width):
            if (row, col) in seen or grid[row][col] in boundary_colors:
                continue

            component = []
            doors = set()
            marker_count = 0
            queue = deque([(row, col)])
            seen.add((row, col))

            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                if grid[r][c] == 3:
                    marker_count += 1

                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if grid[nr][nc] == 7:
                        doors.add((nr, nc))
                    elif (
                        grid[nr][nc] not in boundary_colors
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            fill = 8 if marker_count == len(doors) else 0
            for r, c in component:
                result[r][c] = fill

    return result
