"""Visible-example inference: move loose paint into a matching object's gaps."""
from collections import Counter, deque


def solve(grid):
    out = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]
    foreground = [color for color in counts if color != background]
    if len(foreground) != 2:
        return out
    paint, object_color = sorted(foreground, key=lambda color: counts[color])
    loose = {(r, c) for r in range(height) for c in range(width)
             if grid[r][c] == paint}
    pending = {(r, c) for r in range(height) for c in range(width)
               if grid[r][c] == object_color}
    objects = []
    while pending:
        start = min(pending)
        pending.remove(start)
        component, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    point = (r + dr, c + dc)
                    if point in pending:
                        pending.remove(point)
                        component.add(point)
                        stack.append(point)
        objects.append(component)

    matches = []
    for component in objects:
        top = min(r for r, c in component)
        bottom = max(r for r, c in component)
        left = min(c for r, c in component)
        right = max(c for r, c in component)
        gaps = set()
        # Complete gaps between parts of the same object in a row or column.
        for r in range(top, bottom + 1):
            columns = [c for rr, c in component if rr == r]
            if columns:
                gaps.update((r, c) for c in range(min(columns), max(columns) + 1)
                            if grid[r][c] == background)
        for c in range(left, right + 1):
            rows = [r for r, cc in component if cc == c]
            if rows:
                gaps.update((r, c) for r in range(min(rows), max(rows) + 1)
                            if grid[r][c] == background)
        # Grid edges can also close a pocket (including a missing corner cell).
        remaining = {(r, c) for r in range(top, bottom + 1)
                     for c in range(left, right + 1)
                     if grid[r][c] == background}
        while remaining:
            seed = min(remaining)
            remaining.remove(seed)
            region, queue, escapes = {seed}, deque([seed]), False
            while queue:
                r, c = queue.popleft()
                if ((r == top and top > 0) or
                    (r == bottom and bottom < height - 1) or
                    (c == left and left > 0) or
                    (c == right and right < width - 1)):
                    escapes = True
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    point = (r + dr, c + dc)
                    if point in remaining:
                        remaining.remove(point)
                        region.add(point)
                        queue.append(point)
            if not escapes:
                gaps.update(region)
        if len(gaps) == len(loose):
            matches.append(gaps)
    if len(matches) == 1:
        for r, c in loose:
            out[r][c] = background
        for r, c in matches[0]:
            out[r][c] = paint
    return out
