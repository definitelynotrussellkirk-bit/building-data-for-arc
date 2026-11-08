"""Infer a framed object's selection and fill rule from visible examples."""

from fractions import Fraction


def solve(grid):
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 1}
    frames = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        pending = [start]
        while pending:
            r, c = pending.pop()
            for cell in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if cell in unseen:
                    unseen.remove(cell)
                    component.add(cell)
                    pending.append(cell)
        top = min(r for r, c in component)
        bottom = max(r for r, c in component)
        left = min(c for r, c in component)
        right = max(c for r, c in component)
        if bottom - top < 2 or right - left < 2:
            continue
        border = {(r, c) for r in range(top, bottom + 1) for c in range(left, right + 1)
                  if r in (top, bottom) or c in (left, right)}
        if component != border:
            continue
        area = (bottom - top - 1) * (right - left - 1)
        red = sum(grid[r][c] == 2 for r in range(top + 1, bottom)
                  for c in range(left + 1, right))
        frames.append((Fraction(red, area), -top, -left, top, bottom, left, right))
    if not frames:
        raise ValueError("No complete blue frame found")
    _, _, _, top, bottom, left, right = max(frames)
    return [[3 if grid[r][c] == 0 else grid[r][c]
             for c in range(left, right + 1)] for r in range(top, bottom + 1)]
