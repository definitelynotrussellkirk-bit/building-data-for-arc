"""Visible-example hypothesis: transfer a rotation between separated panels."""

def crop(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, x in enumerate(row) if x != 0]
    if not cells:
        return []
    r0, r1 = min(r for r,c in cells), max(r for r,c in cells)
    c0, c1 = min(c for r,c in cells), max(c for r,c in cells)
    return [row[c0:c1+1] for row in grid[r0:r1+1]]

def rotate(grid):
    return [list(row) for row in zip(*grid[::-1])] if grid else []

def solve(grid):
    separators = [c for c in range(len(grid[0])) if all(row[c] == 5 for row in grid)]
    boundaries = [-1] + separators + [len(grid[0])]
    panels = [crop([row[a+1:b] for row in grid])
              for a,b in zip(boundaries, boundaries[1:]) if b > a+1]
    if len(panels) != 3:
        raise ValueError("Expected three panels divided by gray columns")
    first, second, target = panels
    rotated_first = first
    rotated_target = target
    for _ in range(4):
        if rotated_first == second:
            return rotated_target
        rotated_first = rotate(rotated_first)
        rotated_target = rotate(rotated_target)
    return target
