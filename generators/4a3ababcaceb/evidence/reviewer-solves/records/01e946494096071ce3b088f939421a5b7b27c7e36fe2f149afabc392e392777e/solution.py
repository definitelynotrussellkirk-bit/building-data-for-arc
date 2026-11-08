"""Visible-example solution for the assigned ARC puzzle.

The grid is partitioned into equal rooms by full rows/columns of color 9.
One room is marked with color 3.  A blue (2) pattern elsewhere supplies the
mask to paint into that room with azure (8).  When several blue rooms exist,
the examples identify the intended source as the one containing exactly one
non-blue, non-background marker; otherwise the nearest blue room is used.
"""


def _runs_between_separators(length, separators):
    separators = set(separators)
    runs = []
    start = 0
    for index in range(length + 1):
        if index == length or index in separators:
            if start < index:
                runs.append((start, index))
            start = index + 1
    return runs


def solve(grid):
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    separator_rows = [
        row for row in range(height) if all(value == 9 for value in grid[row])
    ]
    separator_cols = [
        col
        for col in range(width)
        if all(grid[row][col] == 9 for row in range(height))
    ]
    row_runs = _runs_between_separators(height, separator_rows)
    col_runs = _runs_between_separators(width, separator_cols)

    rooms = []
    target = None
    for room_row, (r0, r1) in enumerate(row_runs):
        for room_col, (c0, c1) in enumerate(col_runs):
            values = [grid[r][c] for r in range(r0, r1) for c in range(c0, c1)]
            room = {
                "room_row": room_row,
                "room_col": room_col,
                "bounds": (r0, r1, c0, c1),
                "values": values,
            }
            rooms.append(room)
            if 3 in values:
                target = room

    if target is None:
        return [row[:] for row in grid]

    tr0, tr1, tc0, tc1 = target["bounds"]
    target_shape = (tr1 - tr0, tc1 - tc0)
    candidates = []
    for room in rooms:
        if room is target or 2 not in room["values"]:
            continue
        r0, r1, c0, c1 = room["bounds"]
        if (r1 - r0, c1 - c0) != target_shape:
            continue
        foreign_count = sum(value not in (0, 2) for value in room["values"])
        distance = abs(room["room_row"] - target["room_row"]) + abs(
            room["room_col"] - target["room_col"]
        )
        blue_count = room["values"].count(2)
        # The demonstrated source has one embedded non-blue marker whenever
        # such a room exists.  Distance and then support size break ties.
        room["score"] = (
            0 if foreign_count == 1 else 1,
            abs(foreign_count - 1),
            distance,
            -blue_count,
            room["room_row"],
            room["room_col"],
        )
        candidates.append(room)

    if not candidates:
        return [row[:] for row in grid]

    source = min(candidates, key=lambda room: room["score"])
    sr0, sr1, sc0, sc1 = source["bounds"]

    output = [row[:] for row in grid]
    for dr in range(target_shape[0]):
        for dc in range(target_shape[1]):
            output[tr0 + dr][tc0 + dc] = 8 if grid[sr0 + dr][sc0 + dc] == 2 else 0
    return output
