"""Extract the gray-frame interior and rotate it by the corner marker."""


def solve(grid):
    """Return the framed payload after 0, 1, 2, or 3 clockwise turns.

    The visible demonstrations use a top-left marker from 1 through 4
    and a rectangular border of color 5. Color 5 can also occur inside
    the border, so the interior is sliced geometrically, not filtered.
    """
    marker = grid[0][0]
    if marker not in (1, 2, 3, 4):
        raise ValueError("Expected a top-left rotation marker from 1 to 4")

    gray = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 5
    ]
    if not gray:
        raise ValueError("Expected a gray rectangular frame")

    top = min(row for row, column in gray)
    bottom = max(row for row, column in gray)
    left = min(column for row, column in gray)
    right = max(column for row, column in gray)
    if bottom - top < 2 or right - left < 2:
        raise ValueError("Expected a frame with a nonempty interior")

    payload = [list(row[left + 1:right]) for row in grid[top + 1:bottom]]
    for _ in range(marker - 1):
        payload = [list(row) for row in zip(*payload[::-1])]
    return payload
