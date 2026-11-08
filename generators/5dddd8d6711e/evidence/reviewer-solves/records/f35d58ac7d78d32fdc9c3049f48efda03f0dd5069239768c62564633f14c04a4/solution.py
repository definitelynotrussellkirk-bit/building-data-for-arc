from collections import deque


def solve(grid):
    """Highlight the sequence of rooms linking the color-2 and color-3 cells."""
    height = len(grid)
    width = len(grid[0])
    wall = grid[0][0]
    door = 7

    # A room is a 4-connected component after treating both walls and doors as
    # boundaries.  Door cells are added back later as graph edges between rooms.
    room_of = [[-1] * width for _ in range(height)]
    rooms = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] in (wall, door) or room_of[row][col] != -1:
                continue
            room_id = len(rooms)
            cells = []
            queue = deque([(row, col)])
            room_of[row][col] = room_id
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if room_of[nr][nc] != -1:
                        continue
                    if grid[nr][nc] in (wall, door):
                        continue
                    room_of[nr][nc] = room_id
                    queue.append((nr, nc))
            rooms.append(cells)

    graph = [set() for _ in rooms]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != door:
                continue
            adjacent = set()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = row + dr, col + dc
                if 0 <= nr < height and 0 <= nc < width:
                    room_id = room_of[nr][nc]
                    if room_id != -1:
                        adjacent.add(room_id)
            # A valid doorway separates exactly two room interiors.
            if len(adjacent) == 2:
                left, right = tuple(adjacent)
                graph[left].add(right)
                graph[right].add(left)

    start = goal = None
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 2:
                start = room_of[row][col]
            elif grid[row][col] == 3:
                goal = room_of[row][col]

    path = []
    if start is not None and goal is not None:
        previous = {start: None}
        queue = deque([start])
        while queue and goal not in previous:
            room_id = queue.popleft()
            for neighbor in sorted(graph[room_id]):
                if neighbor not in previous:
                    previous[neighbor] = room_id
                    queue.append(neighbor)
        if goal in previous:
            cursor = goal
            while cursor is not None:
                path.append(cursor)
                cursor = previous[cursor]
            path.reverse()

    output = [row[:] for row in grid]

    # Remove endpoint and distractor tokens everywhere.
    for row in range(height):
        for col in range(width):
            if output[row][col] not in (0, wall, door):
                output[row][col] = 0

    # Fill every room on the connecting route; walls and doorway cells remain.
    for room_id in path:
        for row, col in rooms[room_id]:
            output[row][col] = 8

    return output
