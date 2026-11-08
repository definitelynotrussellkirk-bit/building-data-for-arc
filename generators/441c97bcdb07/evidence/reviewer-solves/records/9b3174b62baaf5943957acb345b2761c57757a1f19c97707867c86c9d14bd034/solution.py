"""Complete missing copies of a repeated object at rectangle corners."""
from collections import Counter, defaultdict


def solve(grid):
    out = [list(row) for row in grid]
    h, w = len(out), len(out[0])
    bg = Counter(value for row in out for value in row).most_common(1)[0][0]
    unseen = {(r, c) for r in range(h) for c in range(w) if out[r][c] != bg}
    groups = defaultdict(list)
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        component, stack = [first], [first]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    stack.append(point)
                    component.append(point)
        top = min(r for r, _ in component)
        left = min(c for _, c in component)
        pattern = tuple(sorted((r - top, c - left, out[r][c]) for r, c in component))
        groups[pattern].append((top, left))
    for pattern, origins in groups.items():
        if len(origins) < 3:
            continue
        rows = sorted({r for r, _ in origins})
        cols = sorted({c for _, c in origins})
        for top in rows:
            for left in cols:
                for dr, dc, value in pattern:
                    r, c = top + dr, left + dc
                    if 0 <= r < h and 0 <= c < w:
                        out[r][c] = value
    return out
