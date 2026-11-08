"""Visible-example solution for the five-panel binary-operation task."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    panel_width = (width - 4) // 5
    panels = []
    for index in range(5):
        left = index * (panel_width + 1)
        panels.append([row[left:left + panel_width] for row in grid])

    def combine(kind, first, second):
        output = [[0] * panel_width for _ in range(height)]
        for row in range(height):
            for column in range(panel_width):
                a = first[row][column] != 0
                b = second[row][column] != 0
                if kind == "union":
                    keep = a or b
                elif kind == "intersection":
                    keep = a and b
                else:
                    keep = a != b
                output[row][column] = 2 if keep else 0
        return output

    operation = None
    for candidate in ("union", "intersection", "xor"):
        if combine(candidate, panels[0], panels[1]) == panels[2]:
            operation = candidate
            break
    if operation is None:
        raise ValueError("third panel does not identify union/intersection/xor")
    return combine(operation, panels[3], panels[4])
