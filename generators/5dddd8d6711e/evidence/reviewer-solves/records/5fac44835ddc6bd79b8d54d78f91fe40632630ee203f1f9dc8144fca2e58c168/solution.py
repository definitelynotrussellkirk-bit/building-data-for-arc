"""Infer a route through rooms connected by orange doors."""

from collections import deque


def solve(grid):
    """Fill the selected minimum-door room route from red to green with cyan.

    Rooms are numbered by their first cell in row-major order.  Neighbors are
    explored in that order to make an otherwise ambiguous shortest route
    deterministic.  This tie choice matches the visible training example.
    """
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    height, width = len(grid), len(grid[0])
    directions = ((-1, 0), (0, -1), (0, 1), (1, 0))
    owner = {}
    rooms = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] in (1, 7) or (row, col) in owner:
                continue
            room_id = len(rooms)
            room = []
            queue = deque([(row, col)])
            owner[row, col] = room_id
            while queue:
                r, c = queue.popleft()
                room.append((r, c))
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] not in (1, 7)
                        and (nr, nc) not in owner
                    ):
                        owner[nr, nc] = room_id
                        queue.append((nr, nc))
            rooms.append(room)

    neighbors = [set() for _ in rooms]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 7:
                continue
            adjacent = {
                owner[row + dr, col + dc]
                for dr, dc in directions
                if (row + dr, col + dc) in owner
            }
            for room_id in adjacent:
                neighbors[room_id].update(adjacent - {room_id})

    start = goal = None
    for (row, col), room_id in owner.items():
        if grid[row][col] == 2:
            start = room_id
        elif grid[row][col] == 3:
            goal = room_id
    if start is None or goal is None:
        raise ValueError("The visible task requires red and green markers.")

    parents = {start: None}
    queue = deque([start])
    while queue and goal not in parents:
        current = queue.popleft()
        for neighbor in sorted(neighbors[current]):
            if neighbor not in parents:
                parents[neighbor] = current
                queue.append(neighbor)
    if goal not in parents:
        raise ValueError("The red and green rooms are not connected.")

    selected = set()
    current = goal
    while current is not None:
        selected.add(current)
        current = parents[current]

    output = [list(row) for row in grid]
    for (row, col), room_id in owner.items():
        output[row][col] = 8 if room_id in selected else 0
    return output
