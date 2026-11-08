"""Visible-example solution for blind task 0f25172eefa4."""


def _rotate_clockwise(tile):
    return [list(row) for row in zip(*tile[::-1])]


def _rotate(tile, quarter_turns):
    result = [row[:] for row in tile]
    for _ in range(quarter_turns % 4):
        result = _rotate_clockwise(result)
    return result


def _crop_upper_object(grid):
    upper = grid[:-1]
    occupied = [
        (r, c)
        for r, row in enumerate(upper)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not occupied:
        return []
    top = min(r for r, _ in occupied)
    bottom = max(r for r, _ in occupied)
    left = min(c for _, c in occupied)
    right = max(c for _, c in occupied)
    return [row[left : right + 1] for row in upper[top : bottom + 1]]


def solve(grid):
    """Expand the upper object according to bottom-row rotation commands.

    Visible examples establish command 2 and command 5 as unrotated copies,
    command 3 as one clockwise quarter-turn, and command 4 as a half-turn.
    Copies are top-aligned and separated by one zero column.
    """
    if not grid or not grid[0]:
        return []

    tile = _crop_upper_object(grid)
    if not tile:
        return []

    turns_by_command = {2: 0, 3: 1, 4: 2, 5: 0}
    commands = [value for value in grid[-1] if value != 0]
    tiles = [_rotate(tile, turns_by_command[value]) for value in commands]
    if not tiles:
        return []

    output_height = max(len(copy) for copy in tiles)
    output = [[] for _ in range(output_height)]
    for index, copy in enumerate(tiles):
        width = len(copy[0])
        for r in range(output_height):
            if r < len(copy):
                output[r].extend(copy[r])
            else:
                output[r].extend([0] * width)
            if index + 1 < len(tiles):
                output[r].append(0)
    return output
