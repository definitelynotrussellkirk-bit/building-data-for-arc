"""Fill each panel's blank cells with the next panel's color, cyclically."""

from collections import Counter


def solve(grid):
    height, width = len(grid), len(grid[0])
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    panels = []
    column = 0
    while column < width:
        if all(grid[row][column] == background for row in range(height)):
            column += 1
            continue
        start = column
        while column < width and any(grid[row][column] != background for row in range(height)):
            column += 1
        colors = {grid[row][col] for row in range(height) for col in range(start, column)} - {background}
        if len(colors) != 1:
            raise ValueError("Expected one foreground color per vertical panel")
        panels.append((start, column, colors.pop()))
    if len(panels) < 2:
        raise ValueError("Expected multiple panels separated by background columns")
    output = [list(row) for row in grid]
    for index, (start, stop, _) in enumerate(panels):
        fill = panels[(index + 1) % len(panels)][2]
        for row in range(height):
            for col in range(start, stop):
                if output[row][col] == background:
                    output[row][col] = fill
    return output
