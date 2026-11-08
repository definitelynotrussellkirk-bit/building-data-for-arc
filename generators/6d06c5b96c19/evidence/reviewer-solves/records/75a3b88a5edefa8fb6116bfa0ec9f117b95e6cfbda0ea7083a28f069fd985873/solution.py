"""Infer a row roll from the exceptional cell in the left control column."""
from collections import Counter

def solve(grid):
    if not grid or not grid[0]:
        return []
    controls = [row[0] for row in grid]
    background = Counter(controls).most_common(1)[0][0]
    markers = [i for i, color in enumerate(controls) if color != background]
    shift = markers[0] if len(markers) == 1 else 0
    body = [list(row[1:]) for row in grid]
    return body[-shift:] + body[:-shift] if shift else body
