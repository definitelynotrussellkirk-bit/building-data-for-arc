"""Standalone public-example solution. No generator or reference dependencies."""
from typing import List


def solve(grid: List[List[int]]) -> List[List[int]]:
    """Crop the non-marker scene and turn clockwise once per top-row marker.

    The four supplied examples establish the marker-count mapping 1->1,
    2->2, 3->3, 4->0 quarter turns. Earlier rule exposure is disclosed in
    SOLVE_NOTES.md; this is not a blind-solve claim.
    """
    if (not isinstance(grid, list) or not grid or
            any(not isinstance(row, list) for row in grid) or not grid[0]):
        raise ValueError('grid must be a nonempty list of nonempty rows')
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError('grid must be rectangular')
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError('grid values must be integer colors 0..9')
    turns = grid[0].count(9) % 4
    scene = [row[:] for row in grid]
    scene[0] = [0 if color == 9 else color for color in scene[0]]
    occupied = [(r, c) for r, row in enumerate(scene)
                for c, color in enumerate(row) if color != 0]
    if not occupied:
        return []
    top = min(r for r, c in occupied)
    bottom = max(r for r, c in occupied)
    left = min(c for r, c in occupied)
    right = max(c for r, c in occupied)
    output = [row[left:right + 1] for row in scene[top:bottom + 1]]
    for _ in range(turns):
        output = [list(row) for row in zip(*output[::-1])]
    return output
