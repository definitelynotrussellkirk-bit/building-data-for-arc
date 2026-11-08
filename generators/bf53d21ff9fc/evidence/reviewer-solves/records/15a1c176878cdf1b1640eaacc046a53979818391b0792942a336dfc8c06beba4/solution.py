CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def solve(grid):
    """Move each route-attached gray marker to the route's penultimate cell."""
    height = len(grid)
    width = len(grid[0])
    source = [row[:] for row in grid]
    output = [row[:] for row in grid]

    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if source[row][col] == 5
    ]

    for marker_row, marker_col in markers:
        first = None
        for row_delta, col_delta in CARDINAL:
            row = marker_row + row_delta
            col = marker_col + col_delta
            if 0 <= row < height and 0 <= col < width and source[row][col] == 3:
                first = (row, col)
                break
        if first is None:
            continue

        previous = (marker_row, marker_col)
        current = first
        trail = [current]
        for _ in range(max(height, width)):
            following = None
            for row_delta, col_delta in CARDINAL:
                row = current[0] + row_delta
                col = current[1] + col_delta
                if (
                    0 <= row < height
                    and 0 <= col < width
                    and source[row][col] == 3
                    and (row, col) != previous
                ):
                    following = (row, col)
                    break
            if following is not None:
                previous, current = current, following
                trail.append(current)

        if len(trail) < 2:
            continue

        for row, col in trail:
            output[row][col] = 7
        endpoint_row, endpoint_col = trail[-1]
        landing_row, landing_col = trail[-2]
        output[endpoint_row][endpoint_col] = 3
        output[landing_row][landing_col] = 5
        output[marker_row][marker_col] = 7

    return output
