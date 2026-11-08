"""Visible-example hypothesis: crop the object and rotate by the corner cue."""


def solve(grid):
    rows = [list(row) for row in grid]
    turns = int(rows[0][0])
    if turns not in (1, 2, 3):
        raise ValueError("Expected the visible corner cue to be 1, 2, or 3")
    cells = [(r, c) for r, row in enumerate(rows) for c, value in enumerate(row)
             if value != 0 and (r, c) != (0, 0)]
    if not cells:
        raise ValueError("No object outside the corner cue")
    top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
    left, right = min(c for _, c in cells), max(c for _, c in cells)
    out = [row[left:right + 1] for row in rows[top:bottom + 1]]
    for _ in range(turns):
        out = [list(column) for column in zip(*out[::-1])]
    return out
