"""Infer a shape-equivalence matrix from separated foreground objects."""

def _signature(points):
    variants = []
    for reflect in (False, True):
        for turns in range(4):
            transformed = []
            for r, c in points:
                x, y = r, -c if reflect else c
                for _ in range(turns):
                    x, y = y, -x
                transformed.append((x, y))
            top = min(r for r, _ in transformed)
            left = min(c for _, c in transformed)
            variants.append(tuple(sorted((r-top, c-left) for r, c in transformed)))
    return min(variants)


def solve(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    objects = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component, pending = [start], [start]
        while pending:
            r, c = pending.pop()
            for neighbor in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.append(neighbor)
                    pending.append(neighbor)
        objects.append((min(r for r, _ in component), min(c for _, c in component), _signature(component)))
    objects.sort(key=lambda item: item[:2])
    return [[8 if a[2] == b[2] else 0 for b in objects] for a in objects]
