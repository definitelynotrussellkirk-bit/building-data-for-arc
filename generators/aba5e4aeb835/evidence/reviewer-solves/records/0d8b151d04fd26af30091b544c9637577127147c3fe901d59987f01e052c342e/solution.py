"""Visible-example-only solution for the blind ARC episode."""

from __future__ import annotations

from copy import deepcopy


# Clockwise order: north, east, south, west.
_DIRECTIONS = ((-1, 0), (0, 1), (1, 0), (0, -1))


def _turn(direction: int, handedness: str) -> int:
    """Return the direction after a 90-degree left or right turn."""
    return (direction + (-1 if handedness == "left" else 1)) % 4


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Trace the encoded orthogonal route, painting traversed zeros with 8."""
    output = deepcopy(grid)
    height = len(grid)
    width = len(grid[0])

    start = next(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    )

    # The visible lessons give one aligned 3/4 waypoint from the red start.
    candidates: list[tuple[int, int, tuple[int, int], int]] = []
    for direction, (delta_row, delta_col) in enumerate(_DIRECTIONS):
        row = start[0] + delta_row
        col = start[1] + delta_col
        distance = 1
        while 0 <= row < height and 0 <= col < width:
            if grid[row][col] in (3, 4):
                candidates.append(
                    (distance, direction, (row, col), grid[row][col])
                )
                break
            row += delta_row
            col += delta_col
            distance += 1

    if not candidates:
        return output

    _, direction, current, current_color = min(candidates)

    # Paint the initial segment, excluding both colored endpoints.
    delta_row, delta_col = _DIRECTIONS[direction]
    row = start[0] + delta_row
    col = start[1] + delta_col
    while (row, col) != current:
        if output[row][col] == 0:
            output[row][col] = 8
        row += delta_row
        col += delta_col

    handedness = "left"

    while True:
        direction = _turn(direction, handedness)
        delta_row, delta_col = _DIRECTIONS[direction]
        row = current[0] + delta_row
        col = current[1] + delta_col
        crossed_gray = False
        next_waypoint: tuple[int, int, int] | None = None

        while 0 <= row < height and 0 <= col < width:
            value = grid[row][col]
            if value == 5:
                crossed_gray = True
            if value in (3, 4):
                next_waypoint = (row, col, value)
                break
            if output[row][col] == 0:
                output[row][col] = 8
            row += delta_row
            col += delta_col

        # Reaching the border completes the route.
        if next_waypoint is None:
            break

        # A gray marker makes this the final segment: arrive but do not turn.
        if crossed_gray:
            break

        next_row, next_col, next_color = next_waypoint
        if next_color == current_color:
            handedness = "right" if handedness == "left" else "left"
        current = (next_row, next_col)
        current_color = next_color

    return output
