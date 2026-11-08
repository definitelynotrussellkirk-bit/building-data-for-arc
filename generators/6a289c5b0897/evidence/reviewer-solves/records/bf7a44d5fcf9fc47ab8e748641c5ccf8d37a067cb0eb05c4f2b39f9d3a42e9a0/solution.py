"""Visible-example solution for the generated 6a289c5b0897 episode."""
from collections import Counter, deque


def solve(grid):
    """Paint the selected shortest route between the two non-gray markers."""
    height = len(grid)
    width = len(grid[0])
    counts = Counter(value for row in grid for value in row)
    marker_colors = [
        color for color, count in counts.items()
        if color not in (0, 5) and count == 2
    ]
    if len(marker_colors) != 1:
        raise ValueError("expected exactly one marker color appearing twice")

    color = marker_colors[0]
    endpoints = sorted(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    )
    start, goal = endpoints

    # The examples select one shortest route deterministically.  Starting at the
    # row-major first marker, breadth-first search with U,D,L,R expansion matches
    # every visible output, including the tie-sensitive examples.
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))
    previous = {start: None}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        if (row, col) == goal:
            break
        for delta_row, delta_col in directions:
            nxt = row + delta_row, col + delta_col
            if (
                0 <= nxt[0] < height
                and 0 <= nxt[1] < width
                and nxt not in previous
                and grid[nxt[0]][nxt[1]] != 5
            ):
                previous[nxt] = (row, col)
                queue.append(nxt)

    if goal not in previous:
        raise ValueError("marker pair is disconnected")

    output = [[0 for _ in range(width)] for _ in range(height)]
    cursor = goal
    while cursor is not None:
        output[cursor[0]][cursor[1]] = color
        cursor = previous[cursor]
    return output
