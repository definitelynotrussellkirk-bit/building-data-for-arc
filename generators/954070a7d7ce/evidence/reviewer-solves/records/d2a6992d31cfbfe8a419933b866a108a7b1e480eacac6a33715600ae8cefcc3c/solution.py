"""Frame-local line completion inferred from the visible solve challenge.

No project code, generators, reference programs, or private labels are imported.
Earlier exposure during authoring is declared in SOLVE_NOTES.md.
"""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("Expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("Expected a rectangular grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("Expected integer colors 0 through 9")
    output = [row[:] for row in grid]
    walls = {(row, col) for row in range(len(grid)) for col in range(width) if grid[row][col] == 9}
    while walls:
        origin = min(walls)
        walls.remove(origin)
        stack, component = [origin], {origin}
        while stack:
            row, col = stack.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in walls:
                    walls.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        top = min(row for row, _ in component)
        bottom = max(row for row, _ in component)
        left = min(col for _, col in component)
        right = max(col for _, col in component)
        border = {(row, col) for row in range(top, bottom + 1) for col in range(left, right + 1)
                  if row in (top, bottom) or col in (left, right)}
        if component != border or bottom - top < 3 or right - left < 3:
            raise ValueError("Expected separate hollow rectangular frames")
        top_marks = [(col, grid[top + 1][col]) for col in range(left + 2, right)
                     if grid[top + 1][col] not in (0, 9)]
        left_marks = [(row, grid[row][left + 1]) for row in range(top + 2, bottom)
                      if grid[row][left + 1] not in (0, 9)]
        if len(top_marks) != 1 or len(left_marks) != 1 or top_marks[0][1] != left_marks[0][1]:
            raise ValueError("Expected matching top and left markers in each frame")
        column, color = top_marks[0]
        row, _ = left_marks[0]
        for r in range(top + 1, bottom):
            output[r][column] = color
        for c in range(left + 1, right):
            output[row][c] = color
    return output
