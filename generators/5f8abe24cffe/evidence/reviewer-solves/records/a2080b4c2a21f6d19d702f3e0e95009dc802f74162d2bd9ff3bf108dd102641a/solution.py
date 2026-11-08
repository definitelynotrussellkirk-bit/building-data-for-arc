"""Infer a geometric transform from a matching pair of framed panels."""


def _panels(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    panels = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue
            todo = [(row, col)]
            seen.add((row, col))
            component = []
            while todo:
                r, c = todo.pop()
                component.append((r, c))
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if 0 <= rr < height and 0 <= cc < width and grid[rr][cc] == 1 and (rr, cc) not in seen:
                        seen.add((rr, cc))
                        todo.append((rr, cc))
            r0 = min(r for r, c in component) + 1
            r1 = max(r for r, c in component)
            c0 = min(c for r, c in component) + 1
            c1 = max(c for r, c in component)
            foreground = [(r, c) for r in range(r0, r1) for c in range(c0, c1) if grid[r][c] != 0]
            if not foreground:
                continue
            top = min(r for r, c in foreground)
            bottom = max(r for r, c in foreground) + 1
            left = min(c for r, c in foreground)
            right = max(c for r, c in foreground) + 1
            panels.append([line[left:right] for line in grid[top:bottom]])
    return panels


def _transform(grid, reflected, turns):
    result = [row[::-1] if reflected else row[:] for row in grid]
    for _ in range(turns):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def solve(grid):
    panels = _panels(grid)
    if len(panels) != 3:
        raise ValueError('Expected three framed panels')
    # The first visible lesson breaks a symmetry in favor of pure rotation.
    for reflected in (False, True):
        for turns in range(4):
            for first in range(3):
                for second in range(first + 1, 3):
                    if _transform(panels[first], reflected, turns) == panels[second]:
                        remaining = next(i for i in range(3) if i not in (first, second))
                        return _transform(panels[remaining], reflected, turns)
    raise ValueError('No geometric relation between any pair of panels')
