from collections import defaultdict, deque


def solve(grid):
    """Paint the clue-selected shortest route through a rectangular room maze."""
    height = len(grid)
    width = len(grid[0])

    # Full blue/orange lines are the maze walls; orange cells are door openings.
    wall_rows = [
        row
        for row in range(height)
        if all(grid[row][col] in (1, 7) for col in range(width))
    ]
    wall_cols = [
        col
        for col in range(width)
        if all(grid[row][col] in (1, 7) for row in range(height))
    ]

    cell_room = {}
    rooms = []
    for room_row, (top, bottom) in enumerate(zip(wall_rows, wall_rows[1:])):
        for room_col, (left, right) in enumerate(zip(wall_cols, wall_cols[1:])):
            room = (room_row, room_col)
            rooms.append(room)
            for row in range(top + 1, bottom):
                for col in range(left + 1, right):
                    cell_room[(row, col)] = room

    adjacency = defaultdict(set)
    door_cells = defaultdict(list)

    # Doors in vertical walls.
    for room_row, (top, bottom) in enumerate(zip(wall_rows, wall_rows[1:])):
        for wall_index in range(1, len(wall_cols) - 1):
            col = wall_cols[wall_index]
            left_room = (room_row, wall_index - 1)
            right_room = (room_row, wall_index)
            doors = [
                (row, col)
                for row in range(top + 1, bottom)
                if grid[row][col] == 7
            ]
            if doors:
                adjacency[left_room].add(right_room)
                adjacency[right_room].add(left_room)
                door_cells[frozenset((left_room, right_room))].extend(doors)

    # Doors in horizontal walls.
    for wall_index in range(1, len(wall_rows) - 1):
        row = wall_rows[wall_index]
        for room_col, (left, right) in enumerate(zip(wall_cols, wall_cols[1:])):
            upper_room = (wall_index - 1, room_col)
            lower_room = (wall_index, room_col)
            doors = [
                (row, col)
                for col in range(left + 1, right)
                if grid[row][col] == 7
            ]
            if doors:
                adjacency[upper_room].add(lower_room)
                adjacency[lower_room].add(upper_room)
                door_cells[frozenset((upper_room, lower_room))].extend(doors)

    start_room = None
    target_room = None
    clue_count = defaultdict(int)
    start_cell = None
    target_cell = None
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            room = cell_room.get((row, col))
            if value == 2:
                start_room = room
                start_cell = (row, col)
            elif value == 3:
                target_room = room
                target_cell = (row, col)
            elif value not in (0, 1, 2, 3, 7) and room is not None:
                clue_count[room] += 1

    if start_room is None or target_room is None:
        return [row[:] for row in grid]

    def room_distances(origin):
        distances = {origin: 0}
        queue = deque([origin])
        while queue:
            room = queue.popleft()
            for neighbor in adjacency[room]:
                if neighbor not in distances:
                    distances[neighbor] = distances[room] + 1
                    queue.append(neighbor)
        return distances

    from_start = room_distances(start_room)
    from_target = room_distances(target_room)
    shortest_edges = from_start[target_room]

    shortest_paths = []

    def collect_shortest(room, path):
        if room == target_room:
            shortest_paths.append(tuple(path))
            return
        for neighbor in sorted(adjacency[room]):
            if from_start.get(neighbor) != from_start[room] + 1:
                continue
            if from_start[neighbor] + from_target.get(neighbor, 10**9) != shortest_edges:
                continue
            collect_shortest(neighbor, path + [neighbor])

    collect_shortest(start_room, [start_room])

    best_clues = max(
        sum(clue_count[room] for room in path) for path in shortest_paths
    )
    clue_best = [
        path
        for path in shortest_paths
        if sum(clue_count[room] for room in path) == best_clues
    ]

    def route_cell_distance(path):
        allowed = set()
        for room in path:
            allowed.update(cell for cell, owner in cell_room.items() if owner == room)
        for first, second in zip(path, path[1:]):
            allowed.update(door_cells[frozenset((first, second))])

        queue = deque([start_cell])
        distances = {start_cell: 0}
        while queue:
            cell = queue.popleft()
            if cell == target_cell:
                return distances[cell]
            row, col = cell
            for next_cell in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if next_cell in allowed and next_cell not in distances:
                    distances[next_cell] = distances[cell] + 1
                    queue.append(next_cell)
        return 10**9

    selected_path = min(clue_best, key=lambda path: (route_cell_distance(path), path))
    selected_rooms = set(selected_path)

    output = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] in (1, 7):
                continue
            output[row][col] = 8 if cell_room.get((row, col)) in selected_rooms else 0
    return output
